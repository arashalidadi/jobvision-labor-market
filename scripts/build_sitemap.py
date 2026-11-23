"""Generate docs/sitemap.xml for the landing pages, the guide and every section page."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = "https://arashalidadi.github.io/jobvision-labor-market"

SLUGS = {path.name for path in (DOCS / "guide").glob("*/") if path.is_dir()}


def url(loc: str, fa: str, en: str, priority: str, changefreq: str = "monthly") -> str:
    return f"""  <url>
    <loc>{loc}</loc>
    <xhtml:link rel="alternate" hreflang="fa" href="{fa}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{fa}"/>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""


entries: list[str] = []
entries.append(url(f"{SITE}/", f"{SITE}/", f"{SITE}/en/", "1.0", "weekly"))
entries.append(url(f"{SITE}/en/", f"{SITE}/", f"{SITE}/en/", "0.9", "weekly"))
entries.append(url(f"{SITE}/guide/", f"{SITE}/guide/", f"{SITE}/en/guide/", "0.9", "weekly"))
entries.append(url(f"{SITE}/en/guide/", f"{SITE}/guide/", f"{SITE}/en/guide/", "0.9", "weekly"))

for slug in sorted(SLUGS):
    entries.append(url(f"{SITE}/guide/{slug}/",
                       f"{SITE}/guide/{slug}/", f"{SITE}/en/guide/{slug}/", "0.8"))

header = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
"""
(DOCS / "sitemap.xml").write_text(header + "\n".join(entries) + "\n</urlset>\n", encoding="utf-8")
count = (DOCS / "sitemap.xml").read_text(encoding="utf-8").count("<url>")
print("sitemap entries:", count, "| sections:", len(SLUGS))
