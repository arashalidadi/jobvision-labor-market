"""Build reports/jobvision_report.html from the executed notebook.

Markdown cells become prose, HTML outputs (tables, metrics, answers) are kept,
and figure outputs are embedded as base64 images. Print to PDF afterwards with
a headless browser (Page.printToPDF).
"""
import base64
import json
import re
from pathlib import Path

import markdown as md_lib

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "jobvision_analysis.ipynb"
OUTPUT = ROOT / "reports" / "jobvision_report.html"

nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

CSS = """
@page { size: A4; margin: 17mm 15mm 18mm 15mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Tahoma", "Iranian Sans", sans-serif;
  direction: rtl; text-align: right; color: #1f2d2c; font-size: 10.6pt; line-height: 1.85;
  margin: 0; background: #fff;
}
.page { max-width: 100%; }
h1 { font-size: 20pt; color: #163f3b; border-bottom: 3px solid #2f7f7a; padding-bottom: 6px;
     margin: 22px 0 10px; page-break-after: avoid; }
h2 { font-size: 15pt; color: #1f5f5b; margin: 18px 0 6px; page-break-after: avoid; }
h3 { font-size: 12.5pt; color: #2f7f7a; margin: 14px 0 5px; page-break-after: avoid; }
p { margin: 5px 0 8px; text-align: justify; }
ul, ol { padding-right: 20px; margin: 4px 0 10px; }
li { margin: 3px 0; }
strong { color: #123c38; }
a { color: #1f6f69; }
code { direction: ltr; unicode-bidi: embed; background: #f2f6f5; padding: 1px 4px;
       border-radius: 3px; font-size: 9.3pt; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-size: 8.8pt;
        page-break-inside: avoid; }
th { background: #e8f2f1; color: #173b37; border-bottom: 2px solid #b9d6d3; padding: 5px 6px;
     text-align: right; font-weight: 700; }
td { border-bottom: 1px solid #e6eeed; padding: 4px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f8fbfa; }
.jv-caption { font-size: 9.5pt; font-weight: 700; color: #1f4b48; margin: 10px 0 4px; }
.jv-wrap { margin: 6px 0 16px; page-break-inside: avoid; }
.jv-note { font-size: 8.5pt; color: #5c6f6d; margin-top: 3px; }
.jv-metrics { border-right: 4px solid #2f7f7a; background: #f1f8f6; padding: 7px 12px;
  border-radius: 5px; margin: 9px 0 13px; font-size: 9.6pt; page-break-inside: avoid; }
.jv-metrics-title { font-weight: 700; color: #173b37; }
.jv-metrics ul { margin: 3px 0 0; padding-right: 16px; }
.jv-answer { border-right: 4px solid #c9974b; background: #fdf8ef; padding: 7px 12px;
  border-radius: 5px; margin: 9px 0 13px; font-size: 9.8pt; page-break-inside: avoid; }
.jv-answer-title { font-weight: 700; color: #6b4a13; margin-bottom: 3px; }
figure { margin: 10px 0 14px; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; border: 1px solid #e2ebeb; border-radius: 4px; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center;
         text-align: right; }
.cover h1 { border: 0; font-size: 30pt; margin: 0 0 10px; line-height: 1.5; }
.cover .sub { font-size: 13pt; color: #3d5b58; margin-bottom: 26px; }
.cover .meta { font-size: 10.5pt; color: #456; line-height: 2.1; }
.cover .rule { height: 5px; width: 120px; background: #c9974b; margin: 18px 0; }
.toc { page-break-after: always; }
.toc ol { list-style: none; padding-right: 0; counter-reset: toc; }
.toc li { margin: 5px 0; border-bottom: 1px dotted #cfdedd; padding-bottom: 4px; }
.toc .num { color: #2f7f7a; font-weight: 700; margin-left: 8px; }
.break { page-break-before: always; }
"""


def clean_markdown(source: str) -> str:
    text = source.strip()
    text = re.sub(r"^<div[^>]*>\s*", "", text)
    text = re.sub(r"\s*</div>\s*$", "", text)
    return text


def markdown_to_html(source: str) -> str:
    return md_lib.markdown(clean_markdown(source), extensions=["tables", "sane_lists", "nl2br"])


def image_tag(data: str) -> str:
    return f'<figure><img src="data:image/png;base64,{data}" alt="figure"></figure>'


def html_output(data: dict) -> str:
    if "text/html" in data:
        return "".join(data["text/html"])
    return ""


body_parts = []
figure_count = 0
for cell in nb.get("cells", []):
    if cell["cell_type"] == "markdown":
        rendered = markdown_to_html("".join(cell["source"]))
        if rendered.strip():
            body_parts.append(rendered)
        continue
    for output in cell.get("outputs", []):
        data = output.get("data", {})
        if "image/png" in data:
            body_parts.append(image_tag("".join(data["image/png"])))
            figure_count += 1
        elif "text/html" in data:
            body_parts.append(html_output(data))
        elif output.get("output_type") == "stream" and output.get("name") == "stdout":
            text = "".join(output.get("text", [])).strip()
            if text:
                body_parts.append(f"<pre>{text}</pre>")

sections = re.findall(r"<h1[^>]*>(.*?)</h1>", "\n".join(body_parts), flags=re.S)
toc_items = []
seen = set()
for title in sections:
    title_text = re.sub(r"<[^>]+>", "", title).strip()
    if title_text and title_text not in seen:
        seen.add(title_text)
        number = title_text.split(".")[0].strip()
        rest = title_text[len(number) + 1:].strip(" .")
        toc_items.append(f'<li><span class="num">{number}</span>{rest or title_text}</li>')

cover = f"""
<div class="cover">
  <div style="font-size:11pt;color:#2f7f7a;font-weight:700;letter-spacing:1px;">گزارش تحلیلی پروژه</div>
  <h1>تحلیل بازار کار ایران<br>بر پایه آگهی‌های استخدامی جاب‌ویژن</h1>
  <div class="rule"></div>
  <div class="sub">از ۳۶۴٬۸۳۸ آگهی خام تا بسته تصمیم مدیریتی | فروردین ۱۴۰۱ تا اسفند ۱۴۰۲</div>
  <div class="meta">
    تحلیلگر داده: آرش علی‌دادی<br>
    منبع داده: JobVision Jobposts Dataset — Hugging Face<br>
    مجوز داده: CC BY-NC 4.0 (پژوهشی و غیرتجاری)<br>
    مخزن کد: github.com/arashalidadi/jobvision-labor-market<br>
    نسخه گزارش: ۱٫۰
  </div>
</div>
<div class="break"></div>
<div class="toc">
  <h1>فهرست مطالب</h1>
  <ol>{''.join(toc_items)}</ol>
</div>
"""

html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<title>گزارش تحلیل بازار کار جاب‌ویژن</title>
<style>{CSS}</style>
</head>
<body>
{cover}
<div class="page">
{''.join(body_parts)}
</div>
</body>
</html>
"""

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(html, encoding="utf-8")
print(f"wrote {OUTPUT} ({len(html) / 1024:.0f} KB, {figure_count} figures)")