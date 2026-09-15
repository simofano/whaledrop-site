"""Genera una pagina statica per lingua a partire dalle due pagine della radice.

Le pagine della radice restano la fonte e fanno da x-default:
- index.html: italiano nell'HTML, le altre lingue nel dizionario I18N in fondo;
- privacy/index.html: una <section data-lang> per lingua, con data-title e data-description.

Scrive /<lingua>/index.html, /<lingua>/privacy/index.html e sitemap.xml, ciascuna pagina con la
sua lingua, il suo titolo, la sua description e il suo canonical già nell'HTML. Gira nel workflow
di Pages prima dell'upload; i file generati sono in .gitignore.

Uso: python3 tools/build_i18n.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://whaledrop.app"
LANGS = ["it", "en", "de", "fr", "es"]


def fail(msg):
    sys.exit(f"build_i18n: {msg}")


def sub(pattern, repl, text, expect=1, flags=0):
    """re.sub che conta le sostituzioni: se il sorgente cambia forma la build si ferma invece di
    pubblicare una pagina tradotta a metà. expect=None accetta una o più corrispondenze."""
    fn = repl if callable(repl) else (lambda m: repl)
    out, n = re.subn(pattern, fn, text, flags=flags)
    if (n < 1) if expect is None else (n != expect):
        fail(f"{pattern!r}: {n} corrispondenze, attese {expect or 'almeno 1'}")
    return out


def attr(value):
    return value.replace("&", "&amp;").replace('"', "&quot;")


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def check_hreflang(src, name, path):
    wanted = [(code, f"{SITE}/{code}/{path}") for code in LANGS] + [("x-default", f"{SITE}/{path}")]
    for code, href in wanted:
        if f'<link rel="alternate" hreflang="{code}" href="{href}">' not in src:
            fail(f"{name}: manca <link rel=\"alternate\" hreflang=\"{code}\" href=\"{href}\">")


def lang_nav(text, lang, path):
    """Bandierine: link veri alla stessa pagina nelle altre lingue, con la corrente evidenziata."""
    def link(m):
        code, title = m.group(1), m.group(2)
        current = ' aria-current="true"' if code == lang else ""
        return f'<a href="/{code}/{path}" hreflang="{code}" data-pick="{code}" title="{title}"{current}>'
    pattern = (r'<a href="/(\w\w)/' + re.escape(path)
               + r'" hreflang="\1" data-pick="\1" title="([^"]*)"(?: aria-current="true")?>')
    return sub(pattern, link, text, expect=len(LANGS))


def build_landing():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    check_hreflang(src, "index.html", "")
    m = re.search(r"\n<script>\n  var I18N = (\{.*?\n  \});.*?</script>\n", src, re.S)
    if not m:
        fail("index.html: dizionario I18N non trovato")
    i18n = json.loads(re.sub(r"(?m)^(\s*)(\w+): \{", r'\1"\2": {', m.group(1)))
    if set(LANGS) - set(i18n):
        fail(f"index.html: I18N non ha {sorted(set(LANGS) - set(i18n))}")
    # Le pagine generate sono statiche: niente script di scelta della lingua.
    page = src[:m.start()] + "\n" + src[m.end():]
    keys = re.findall(r'data-i18n="([^"]+)"', page)

    for lang in LANGS:
        t = i18n[lang]
        missing = sorted(set(keys + ["title", "meta.description", "hero.badgeAlt"]) - set(t))
        if missing:
            fail(f"index.html: in I18N.{lang} mancano {missing}")
        out = page
        out = sub(re.escape('<html lang="it">'), f'<html lang="{lang}">', out)
        out = sub(r"<title>[^<]*</title>", f"<title>{t['title']}</title>", out)
        out = sub(r'<meta name="description" data-i18n-content="meta\.description" content="[^"]*">',
                  f'<meta name="description" content="{attr(t["meta.description"])}">', out)
        out = sub(re.escape(f'<link rel="canonical" href="{SITE}/">'),
                  f'<link rel="canonical" href="{SITE}/{lang}/">', out)
        out = sub(r'<meta property="og:description" content="[^"]*">',
                  f'<meta property="og:description" content="{attr(t["meta.description"])}">', out)
        out = sub(re.escape(f'<meta property="og:url" content="{SITE}/">'),
                  f'<meta property="og:url" content="{SITE}/{lang}/">', out)
        out = sub(r'(<(\w+)\b[^>]*\bdata-i18n="([^"]+)"[^>]*>)(.*?)(</\2>)',
                  lambda mm: mm.group(1) + t[mm.group(3)] + mm.group(5), out, expect=len(keys), flags=re.S)
        out = sub(r'src="/img/play-it\.svg" alt="[^"]*"',
                  f'src="/img/play-{lang}.svg" alt="{attr(t["hero.badgeAlt"])}"', out)
        out = sub(re.escape('href="https://play.google.com/store/apps/details?id=com.simofano.whaledrop"'),
                  f'href="https://play.google.com/store/apps/details?id=com.simofano.whaledrop&amp;hl={lang}"', out)
        out = sub(re.escape("/img/shots/it/"), f"/img/shots/{lang}/", out, expect=None)
        out = sub(re.escape('<a class="brand" href="/">'), f'<a class="brand" href="/{lang}/">', out)
        out = sub(re.escape('href="/privacy/"'), f'href="/{lang}/privacy/"', out, expect=None)
        out = lang_nav(out, lang, "")
        if "?lang=" in out:
            fail(f"{lang}/index.html: è rimasto un link ?lang=")
        write(f"{lang}/index.html", out)


def build_privacy():
    src = (ROOT / "privacy" / "index.html").read_text(encoding="utf-8")
    check_hreflang(src, "privacy/index.html", "privacy/")
    sections = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
        r'<section data-lang="(\w+)" lang="\1" data-title="([^"]*)" data-description="([^"]*)">', src)}
    if sorted(sections) != sorted(LANGS):
        fail(f"privacy/index.html: sezioni trovate {sorted(sections)}, attese {sorted(LANGS)}")

    for lang in LANGS:
        title, description = sections[lang]
        out = src
        out = sub(re.escape('<html lang="it" data-active="it" class="nojs">'),
                  f'<html lang="{lang}" data-active="{lang}">', out)
        out = sub(r"<title>[^<]*</title>", f"<title>{title}</title>", out)
        out = sub(r'<meta name="description" content="[^"]*">',
                  f'<meta name="description" content="{description}">', out)
        out = sub(re.escape(f'<link rel="canonical" href="{SITE}/privacy/">'),
                  f'<link rel="canonical" href="{SITE}/{lang}/privacy/">', out)
        out = sub(re.escape('<nav class="top"><a href="/">'), f'<nav class="top"><a href="/{lang}/">', out)
        out = lang_nav(out, lang, "privacy/")
        # Resta solo la sezione di questa lingua (con il suo commento di intestazione).
        out = sub(r'\n  <!-- =+ \w+ -->\n  <section data-lang="(?!' + lang + r'")\w+".*?</section>\n', "\n", out,
                  expect=len(LANGS) - 1, flags=re.S)
        out = sub(r"\n<script>.*?</script>\n<script>.*?</script>\n", "\n", out, flags=re.S)
        if "?lang=" in out:
            fail(f"{lang}/privacy/index.html: è rimasto un link ?lang=")
        write(f"{lang}/privacy/index.html", out)


def build_sitemap():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path in ("", "privacy/"):
        alternates = [(code, f"{SITE}/{code}/{path}") for code in LANGS] + [("x-default", f"{SITE}/{path}")]
        for _, loc in alternates:
            lines.append("  <url>")
            lines.append(f"    <loc>{loc}</loc>")
            for code, href in alternates:
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{code}" href="{href}"/>')
            lines.append("  </url>")
    lines.append("</urlset>")
    write("sitemap.xml", "\n".join(lines) + "\n")


if __name__ == "__main__":
    build_landing()
    build_privacy()
    build_sitemap()
    print(f"build_i18n: {len(LANGS) * 2} pagine e sitemap.xml generate")
