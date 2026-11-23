"""Build a 15-slide 16:9 deck (HTML -> PDF) for the JobVision project.

Content lives in slides_content.py as SLIDES: list of dicts with keys
kicker, title, body (html), image (optional path), stat (optional list of (value,label)).
"""
import base64
from pathlib import Path

from slides_content import SLIDES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "jobvision_presentation.html"

CSS = """
@page { size: 338mm 190mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #e9eeed; }
body { font-family: "Segoe UI", "Tahoma", sans-serif; direction: rtl; color: #16302e; }
.slide {
  width: 338mm; height: 190mm; page-break-after: always; position: relative;
  padding: 14mm 18mm 12mm; background: #ffffff; overflow: hidden;
}
.slide::after {
  content: ""; position: absolute; left: 0; bottom: 0; height: 4mm; width: 100%;
  background: linear-gradient(90deg, #2f7f7a 0%, #2f7f7a 55%, #c9974b 55%, #c9974b 100%);
}
.kicker { font-size: 10pt; color: #2f7f7a; font-weight: 700; letter-spacing: .5px; }
h1 { font-size: 25pt; margin: 4mm 0 3mm; color: #123c38; line-height: 1.45; }
h2 { font-size: 15pt; margin: 0 0 3mm; color: #1f5f5b; }
.body { font-size: 12.5pt; line-height: 1.95; }
.body ul { margin: 0; padding-right: 6mm; }
.body li { margin: 2.2mm 0; }
.body b { color: #123c38; }
.grid { display: flex; gap: 7mm; align-items: flex-start; height: 118mm; }
.col { flex: 1; }
.col.img { flex: 1.15; display: flex; align-items: center; justify-content: center; }
.col.img img { max-width: 100%; max-height: 112mm; border-radius: 3mm; border: 1px solid #d9e5e3; }
.stats { display: flex; gap: 4mm; margin: 5mm 0 2mm; }
.stat { flex: 1; background: #f2f8f7; border-right: 3px solid #2f7f7a; border-radius: 2mm;
        padding: 3mm 4mm; }
.stat .v { font-size: 19pt; font-weight: 800; color: #1f5f5b; }
.stat .l { font-size: 9.5pt; color: #4c6663; margin-top: 1mm; }
.note { position: absolute; bottom: 8mm; right: 18mm; left: 18mm; font-size: 8.6pt; color: #6b8280; }
.pageno { position: absolute; bottom: 8mm; left: 18mm; font-size: 8.6pt; color: #8aa19e; }
.cover { display: flex; flex-direction: column; justify-content: center; height: 100%; }
.cover h1 { font-size: 34pt; line-height: 1.4; }
.cover .sub { font-size: 14pt; color: #3f5c59; margin: 4mm 0 8mm; }
.cover .meta { font-size: 11pt; color: #526d6a; line-height: 2; }
.badge { display: inline-block; background: #2f7f7a; color: #fff; border-radius: 8mm;
         padding: 1.6mm 5mm; font-size: 10pt; font-weight: 700; }
.quote { background: #fdf8ef; border-right: 4px solid #c9974b; padding: 4mm 6mm;
         border-radius: 2mm; font-size: 12pt; line-height: 1.95; }
table.mini { width: 100%; border-collapse: collapse; font-size: 10.5pt; }
table.mini th { background: #e8f2f1; padding: 2mm; text-align: right; }
table.mini td { border-bottom: 1px solid #e6eeed; padding: 1.8mm; }
"""


def image_src(path):
    data = Path(path).read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode()


parts = []
for number, slide in enumerate(SLIDES, start=1):
    image = ""
    if slide.get("image"):
        image = f'<div class="col img"><img src="{image_src(slide["image"])}"></div>'
        body = f'<div class="grid"><div class="col">{slide["body"]}</div>{image}</div>'
    else:
        body = f'<div>{slide["body"]}</div>'
    stats = ""
    if slide.get("stats"):
        stats = '<div class="stats">' + "".join(
            f'<div class="stat"><div class="v">{value}</div><div class="l">{label}</div></div>'
            for value, label in slide["stats"]) + "</div>"
    cover_class = " cover" if slide.get("cover") else ""
    parts.append(f"""
<section class="slide{cover_class}">
  <div class="kicker">{slide.get('kicker', '')}</div>
  <h1>{slide['title']}</h1>
  {stats}
  {body}
  <div class="note">{slide.get('note', '')}</div>
  <div class="pageno">{number} / {len(SLIDES)}</div>
</section>""")

html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<title>ارائه تحلیل بازار کار جاب‌ویژن</title><style>{CSS}</style></head>
<body>{''.join(parts)}</body></html>"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT} ({len(SLIDES)} slides, {len(html)/1024:.0f} KB)")