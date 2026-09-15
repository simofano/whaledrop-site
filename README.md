# whaledrop.app

Landing page and privacy policy for [Whale Drop](https://whaledrop.app), an Android app that
helps you drink more water. Static pages served by GitHub Pages on the `whaledrop.app` domain
(see the `CNAME` file).

- `index.html`: the landing page in five languages (full-screen video, numbers band, screens,
  gallery, privacy). The Italian text lives in the HTML; the other languages are in the `I18N`
  dictionary at the bottom of the page, applied through `data-i18n`. It is the `x-default`
  page: it shows the browser's language, and old `?lang=xx` links redirect to `/xx/`.
- `privacy/index.html`: the privacy policy in Italian, English, German, French and Spanish, one
  `<section data-lang>` per language with its `data-title` and `data-description`. It is the
  `x-default` page (`?lang=xx` redirects to `/xx/privacy/`) and the URL given to the Play
  Console: `https://whaledrop.app/privacy/`.
- `tools/build_i18n.py`: generates the static per-language pages `/it/`, `/en/`, `/de/`, `/fr/`,
  `/es/` and `/<lang>/privacy/` from the two pages above (text, `lang`, title, description and
  canonical already in the HTML, `hreflang` links for Google), plus `sitemap.xml`. The Pages
  workflow runs it before uploading, so the outputs are in `.gitignore` and never committed;
  run `python tools/build_i18n.py` locally to preview them. It stops with an error if a source
  page no longer has the shape it expects (for example a `data-i18n` key missing in a language).
- `img/`: `promo.mp4` (muted, 960 px, looping) with `promo-poster.jpg`, the two gym photos, the
  localized Google Play badges as SVG, the flags, and `logo.svg` derived from the app icon's
  vector drawable.
- `img/shots/<lang>/1..6.png`: the six store screenshots scaled to 540 px, shown in the language
  picked by the switcher (1 welcome, 2 your day, 3 stats, 4 weather, 5 reminders, 6 third step
  of the guided Drink flow). Source: `store_screenshots/` in the app repository.
- `.nojekyll`: tells Pages to serve the files as they are, without Jekyll.

Publishing is a push to `main`: Pages rebuilds on its own within a minute.
