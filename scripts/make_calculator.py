"""Build the interactive salary-band calculator (fa + en) from the dataset.

Outputs
    docs/assets/data/salary-bands.json          raw cells (for reuse)
    docs/tools/salary-calculator.html           Persian page (data embedded, no fetch)
    docs/en/tools/salary-calculator.html        English page (data embedded)

The bands mirror the notebook: disclosed salaries only, salary_mid = (min + max) / 2 in
million toman, grouped by job category × province group × required-experience bucket.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "JobVision-data" / "JobVision_Jobposts_Dataset.csv"
DATA_OUT = ROOT / "docs" / "assets" / "data" / "salary-bands.json"
FA_PAGE = ROOT / "docs" / "tools" / "salary-calculator.html"
EN_PAGE = ROOT / "docs" / "en" / "tools" / "salary-calculator.html"

COLUMNS = ["Jobpost_SalaryCanBeShown", "Jobpost_MinSalary", "Jobpost_MaxSalary",
           "Jobpost_MainJobCategory", "Jobpost_ProvinceFa", "Jobpost_RequiredExperienceYears"]

CATEGORY_EN = {
    "مالی و حسابداری": "Finance and accounting",
    "فروش و بازاریابی - سطوح کارشناسی و مدیریتی": "Sales & marketing — specialist and managerial",
    "فروش و بازاریابی - فروشنده / بازاریاب و ویزیتور / صندوقدار": "Sales — salesperson / merchandiser / cashier",
    "مسئول دفتر / کارمند اداری و ثبت اطلاعات / تایپیست": "Office clerk / data entry / typist",
    "مهندسی صنایع / مدیریت تولید / مدیریت پروژه / مدیریت عملیات": "Industrial engineering / production, project & operations",
    "توسعه نرم افزار و برنامه نویسی": "Software development and programming",
    "کارگر ساده / نیروی خدماتی": "General labour / service worker",
    "شبکه / DevOps / پشتیبانی سخت افزاری و نرم افزاری": "Network / DevOps / IT support",
    "دیجیتال مارکتینگ و سئو": "Digital marketing and SEO",
    "تکنسین فنی / تعمیرکار / کارگر ماهر": "Technician / repairer / skilled worker",
    "other": "Other categories",
}


EXPERIENCE_BUCKETS = [
    ("none", "بدون سابقه", "No experience", -0.5, 0.5),
    ("low", "۱ تا ۲ سال", "1–2 years", 0.5, 2.5),
    ("mid", "۳ تا ۴ سال", "3–4 years", 2.5, 4.5),
    ("high", "۵ سال و بیشتر", "5+ years", 4.5, 99),
    ("unknown", "اعلام نشده", "Not stated", None, None),
]


def load() -> pd.DataFrame:
    frame = pd.read_csv(CSV, usecols=COLUMNS)
    frame = frame[frame.Jobpost_SalaryCanBeShown.astype(bool)]
    frame["salary_mid"] = (frame.Jobpost_MinSalary.astype(float) + frame.Jobpost_MaxSalary.astype(float)) / 2
    frame = frame[frame.salary_mid.between(1, 200)]
    frame["province_group"] = frame.Jobpost_ProvinceFa.eq("تهران").map({True: "tehran", False: "other"})
    experience = frame.Jobpost_RequiredExperienceYears
    bucket = pd.Series("unknown", index=frame.index)
    for key, _, _, low, high in EXPERIENCE_BUCKETS:
        if low is None:
            continue
        bucket = bucket.mask(experience.between(low, high), key)
    frame["experience_bucket"] = bucket
    top_categories = frame.Jobpost_MainJobCategory.value_counts().head(10).index
    frame["category"] = frame.Jobpost_MainJobCategory.where(
        frame.Jobpost_MainJobCategory.isin(top_categories), "other")
    return frame


def summarise(frame: pd.DataFrame, group) -> list[dict]:
    rows = []
    for keys, block in frame.groupby(group, observed=True):
        if len(block) < 40:
            continue
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group, keys))
        record.update({
            "n": int(len(block)),
            "median": round(float(block.salary_mid.median()), 2),
            "q1": round(float(block.salary_mid.quantile(.25)), 2),
            "q3": round(float(block.salary_mid.quantile(.75)), 2),
        })
        rows.append(record)
    return rows


def main() -> None:
    frame = load()
    categories = (frame.category.value_counts().index.tolist())
    cells = summarise(frame, ["category", "province_group", "experience_bucket"])
    overall = summarise(frame, ["province_group", "experience_bucket"])
    payload = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "period": "1401-1402",
        "sample": int(len(frame)),
        "median": round(float(frame.salary_mid.median()), 2),
        "categories": [category for category in categories if category != "other"] + ["other"],
        "experience": [{"key": key, "fa": fa, "en": en} for key, fa, en, _, _ in EXPERIENCE_BUCKETS],
        "cells": cells,
        "overall": overall,
    }
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    FA_PAGE.parent.mkdir(parents=True, exist_ok=True)
    EN_PAGE.parent.mkdir(parents=True, exist_ok=True)
    FA_PAGE.write_text(render(payload, "fa"), encoding="utf-8")
    EN_PAGE.write_text(render(payload, "en"), encoding="utf-8")
    print(f"sample {len(frame):,} | cells {len(cells)} | overall rows {len(overall)}")
    print(f"wrote {DATA_OUT.relative_to(ROOT)} ({DATA_OUT.stat().st_size / 1024:.0f} KB)")
    print(f"wrote {FA_PAGE.relative_to(ROOT)} and {EN_PAGE.relative_to(ROOT)}")


def render(payload: dict, lang: str) -> str:
    fa = lang == "fa"
    data = json.dumps(payload, ensure_ascii=False)
    experience_labels = {item["key"]: (item["fa"] if fa else item["en"]) for item in payload["experience"]}

    title = "ماشین‌حساب باند حقوق" if fa else "Salary band calculator"
    intro = ("باند رقابتی حقوق را برای یک نقش، استان و سطح سابقه ببینید. اعداد از آگهی‌های واقعی "
             "جاب‌ویژن (۱۴۰۱–۱۴۰۲) می‌آیند و میانه و دامنهٔ چارکی هر گروه است."
             if fa else
             "See the competitive salary band for a role, province and experience level. "
             "Numbers come from real JobVision postings (1401–1402): median and interquartile range per group.")
    labels = {
        "category": "دستهٔ شغلی" if fa else "Job category",
        "province": "استان" if fa else "Province",
        "experience": "سابقهٔ لازم" if fa else "Required experience",
        "tehran": "تهران" if fa else "Tehran",
        "other": "سایر استان‌ها" if fa else "Other provinces",
        "result": "باند رقابتی" if fa else "Competitive band",
        "median": "میانه" if fa else "Median",
        "range": "دامنهٔ چارکی" if fa else "Interquartile range",
        "sample": "آگهی دارای حقوق" if fa else "postings with salary",
        "fallback": ("برای این ترکیب آگهی کافی نبود؛ باند کل بازار نشان داده می‌شود."
                     if fa else "Not enough postings for this combination; the market-wide band is shown."),
        "hint": ("باند را با پیشنهاد خود مقایسه کنید: اگر پیشنهاد شما زیر چارک اول است، برای جذب نیرو "
                 "باید بالاتر بروید؛ اگر بالای چارک سوم است، در صدر بازار هستید."
                 if fa else
                 "Compare your offer with the band: below Q1 you will struggle to attract candidates, "
                 "above Q3 you are at the top of the market."),
        "hourly": "" if fa else "",
        "other_category": "سایر دسته‌ها" if fa else "Other categories",
        "back": "راهنمای پروژه" if fa else "Project guide",
        "home": "صفحه اصلی" if fa else "Home",
    }
    direction, align = ("rtl", "right") if fa else ("ltr", "left")
    prefix = "../" if fa else "../../"

    option_label = (lambda category: category if fa else CATEGORY_EN.get(category, category))
    options_category = "".join(
        f'<option value="{category}">{option_label(category)}</option>'
        for category in payload["categories"])
    options_experience = "".join(
        f'<option value="{item["key"]}">{experience_labels[item["key"]]}</option>'
        for item in payload["experience"])

    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — JobVision</title>
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
<style>
  .calc-wrap {{ max-width: 980px; margin: 0 auto; padding: 28px 20px 64px; }}
  .calc-head h1 {{ font-size: clamp(1.5rem, 3vw, 2.1rem); margin: 6px 0 10px; }}
  .calc-head p {{ color: var(--muted, #5c6b6b); line-height: 1.9; margin: 0 0 22px; }}
  .calc-controls {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-bottom: 22px; }}
  .calc-controls label {{ display: block; font-size: .85rem; font-weight: 700; margin-bottom: 6px; }}
  .calc-controls select {{ width: 100%; padding: 10px 12px; border-radius: 10px; border: 1px solid #cfe0dd;
                           background: #fff; font: inherit; color: inherit; }}
  .calc-result {{ border: 1px solid #cfe0dd; border-radius: 16px; padding: 20px 22px; background: #f7fbfa; }}
  .calc-band {{ display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }}
  .calc-number {{ font-size: 2.1rem; font-weight: 800; color: #1f5f5a; }}
  .calc-unit {{ color: #5c6b6b; font-size: .95rem; }}
  .calc-range {{ color: #445; font-size: .95rem; margin-top: 4px; }}
  .calc-bar {{ position: relative; height: 14px; border-radius: 999px; background: #e3efed; margin: 18px 0 8px; }}
  .calc-bar span {{ position: absolute; inset-block: 0; border-radius: 999px;
                    background: linear-gradient(90deg, #7fb8b1, #2f7f7a); }}
  .calc-scale {{ display: flex; justify-content: space-between; font-size: .78rem; color: #7b8c8c; }}
  .calc-note {{ margin-top: 14px; font-size: .87rem; color: #6b4a13; background: #fff8ea;
                border: 1px solid #f0e0bf; border-radius: 10px; padding: 10px 12px; }}
  .calc-meta {{ margin-top: 18px; font-size: .85rem; color: #5c6b6b; }}
  .calc-links {{ margin-top: 26px; display: flex; gap: 14px; flex-wrap: wrap; font-size: .9rem; }}
</style>
</head>
<body>
<main class="calc-wrap" style="text-align:{align}">
  <div class="calc-head">
    <p class="calc-links"><a href="{'../index.html' if fa else '../index.html'}">{labels['home']}</a> ·
      <a href="../guide/">{labels['back']}</a></p>
    <h1>{title}</h1>
    <p>{intro}</p>
  </div>

  <div class="calc-controls">
    <div><label for="category">{labels['category']}</label>
      <select id="category">{options_category}</select></div>
    <div><label for="province">{labels['province']}</label>
      <select id="province">
        <option value="tehran">{labels['tehran']}</option>
        <option value="other">{labels['other']}</option>
      </select></div>
    <div><label for="experience">{labels['experience']}</label>
      <select id="experience">{options_experience}</select></div>
  </div>

  <section class="calc-result" aria-live="polite">
    <div class="calc-band">
      <span class="calc-number" id="median">—</span>
      <span class="calc-unit">{'میلیون تومان در ماه' if fa else 'million toman / month'}</span>
    </div>
    <div class="calc-range" id="range"></div>
    <div class="calc-bar"><span id="bar" style="inset-inline-start:0; inset-inline-end:100%"></span></div>
    <div class="calc-scale"><span id="q1">—</span><span id="q3">—</span></div>
    <div class="calc-meta" id="meta"></div>
    <div class="calc-note" id="note" hidden>{labels['fallback']}</div>
  </section>

  <p class="calc-meta">{labels['hint']}</p>
</main>

<script>
const DATA = {data};
const LABELS = {json.dumps(labels, ensure_ascii=False)};
const EXPERIENCE = Object.fromEntries(DATA.experience.map(item => [item.key, item.{'fa' if fa else 'en'}]));
const el = id => document.getElementById(id);

function pick(category, province, experience) {{
  return DATA.cells.find(cell => cell.category === category
                                && cell.province_group === province
                                && cell.experience_bucket === experience);
}}

function pickOverall(province, experience) {{
  return DATA.overall.find(cell => cell.province_group === province && cell.experience_bucket === experience)
      || DATA.overall.find(cell => cell.province_group === province) || DATA.overall[0];
}}

function format(value) {{
  return value.toLocaleString('{('fa-IR' if fa else 'en-US')}', {{ maximumFractionDigits: 1 }});
}}

function update() {{
  const category = el('category').value;
  const province = el('province').value;
  const experience = el('experience').value;
  const cell = pick(category, province, experience);
  const used = cell || pickOverall(province, experience) || {{ median: DATA.median, q1: DATA.median * .8, q3: DATA.median * 1.5, n: DATA.sample }};
  el('note').hidden = Boolean(cell);
  el('median').textContent = format(used.median);
  el('q1').textContent = format(used.q1);
  el('q3').textContent = format(used.q3);
  el('range').textContent = `${{LABELS.range}}: ${{format(used.q1)}} – ${{format(used.q3)}}`;
  el('meta').textContent = `${{LABELS.sample}}: ${{used.n.toLocaleString('{('fa-IR' if fa else 'en-US')}')}}`;
  const ceiling = Math.max(used.q3 * 1.35, 1);
  const start = Math.max(0, used.q1 / ceiling * 100);
  const width = Math.max(6, (used.q3 - used.q1) / ceiling * 100);
  const bar = el('bar');
  bar.style.insetInlineStart = start + '%';
  bar.style.insetInlineEnd = 'auto';
  bar.style.width = width + '%';
}}

['category', 'province', 'experience'].forEach(id => el(id).addEventListener('change', update));
update();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()