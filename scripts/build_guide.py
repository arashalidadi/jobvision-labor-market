"""Build the bilingual project guide (docs/guide + docs/en/guide) from the executed notebook.

The notebook is the single source of truth: every section page is generated from its
markdown cells (analysis prose), code cells (highlighted code) and cell outputs
(tables, metric blocks, figures). Persian renders natively; English comes from the
translation layer in content/en/.

Usage:  python scripts/build_guide.py [--lang fa|en|all]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

import markdown as md_lib
from bs4 import BeautifulSoup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "jobvision_analysis.ipynb"
IMG_DIR = ROOT / "docs" / "assets" / "img"
CONTENT = ROOT / "content" / "en"
SITE = "https://arashalidadi.github.io/jobvision-labor-market"
REPO = "https://github.com/arashalidadi/jobvision-labor-market"
COLAB = f"{REPO}/blob/main/notebooks/jobvision_colab.ipynb"

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
SLUGS = {
    1: "project-brief-and-questions",
    2: "data-rules",
    3: "tooling-and-helpers",
    4: "data-quality",
    5: "cleaning-and-analysis-layer",
    6: "feature-engineering",
    7: "distributions-and-outliers",
    8: "correlation-and-collinearity",
    9: "salary-disclosure",
    10: "time-trends-and-seasonality",
    11: "gender-and-opportunity",
    12: "education-vs-experience",
    13: "income-peak-by-age",
    14: "geography-and-provinces",
    15: "global-comparison",
    16: "salary-modelling",
    17: "job-title-clustering",
    18: "industry-occupation",
    19: "skills-evolution",
    20: "employer-typology",
    21: "skill-network",
    22: "decision-package",
    23: "conclusions-and-dashboard",
    24: "reproducibility-checks",
}

UI = {
    "fa": dict(
        lang="fa", dir="rtl", home="صفحه اصلی", guide="راهنما", docs="مستندات",
        search="جست‌وجو در راهنما…", search_hint="برای جست‌وجو تایپ کنید؛ Esc برای بستن",
        no_result="چیزی پیدا نشد", on_this_page="در این صفحه", toc="فهرست بخش‌ها",
        prev="قبلی", next="بعدی", back_to_guide="فهرست راهنما", read_time="دقیقه مطالعه",
        tables="جدول", figures="نمودار", code_cells="سلول کد", copy="کپی", copied="کپی شد",
        show_code="نمایش کد این مرحله", show_all="نمایش همه ردیف‌ها", collapse="جمع کردن",
        output="خروجی", cells_label="سلول‌های نوتبوک", open_notebook="نوتبوک در گیت‌هاب",
        run_colab="اجرا در Colab", part="بخش", of="از", last_update="آخرین بازسازی از نوتبوک",
        lang_other="EN", lang_other_href="en/guide/", note_prefix="یادداشت",
        all_sections="همه بخش‌ها", start_here="از اینجا شروع کنید", sections_word="بخش",
        metric_block="اعداد کلیدی", guide_lead="راهنمای کامل پروژه؛ عیناً از نوتبوک اجراشده ساخته می‌شود.",
        footer_note="این راهنما از اجرای نوتبوک پروژه ساخته شده است؛ هر عدد قابل بازتولید است.",
        toc_title="فهرست مطالب", show_more_code="نمایش کد", key_numbers="اعداد کلیدی",
        print_note="", dataset="داده", license_word="مجوز", tools="ماشین‌حساب حقوق",
        dashboard="داشبورد پروژه",
    ),
    "en": dict(
        lang="en", dir="ltr", home="Home", guide="Guide", docs="Docs",
        search="Search the guide…", search_hint="Type to search, Esc to close",
        no_result="Nothing found", on_this_page="On this page", toc="Sections",
        prev="Previous", next="Next", back_to_guide="Guide index", read_time="min read",
        tables="tables", figures="figures", code_cells="code cells", copy="Copy", copied="Copied",
        show_code="Show the code for this step", show_all="Show all rows", collapse="Collapse",
        output="Output", cells_label="Notebook cells", open_notebook="Notebook on GitHub",
        run_colab="Run in Colab", part="Part", of="of", last_update="Rebuilt from the notebook",
        lang_other="فارسی", lang_other_href="../guide/", note_prefix="Note",
        all_sections="All sections", start_here="Start here", sections_word="sections",
        metric_block="Key numbers", guide_lead="The full project guide, generated directly from the executed notebook.",
        footer_note="This guide is generated from the project notebook; every number is reproducible.",
        toc_title="Table of contents", show_more_code="Show code", key_numbers="Key numbers",
        print_note="", dataset="Dataset", license_word="License", tools="Salary calculator",
        dashboard="Project dashboard",
    ),
}


# --------------------------------------------------------------------------- utils
def fa_to_en_digits(text: str) -> str:
    out = []
    for ch in text:
        if ch in FA_DIGITS:
            out.append(str(FA_DIGITS.index(ch)))
        elif ch == "٬":
            out.append(",")
        elif ch == "٫":
            out.append(".")
        elif ch == "٪":
            out.append("%")
        else:
            out.append(ch)
    return "".join(out)


def norm_number(text: str) -> str:
    """Extract the leading number of a heading (Persian or Latin)."""
    digits = fa_to_en_digits(text)
    match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", digits.strip())
    return match.group(1) if match else ""


def anchor(text: str, fallback: str) -> str:
    num = norm_number(text)
    if num:
        return "sec-" + num.replace(".", "-")
    return fallback


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def display_title(title: str) -> str:
    """Section title without its leading number (the badge shows the number)."""
    return re.sub(r"^[\u06F0-\u06F90-9]+\s*\.\s*", "", title).strip()


# ------------------------------------------------------------------- notebook model
def load_model() -> dict:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    sections: list[dict] = []
    current = None
    for index, cell in enumerate(cells):
        source = "".join(cell["source"])
        if cell["cell_type"] == "markdown":
            body = strip_wrapper(source)
            heading = re.search(r"^#\s+(.+)$", body, flags=re.M)
            if heading:
                title = clean_text(heading.group(1))
                num = norm_number(title)
                section = dict(num=int(num) if num.isdigit() else 0, title=title,
                               cells=[], start_cell=index)
                sections.append(section)
                current = section
                body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.M).strip()
                if current["cells"] and False:
                    pass
                current.setdefault("title_en", title)
            if current is None:
                current = dict(num=0, title="JobVision — Iran Labor Market Analysis",
                               cells=[], start_cell=index)
                sections.append(current)
            current["cells"].append(dict(kind="md", cell=index, text=body,
                                      h1=bool(heading) if cell["cell_type"] == "markdown" else False))
        elif cell["cell_type"] == "code":
            if current is None:
                continue
            current["cells"].append(dict(kind="code", cell=index, source=source,
                                         outputs=cell.get("outputs", [])))
    return dict(sections=sections)


def strip_wrapper(source: str) -> str:
    text = source.strip()
    text = re.sub(r"^<div[^>]*dir=\"rtl\"[^>]*>\s*", "", text)
    text = re.sub(r"\s*</div>\s*$", "", text)
    return text


# ----------------------------------------------------------------------- rendering
def md_to_html(text: str, lang: str) -> str:
    converter = md_lib.Markdown(extensions=["tables", "fenced_code", "attr_list",
                                            "sane_lists", "md_in_html"])
    html_out = converter.convert(text)
    soup = BeautifulSoup(html_out, "html.parser")
    counter = [0]
    for tag in soup.find_all(["h2", "h3"]):
        label = tag.get_text(" ", strip=True)
        counter[0] += 1
        tag["id"] = anchor(label, f"sub-{counter[0]}")
        tag["class"] = tag.get("class", []) + ["guide-heading"]
        link = soup.new_tag("a", **{"class": "anchor", "href": f"#{tag['id']}",
                                    "aria-label": "link"})
        link.string = "#"
        tag.append(" ")
        tag.append(link)
    if lang == "en":
        for tag in soup.find_all(attrs={"dir": "rtl"}):
            del tag["dir"]
            if tag.get("align") == "right":
                del tag["align"]
    return str(soup)


def translate_string(text: str, strings: dict, lang: str) -> str:
    if lang == "fa":
        return text
    stripped = clean_text(text)
    norm = fa_to_en_digits(stripped)  # Arabic/Persian digits -> Latin so the lookup keys (Latin digits)
    for key, value in strings.items():  # match regardless of digit rendering in the caption
        if fa_to_en_digits(clean_text(key)) == norm:
            return value
    # fall back to token-level replacement for compound strings without a full match
    out = norm
    for key, value in sorted(strings.items(), key=lambda kv: -len(kv[0])):
        if len(key) > 3 and key in out:
            out = out.replace(key, value)
    return fa_to_en_digits(out)


def html_blocks_from_outputs(outputs: list, lang: str, strings: dict, caption_map: dict) -> list:
    blocks: list[dict] = []
    for output in outputs:
        data = output.get("data") or {}
        if "image/png" in data:
            continue
        if "text/html" in data:
            raw = "".join(data["text/html"])
            soup = BeautifulSoup(raw, "html.parser")
            if soup.find("style") and not soup.select(".jv-wrap, .jv-metrics"):
                continue  # style injection cell
            for wrap in soup.select(".jv-wrap"):
                caption_el = wrap.select_one(".jv-caption")
                table = wrap.select_one("table")
                note_el = wrap.select_one(".jv-note")
                if table is None:
                    continue
                caption = clean_text(caption_el.get_text(" ", strip=True)) if caption_el else ""
                note = clean_text(note_el.get_text(" ", strip=True)) if note_el else ""
                for el in table.select("th, td, caption"):
                    original = el.get_text(" ", strip=True)
                    translated = translate_string(original, strings, lang)
                    if translated != original:
                        el.clear()
                        el.append(translated)
                rows = table.select("tbody tr")
                blocks.append(dict(kind="table", caption=translate_string(caption, strings, lang),
                                   html=str(table), note=translate_string(note, strings, lang),
                                   rows=len(rows), cols=len(table.select("thead th")) or None,
                                   number=re.sub(r"^\D+", "", norm_number(caption)) or ""))
            for metrics in soup.select(".jv-metrics"):
                title_el = metrics.select_one(".jv-metrics-title")
                title = clean_text(title_el.get_text(" ", strip=True)) if title_el else ""
                items = []
                for li in metrics.select("li"):
                    original = clean_text(li.get_text(" ", strip=True))
                    items.append(translate_string(original, strings, lang))
                if items:
                    blocks.append(dict(kind="metrics", title=translate_string(title, strings, lang),
                                       items=items))
        elif "text/plain" in data and output.get("output_type") in ("execute_result", "display_data"):
            if any("text/html" in (o.get("data") or {}) for o in outputs):
                continue
            text = "".join(data["text/plain"]).strip()
            if text and not text.startswith("<Figure"):
                blocks.append(dict(kind="text", text=text))
        elif output.get("output_type") == "stream":
            text = "".join(output.get("text", ""))
            if text.strip():
                blocks.append(dict(kind="stream", text=text.rstrip(), stream=output.get("name")))
    return blocks


def figure_map(source: str, outputs: list) -> list[dict]:
    names = re.findall(r"complete\(\s*'([^']+)'\s*\)", source)
    captions = {}
    for match in re.finditer(r"heading\(\s*ax\s*,\s*'([^']+)'\s*,\s*'([^']+)'", source):
        captions[fa_to_en_digits(match.group(1)).replace(".", "_")] = match.group(2)
    images = [o for o in outputs if "image/png" in (o.get("data") or {})]
    figures = []
    for position, image in enumerate(images):
        name = names[position] if position < len(names) else (names[-1] if names else None)
        if name is None:
            continue
        key = "fig_" + name.replace(".", "_")
        titles = [captions[part.replace(".", "_")] for part in name.split("-")
                  if part.replace(".", "_") in captions]
        figures.append(dict(key=key, number=name, title=" · ".join(titles)))
    return figures


def render_code(source: str, lang: str, ui: dict) -> str:
    formatter = HtmlFormatter(style="one-dark", nowrap=True)
    highlighted = highlight(source.rstrip("\n"), PythonLexer(), formatter)
    lines = source.rstrip("\n").count("\n") + 1
    label = f"{lines} خط" if lang == "fa" else f"{lines} lines"
    if lines > 24:
        return f"""<details class="code-fold">
  <summary><span>{ui['show_code']}</span><em>{label}</em></summary>
  <div class="code-card">
    <header><span>Python</span><button class="copy-btn" data-copy="{html.escape(source, quote=True)}" data-done-text="{ui['copied']}">{ui['copy']}</button></header>
    <pre class="code"><code>{highlighted}</code></pre>
  </div>
</details>"""
    return f"""<div class="code-card">
    <header><span>Python · {label}</span><button class="copy-btn" data-copy="{html.escape(source, quote=True)}" data-done-text="{ui['copied']}">{ui['copy']}</button></header>
    <pre class="code"><code>{highlighted}</code></pre>
  </div>"""


def render_table(block: dict, lang: str, ui: dict) -> str:
    soup = BeautifulSoup(block["html"], "html.parser")
    table = soup.find("table")
    table["class"] = ["data", "compact", "guide-table"]
    rows = table.select("tbody tr")
    clipped = len(rows) > 14
    if clipped:
        for row in rows[12:]:
            row["class"] = row.get("class", []) + ["is-extra"]
            row["hidden"] = ""
    note = f'<p class="tbl-note"><span>{ui["note_prefix"]}:</span> {block["note"]}</p>' if block["note"] else ""
    more = ""
    if clipped:
        more = (f'<button class="table-more" type="button" data-rows="{len(rows)}">'
                f'{ui["show_all"]} ({len(rows):,})</button>')
    number = block.get("number") or ""
    return f"""<figure class="guide-table" id="table-{html.escape(number.replace('.', '-'))}">
  <figcaption>{block['caption']}</figcaption>
  <div class="table-wrap">{table}</div>
  {note}
  {more}
</figure>"""


def render_metrics(block: dict, lang: str, ui: dict) -> str:
    items = "".join(f"<li>{item}</li>" for item in block["items"])
    title = block["title"] or ui["metric_block"]
    return f"""<div class="guide-metrics">
  <p class="m-title">{title}</p>
  <ul>{items}</ul>
</div>"""


def render_figure(fig: dict, lang: str, ui: dict, strings: dict, assets: str) -> str:
    key = fig["key"]
    number = fig["number"].replace(".", "-")
    title = translate_string(fig["title"], strings, lang) if fig["title"] else ""
    if lang == "fa":
        caption = f"نمودار {fig['number']}" + (f" | {title}" if title else "")
    else:
        caption = f"Figure {fa_to_en_digits(fig['number'])}" + (f" | {title}" if title else "")
    return f"""<figure class="figure guide-figure" id="figure-{html.escape(number)}">
  <button type="button" data-full="{assets}img/{key}.webp" data-caption="{html.escape(caption, quote=True)}">
    <img src="{assets}img/{key}-sm.webp" alt="{html.escape(caption, quote=True)}" loading="lazy" decoding="async">
  </button>
  <figcaption>{caption}</figcaption>
</figure>"""


# ------------------------------------------------------------------- page assembly
def section_title(section: dict, lang: str) -> str:
    if lang == "en" and section.get("title_en"):
        return clean_text(section["title_en"])
    return section["title"]


def page_paths(lang: str, section_page: bool) -> dict:
    """Relative path prefixes that are correct for each page depth."""
    if section_page:
        assets = "../../assets/" if lang == "fa" else "../../../assets/"
        home = "../../index.html"  # fa: docs/index.html · en: docs/en/index.html
        other = ("../../en/guide/" if lang == "fa" else "../../../guide/")
        guide_root = "../"
    else:
        assets = "../assets/" if lang == "fa" else "../../assets/"
        home = "../index.html"
        other = "../en/guide/" if lang == "fa" else "../../guide/"
        guide_root = ""
    return dict(assets=assets, home=home, other=other, guide_root=guide_root)


def card_meta(stats: dict, ui: dict) -> str:
    parts = []
    for key, label in (("tables", ui["tables"]), ("figures", ui["figures"]), ("code", ui["code_cells"])):
        if stats[key]:
            parts.append(f'{stats[key]} {label}')
    if not parts:
        parts.append(f'{stats["words"]} {"کلمه" if ui["lang"] == "fa" else "words"}')
    return " · ".join(parts)


def section_stats(section: dict, lang: str) -> dict:
    tables = figures = code = 0
    words = 0
    for block in section["rendered"]:
        if block["kind"] == "table":
            tables += 1
        elif block["kind"] == "figure":
            figures += 1
        elif block["kind"] == "code":
            code += 1
        elif block["kind"] == "md":
            words += len(re.sub(r"<[^>]+>", " ", block["html"]).split())
    return dict(tables=tables, figures=figures, code=code, words=words)


def build_section(section: dict, model: dict, lang: str, translations: dict,
                      assets: str = "../../") -> dict:
    ui = UI[lang]
    strings = translations.get("strings", {})
    cells_map = translations.get("cells", {})
    rendered: list[dict] = []
    headings: list[dict] = []
    for block in section["cells"]:
        if block["kind"] == "md":
            text = cells_map.get(str(block["cell"]), block["text"])
            if lang == "en":
                text = fa_to_en_digits(text) if str(block["cell"]) in cells_map else text
            if block.get("h1"):
                head = re.search(r"^#\s+(.+)$", text, flags=re.M)
                if head:
                    section["title_en"] = clean_text(head.group(1))
                    text = re.sub(r"^#\s+.+$", "", text, count=1, flags=re.M).strip()
            html_out = md_to_html(text, lang)
            soup = BeautifulSoup(html_out, "html.parser")
            for tag in soup.find_all(["h2", "h3"]):
                headings.append(dict(level=tag.name, id=tag["id"],
                                     text=tag.get_text(" ", strip=True).rstrip("# ").strip()))
            if soup.get_text(strip=True):
                rendered.append(dict(kind="md", html=html_out))
        else:
            source = block["source"]
            figures = figure_map(source, block["outputs"])
            blocks = html_blocks_from_outputs(block["outputs"], lang, strings, {})
            code_html = ""
            if source.strip() and not re.fullmatch(r"\s*%matplotlib inline\s*", source):
                code_html = render_code(source, lang, ui)
            if code_html:
                rendered.append(dict(kind="code", html=code_html, cell=block["cell"]))
            for figure in figures:
                rendered.append(dict(kind="figure", html=render_figure(figure, lang, ui, strings, assets)))
            for item in blocks:
                if item["kind"] == "table":
                    rendered.append(dict(kind="table", html=render_table(item, lang, ui)))
                elif item["kind"] == "metrics":
                    rendered.append(dict(kind="metrics", html=render_metrics(item, lang, ui)))
                else:
                    text = html.escape(item["text"])
                    rendered.append(dict(kind="text", html=f'<pre class="out-text">{text}</pre>'))
    section["rendered"] = rendered
    section["headings"] = headings
    return section


def page_shell(*, lang: str, title: str, description: str, canonical: str, body: str,
               sidebar: str, toc: str, other_lang_href: str, other_lang_absolute: str,
               paths: dict, search_index: str = "../search.json") -> str:
    ui = UI[lang]
    other = "en" if lang == "fa" else "fa"
    other_ready = (ROOT / "docs" / "en" / "guide" / "index.html").exists()
    assets, home, guide_root = paths["assets"], paths["home"], paths["guide_root"]
    tools_href = assets.replace("assets/", "tools/salary-calculator.html")
    dashboard_href = assets.replace("assets/", "dashboard/")
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{ui['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="author" content="Arash Alidadi">
<meta name="theme-color" content="#0b3d39">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="{lang}" href="{canonical}">
<link rel="alternate" hreflang="{other}" href="{other_lang_absolute}">
<link rel="alternate" hreflang="x-default" href="{SITE}/guide/">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/img/og-cover.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{assets}img/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{assets}fonts/Vazirmatn-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{assets}css/site.css">
<link rel="stylesheet" href="{assets}css/pygments.css">
<link rel="stylesheet" href="{assets}css/guide.css">
<script type="application/ld+json">
{json.dumps({
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": title,
  "description": description,
  "url": canonical,
  "inLanguage": lang,
  "author": {"@type": "Person", "name": "Arash Alidadi"},
  "isPartOf": {"@type": "WebSite", "name": "JobVision Labor Market", "url": SITE},
  "license": "https://creativecommons.org/licenses/by-nc/4.0/",
}, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="guide-page{' en' if lang == 'en' else ''}">
<a class="skip-link" href="#main">Skip</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="JobVision Labor Market">
      <span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"><path d="M4 17l4-6 4 3 4-7 4 4"/></svg></span>
      <span>JobVision<small>Labor Market Analytics</small></span>
    </a>
    <nav class="nav" id="nav" aria-label="Primary">
      <a href="{home}#problem">{ui['home']}</a>
      <a href="{home}#findings">{'یافته‌ها' if lang == 'fa' else 'Findings'}</a>
      <a href="{home}#visuals">{'نمودارها' if lang == 'fa' else 'Visuals'}</a>
      <a href="{home}#playbook">{'بسته اجرایی' if lang == 'fa' else 'Playbook'}</a>
      <a class="active" href="{guide_root}">{ui['docs']}</a>
      <a href="{tools_href}">{ui['tools']}</a>
      <a href="{dashboard_href}">{ui['dashboard']}</a>
    </nav>
    <div class="header-actions">
      <div class="lang-switch" role="group" aria-label="Language">
        {(f'<span class="on" aria-current="true">FA</span><a href="{other_lang_href}" hreflang="en" lang="en">EN</a>' if other_ready else '<span class="on" aria-current="true">FA</span><span class="off" title="EN">EN</span>') if lang == 'fa' else f'<a href="{other_lang_href}" hreflang="fa" lang="fa">FA</a><span class="on" aria-current="true">EN</span>'}
      </div>
      <button class="guide-search-btn" type="button" aria-label="{ui['search']}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
        <span>{ui['search'].replace('…', '')}</span>
      </button>
      <a class="icon-link" href="{REPO}" aria-label="GitHub" title="GitHub">
        <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      </a>
      <button class="icon-link menu-toggle" aria-label="menu" aria-expanded="false" aria-controls="nav">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>
    </div>
  </div>
</header>

<div class="guide-shell">
  <aside class="guide-side" id="guideSide" aria-label="{ui['toc']}">
    {sidebar}
  </aside>
  <main class="guide-main" id="main">
    {body}
  </main>
  <aside class="guide-aside" aria-label="{ui['on_this_page']}">
    {toc}
  </aside>
</div>

<div class="lightbox" id="lightbox" role="dialog" aria-modal="true">
  <button type="button" aria-label="close">×</button>
  <img alt="">
  <p class="cap"></p>
</div>

<div class="search-modal" id="searchModal" role="dialog" aria-modal="true" aria-label="{ui['search']}">
  <div class="search-box">
    <input type="search" id="searchInput" placeholder="{ui['search']}" autocomplete="off">
    <p class="hint">{ui['search_hint']}</p>
    <ul id="searchResults"></ul>
  </div>
</div>

<footer class="site-footer">
  <div class="wrap">
    <div class="footer-bottom">
      <p>{ui['footer_note']}</p>
      <p><a href="{REPO}">GitHub</a> · <a href="{home}">{ui['home']}</a> · <a href="{guide_root}">{ui['back_to_guide']}</a></p>
    </div>
  </div>
</footer>

<script src="{assets}js/site.js"></script>
<script src="{assets}js/guide.js" data-index="{search_index}" data-ui-search="{ui['search']}"></script>
</body>
</html>
"""


def sidebar_html(sections: list[dict], active_num: int, lang: str, depth: str = "../") -> str:
    ui = UI[lang]
    items = []
    for section in sections:
        if section["num"] == 0:
            continue
        slug = f"{section['num']:02d}-{SLUGS[section['num']]}"
        label = display_title(section_title(section, lang))
        classes = "guide-nav-link" + (" is-active" if section["num"] == active_num else "")
        subs = ""
        if section["num"] == active_num and section.get("headings"):
            sub_items = "".join(
                f'<li class="lvl-{h["level"]}"><a href="#{h["id"]}">{html.escape(h["text"])}</a></li>'
                for h in section["headings"] if h["level"] in ("h2", "h3"))
            if sub_items:
                subs = f'<ul class="guide-sub">{sub_items}</ul>'
        items.append(f'<li><a class="{classes}" href="{depth}{slug}/">'
                     f'<span class="n">{section["num"]}</span><span>{html.escape(label)}</span></a>{subs}</li>')
    return f"""<div class="guide-side-head">
  <a class="guide-back" href="../">{'← ' if lang == 'fa' else '← '}{ui['back_to_guide']}</a>
  <p class="guide-side-title">{ui['toc_title']}</p>
</div>
<ul class="guide-nav">{''.join(items)}</ul>"""


def toc_html(section: dict, lang: str) -> str:
    ui = UI[lang]
    items = "".join(f'<li class="lvl-{h["level"]}"><a href="#{h["id"]}">{html.escape(h["text"])}</a></li>'
                    for h in section.get("headings", []) if h["level"] == "h2")
    if not items:
        return ""
    return f'<p class="aside-title">{ui["on_this_page"]}</p><ul class="aside-toc">{items}</ul>'


def write_index(model: dict, lang: str, out_dir: Path, translations: dict) -> None:
    ui = UI[lang]
    sections = [s for s in model["sections"] if s["num"] > 0]
    cards = []
    for section in sections:
        stats = section_stats(section, lang)
        slug = f"{section['num']:02d}-{SLUGS[section['num']]}"
        href = f"{slug}/" if lang == "fa" else f"../guide/{slug}/"
        cards.append(
            f'<li class="guide-card reveal"><a href="{href}">'
            f'<span class="num">{section["num"]}</span>'
            f'<span class="t">{html.escape(display_title(section_title(section, lang)))}</span>'
            f'<span class="meta">{card_meta(stats, ui)}</span>'
            f'</a></li>')
    total = dict(tables=sum(section_stats(s, lang)["tables"] for s in sections),
                 figures=sum(section_stats(s, lang)["figures"] for s in sections),
                 code=sum(section_stats(s, lang)["code"] for s in sections))
    lead = translations.get("strings", {}).get("__guide_lead__", ui["guide_lead"])
    paths = page_paths(lang, section_page=False)
    body = f"""<nav class="guide-crumbs"><a href="{paths['home']}">{ui['home']}</a> <span>/</span> <span>{ui['docs']}</span></nav>
<h1>{ui['guide']}</h1>
<p class="lead">{lead}</p>
<div class="kpi-strip guide-kpis">
  <div class="kpi"><b>{len(sections)}</b><span>{ui['sections_word']}</span></div>
  <div class="kpi"><b>{total['tables']}</b><span>{ui['tables']}</span></div>
  <div class="kpi"><b>{total['figures']}</b><span>{ui['figures']}</span></div>
  <div class="kpi"><b>{total['code']}</b><span>{ui['code_cells']}</span></div>
</div>
<ul class="guide-cards">{''.join(cards)}</ul>"""
    (out_dir / "index.html").write_text(
        page_shell(lang=lang, title=f"{ui['guide']} — JobVision", canonical=f"{SITE}/{'' if lang=='fa' else 'en/'}guide/",
                   description=lead, body=body, sidebar=sidebar_html(model['sections'], -1, lang, depth=""),
                   toc="", other_lang_href=page_paths(lang, section_page=False)["other"],
                   other_lang_absolute=f"{SITE}/en/guide/" if lang == "fa" else f"{SITE}/guide/",
                   paths=page_paths(lang, section_page=False), search_index="search.json"),
        encoding="utf-8")


def write_section_page(section: dict, previous: dict | None, following: dict | None,
                       model: dict, lang: str, out_dir: Path, translations: dict) -> None:
    ui = UI[lang]
    slug = f"{section['num']:02d}-{SLUGS[section['num']]}"
    stats = section_stats(section, lang)
    words = sum(len(re.sub(r"<[^>]+>", " ", b["html"]).split()) for b in section["rendered"] if b["kind"] == "md")
    minutes = max(1, round(words / 170))
    content = "".join(block["html"] for block in section["rendered"])
    pager = '<nav class="guide-pager">'
    if previous:
        pager += (f'<a class="prev" href="../{previous["num"]:02d}-{SLUGS[previous["num"]]}/">'
                  f'<span>{ui["prev"]}</span><b>{html.escape(display_title(section_title(previous, lang)))}</b></a>')
    if following:
        pager += (f'<a class="next" href="../{following["num"]:02d}-{SLUGS[following["num"]]}/">'
                  f'<span>{ui["next"]}</span><b>{html.escape(display_title(section_title(following, lang)))}</b></a>')
    pager += "</nav>"
    meta = (f'<p class="guide-meta">{minutes} {ui["read_time"]} · '
            f'{card_meta(stats, ui)}</p>')
    paths = page_paths(lang, section_page=True)
    crumb = (f'<nav class="guide-crumbs"><a href="{paths["home"]}">{ui["home"]}</a> <span>/</span> '
             f'<a href="../">{ui["docs"]}</a> <span>/</span> <span>{ui["part"]} {section["num"]}</span></nav>')
    body = f"""{crumb}
<h1>{html.escape(section_title(section, lang))}</h1>
{meta}
{content}
<p class="guide-source">{ui['last_update']} · <a href="{REPO}/blob/main/jobvision_analysis.ipynb">{ui['open_notebook']}</a> · <a href="{COLAB}">{ui['run_colab']}</a></p>
{pager}"""
    first_md = next((b["html"] for b in section["rendered"] if b["kind"] == "md"), "")
    description = re.sub(r"\s+", " ", BeautifulSoup(first_md, "html.parser").get_text(" ")).strip()[:200] or section_title(section, lang)
    canonical = f"{SITE}/{'en/' if lang == 'en' else ''}guide/{slug}/"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        page_shell(lang=lang, title=f"{section_title(section, lang)} — JobVision {UI[lang]['guide']}",
                   description=description,
                   canonical=canonical, body=body,
                   sidebar=sidebar_html(model['sections'], section['num'], lang),
                   toc=toc_html(section, lang), other_lang_href=page_paths(lang, section_page=True)["other"] + slug + "/",
                   other_lang_absolute=f"{SITE}/{'guide' if lang == 'en' else 'en/guide'}/{slug}/",
                   paths=page_paths(lang, section_page=True)),
        encoding="utf-8")


def write_search_index(model: dict, lang: str, out_dir: Path) -> None:
    entries = []
    for section in model["sections"]:
        if section["num"] == 0:
            continue
        slug = f"{section['num']:02d}-{SLUGS[section['num']]}"
        base = f"{slug}/" if lang == "fa" else f"../guide/{slug}/"
        text_parts = []
        for block in section["rendered"]:
            if block["kind"] in ("md", "table", "metrics", "text"):
                text_parts.append(BeautifulSoup(block["html"], "html.parser").get_text(" "))
        joined = re.sub(r"\s+", " ", " ".join(text_parts)).strip()
        entries.append(dict(section=section["num"], title=display_title(section_title(section, lang)), url=base,
                            text=joined[:4000]))
        for heading in section.get("headings", []):
            if heading["level"] != "h2":
                continue
            entries.append(dict(section=section["num"], title=heading["text"],
                                url=base + "#" + heading["id"], text=""))
    (out_dir / "search.json").write_text(json.dumps(entries, ensure_ascii=False),
                                         encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="all", choices=["fa", "en", "all"])
    args = parser.parse_args()

    model = load_model()
    langs = ["fa", "en"] if args.lang == "all" else [args.lang]
    built = []
    for lang in langs:
        translations = {}
        if lang == "en":
            if not CONTENT.exists():
                print("skip en: content/en not found")
                continue
            for name in ("strings", "cells", "ui"):
                path = CONTENT / f"{name}.json"
                translations[name] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            UI["en"].update({k: v for k, v in translations.get("ui", {}).items() if k in UI["en"]})
        for section in model["sections"]:
            build_section(section, model, lang, translations,
                          page_paths(lang, section_page=True)["assets"])
        out_root = (ROOT / "docs" / ("guide" if lang == "fa" else "en/guide")).resolve()
        numbered = [s for s in model["sections"] if s["num"] > 0]
        for position, section in enumerate(numbered):
            previous = numbered[position - 1] if position else None
            following = numbered[position + 1] if position + 1 < len(numbered) else None
            out_dir = out_root / f"{section['num']:02d}-{SLUGS[section['num']]}"
            write_section_page(section, previous, following, model, lang, out_dir, translations)
        write_index(model, lang, out_root, translations)
        write_search_index(model, lang, out_root)
        built.append((lang, len(numbered) + 1))
    css = HtmlFormatter(style="one-dark").get_style_defs(".code")
    (ROOT / "docs" / "assets" / "css" / "pygments.css").write_text(
        "/* generated by scripts/build_guide.py */\n" + css + "\n", encoding="utf-8")
    print("built:", built)


if __name__ == "__main__":
    main()
