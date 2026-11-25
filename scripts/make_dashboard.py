"""Generate the project dashboard page (fa + en): key numbers, six charts, deep links."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = "https://arashalidadi.github.io/jobvision-labor-market"

KPIS = [
    ("۳۶۰٬۰۸۳", "360,083", "آگهی در ۲۳ ماه", "postings across 23 months"),
    ("۳۳٫۱٪", "33.1%", "نرخ افشای حقوق", "salary disclosure rate"),
    ("۱۱ میلیون", "11 million", "میانه حقوق ماهانه (IQR ۹–۱۷٫۵)", "median monthly salary (IQR 9–17.5)"),
    ("۴۰", "40", "مقدار یکتای حقوق (باندبندی بازار)", "unique salary values (anchored market)"),
    ("۶۴٫۶٪", "64.6%", "سهم تهران از آگهی‌ها", "Tehran share of postings"),
    ("۱٬۷۵۲", "1,752", "نفوذ تهران در هر ۱۰۰ هزار نفر (ملی: ۴۵۰)", "Tehran penetration per 100k (national: 450)"),
    ("۵۳٫۸٪", "53.8%", "آگهی‌های دارای فهرست مهارت", "postings listing skills"),
    ("۱٬۸۵۲", "1,852", "تمرکز بازار (HHI از ۱۰٬۰۰۰)", "market concentration (HHI of 10,000)"),
]

CHARTS = [
    ("fig_10_1", "روند ماهانه حجم آگهی", "Monthly posting volume",
     "10-time-trends-and-seasonality", "بخش ۱۰ — روند زمانی"),
    ("fig_9_1", "پرتکرارترین مقادیر حقوق", "Most frequent salary values",
     "09-salary-disclosure", "بخش ۹ — سازوکار گمشدگی حقوق"),
    ("fig_10_5", "شاخص فصلی به تفکیک دستهٔ شغلی", "Seasonal index by job category",
     "10-time-trends-and-seasonality", "بخش ۱۰ — فصلی‌بودن"),
    ("fig_14_6", "نفوذ آگهی در استان‌ها", "Provincial penetration",
     "14-geography-and-provinces", "بخش ۱۴ — جغرافیا"),
    ("fig_19_3", "پاداش خالص مهارت‌ها", "Net skill premiums",
     "19-skills-evolution", "بخش ۱۹ — تحول مهارت‌ها"),
    ("fig_8_5", "ساعت کاری، سابقه و مزایا", "Hours, experience and benefits",
     "08-correlation-and-collinearity", "بخش ۸ — همبستگی و روابط"),
]

TITLE = {"fa": "داشبورد پروژه", "en": "Project dashboard"}
LEAD = {
    "fa": "چکیدهٔ یک‌صفحه‌ای پروژه: هشت عدد کلیدی، شش نمودار محوری و مسیر رفتن به تحلیل کامل هر بخش.",
    "en": "A one-page summary of the project: eight headline numbers, six core charts and links into the full analysis.",
}
NAV = {
    "fa": [("../index.html", "صفحه اصلی"), ("../guide/", "راهنما"),
           ("../tools/salary-calculator.html", "ماشین‌حساب حقوق")],
    "en": [("../index.html", "Home"), ("../guide/", "Guide"),
           ("../tools/salary-calculator.html", "Salary calculator")],
}
LINKS = {"fa": "خواندن تحلیل کامل", "en": "Read the full analysis"}


def render(lang: str) -> str:
    fa = lang == "fa"
    direction = "rtl" if fa else "ltr"
    prefix = "../" if fa else "../../"
    index = 0 if fa else 1
    cards = "".join(
        f'<div class="dash-kpi"><b>{item[0 if fa else 1]}</b><span>{item[2 if fa else 3]}</span></div>'
        for item in KPIS)

    figures = []
    guide_root = "../guide/" if fa else "../guide/"
    for stem, fa_title, en_title, slug, fa_link in CHARTS:
        title = fa_title if fa else en_title
        href = f"{guide_root}{slug}/"
        figures.append(f"""<figure class="dash-fig">
      <a href="{href}"><img src="{prefix}assets/img/{stem}-sm.webp" alt="{title}" loading="lazy" decoding="async"></a>
      <figcaption>{title}<a class="dash-more" href="{href}">{LINKS['fa' if fa else 'en']} →</a></figcaption>
    </figure>""")

    nav = " · ".join(f'<a href="{href}">{label}</a>' for href, label in NAV[lang])
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE[lang]} — JobVision</title>
<link rel="icon" href="{prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
<style>
  .dash {{ max-width: 1080px; margin: 0 auto; padding: 28px 20px 70px; }}
  .dash h1 {{ font-size: clamp(1.6rem, 3vw, 2.2rem); margin: 8px 0 10px; }}
  .dash .dash-nav {{ font-size: .9rem; color: #5c6b6b; }}
  .dash .dash-lead {{ color: #5c6b6b; line-height: 1.9; margin: 0 0 24px; }}
  .dash-kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin-bottom: 30px; }}
  .dash-kpi {{ border: 1px solid #cfe0dd; border-radius: 14px; padding: 14px 16px; background: #f7fbfa; }}
  .dash-kpi b {{ display: block; font-size: 1.5rem; color: #1f5f5a; }}
  .dash-kpi span {{ font-size: .85rem; color: #5c6b6b; }}
  .dash-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
  .dash-fig {{ margin: 0; border: 1px solid #e2ecea; border-radius: 14px; overflow: hidden; background: #fff; }}
  .dash-fig img {{ display: block; width: 100%; height: auto; }}
  .dash-fig figcaption {{ padding: 10px 12px; font-size: .9rem; display: flex; justify-content: space-between;
                          gap: 10px; flex-wrap: wrap; align-items: center; }}
  .dash-more {{ font-size: .82rem; color: #2f7f7a; white-space: nowrap; }}
</style>
</head>
<body>
<main class="dash">
  <p class="dash-nav">{nav}</p>
  <h1>{TITLE[lang]}</h1>
  <p class="dash-lead">{LEAD[lang]}</p>
  <div class="dash-kpis">{cards}</div>
  <div class="dash-grid">{''.join(figures)}</div>
</main>
</body>
</html>
"""


def main() -> None:
    for lang, folder in (("fa", DOCS / "dashboard"), ("en", DOCS / "en" / "dashboard")):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(render(lang), encoding="utf-8")
        print("wrote", (folder / "index.html").relative_to(ROOT))


if __name__ == "__main__":
    main()