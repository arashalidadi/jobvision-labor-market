# Project site (GitHub Pages)

Bilingual static site for the JobVision labor-market analysis. Plain HTML/CSS/JS —
no build step, no external CDN, no tracking.

```
docs/
├── index.html            # Persian (default, RTL)
├── en/index.html         # English (LTR)
├── assets/css/site.css   # design tokens + components
├── assets/js/site.js     # tabs, lightbox, copy buttons, reveal-on-scroll
├── assets/fonts/         # Vazirmatn (SIL OFL) + Inter subset, self-hosted
├── assets/img/           # figures (WebP + PNG), social card, favicon
├── project-brief.md      # assignment brief (unchanged)
└── dataset-card.md       # dataset card (unchanged)
```

## Hosting

Everything in this folder is published as-is: **Settings → Pages → Source:
*Deploy from a branch* → `main` / `/docs`**. No workflow or build step is
required, and `.nojekyll` keeps the folder byte-for-byte identical to what is
served. Locally:

```bash
python -m http.server -d docs 8000
# http://localhost:8000/      (Persian)
# http://localhost:8000/en/   (English)
```

## Refreshing figures

`scripts/build_site_assets.py` regenerates `assets/img/` from `outputs/figures/`
and rebuilds `assets/img/og-cover.png`. Run it after re-executing the notebook:

```bash
pip install pillow arabic-reshaper python-bidi
python scripts/build_site_assets.py
```

## Numbers on the site

Every figure on the site comes from the notebook output tables (`outputs/figures/`
and the notebook's own HTML tables); the site itself performs no calculation.
Canonical numbers live in `jobvision_analysis.ipynb` and `reports/`.
