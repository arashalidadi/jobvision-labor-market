"""Prepare the static assets used by the GitHub Pages site (docs/).

Run it from the repository root after the notebook has been executed:

    python scripts/build_site_assets.py

It reads ``outputs/figures/*.png`` and writes two WebP derivatives per figure
(a 1500 px view for the lightbox and a 700 px thumbnail for the grid) plus the
1200x630 social preview card. Only Pillow is required.

Persian shaping needs libraqm; when Pillow was built without it the script
falls back to arabic-reshaper + python-bidi (already project dependencies).
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "outputs" / "cache").mkdir(parents=True, exist_ok=True)
SRC = ROOT / "outputs" / "figures"
OUT = ROOT / "docs" / "assets" / "img"
FONT_DIR = ROOT / "docs" / "assets" / "fonts"

WIDE, THUMB = 1500, 700
WEBP_QUALITY = 88


def slug(path: Path) -> str:
    return re.sub(r"[^a-z0-9_-]+", "_", path.stem.lower())


def optimize_figures() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for png in sorted(SRC.glob("fig_*.png")):
        image = Image.open(png)
        if image.mode != "RGB":
            base = Image.new("RGB", image.size, "white")
            base.paste(image, mask=image.getchannel("A") if image.mode == "RGBA" else None)
            image = base
        name = slug(png)
        wide = image.copy()
        wide.thumbnail((WIDE, 4000), Image.LANCZOS)
        wide.save(OUT / f"{name}.webp", "WEBP", quality=WEBP_QUALITY, method=6)
        thumb = image.copy()
        thumb.thumbnail((THUMB, 4000), Image.LANCZOS)
        thumb.save(OUT / f"{name}-sm.webp", "WEBP", quality=82, method=6)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Social preview card (1200 x 630, Open Graph / Twitter summary_large_image)
# ---------------------------------------------------------------------------
INK = (255, 255, 255, 255)
SOFT = (200, 228, 223, 255)
GOLD = (216, 170, 98, 255)
DIM = (132, 180, 174, 255)


def _mix(fg, bg, alpha):
    return tuple(int(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))


ARABIC_LETTER = re.compile(r"[\u0621-\u064a\u0671-\u06d3\u200c]")


def _shape(text: str, has_raqm: bool) -> str:
    """Shape Persian text for drawing.

    Strings without Arabic letters (pure numbers, Latin, symbols) must skip the
    bidi pass entirely: in an RTL paragraph the bidi algorithm would otherwise
    reorder their digits, so "۳۶۰٬۰۸۳" would render as "۳۸۰٬۰۶۳".
    """
    if has_raqm or not ARABIC_LETTER.search(text):
        return text
    import arabic_reshaper
    from bidi.algorithm import get_display

    return get_display(arabic_reshaper.reshape(text))


def social_card() -> None:
    width, height = 1200, 630
    card = Image.new("RGB", (width, height), (11, 63, 59))
    draw = ImageDraw.Draw(card)
    for y in range(height):
        t = y / height
        draw.line([(0, y), (width, y)],
                  fill=(int(12 + 4 * t), int(70 - 26 * t), int(66 - 24 * t)))

    def load(name: str, size: int):
        path = FONT_DIR / name
        return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()

    title = load("Vazirmatn-Bold.ttf", 50)
    small = load("Vazirmatn-Bold.ttf", 24)
    micro = load("Vazirmatn-Regular.ttf", 20)
    chip_value = load("Vazirmatn-Bold.ttf", 28)
    latin = load("Vazirmatn-Bold.ttf", 19)

    try:
        draw.textbbox((0, 0), "ت", font=title, direction="rtl", language="fa")
        has_raqm = True
    except (KeyError, ValueError):
        has_raqm = False

    def put(right_x, y, text, font, fill):
        shaped = _shape(text, has_raqm)
        w = draw.textlength(shaped, font=font)
        draw.text((right_x - w, y), shaped, font=font, fill=fill)

    draw.rectangle([60, 96, 72, 236], fill=GOLD)
    put(width - 60, 82, "بازار کار ایران در آینه", title, INK)
    put(width - 60, 146, "۳۶۰ هزار آگهی استخدامی", title, INK)
    put(width - 60, 246, "حقوق، مهارت، جغرافیا و رقابت", small, SOFT)
    put(width - 60, 284, "جاب‌ویژن — فروردین ۱۴۰۱ تا بهمن ۱۴۰۲", small, DIM)

    chips = [("۳۶۰٬۰۸۳", "آگهی"), ("۴۳", "ستون"), ("۲۳", "ماه"),
             ("۳۳٫۱٪", "با حقوق"), ("۱۱٫۰", "میانه حقوق")]
    w, h, gap, right, top = 200, 100, 12, width - 60, 356
    for i, (value, label) in enumerate(chips):
        x1 = right - i * (w + gap)
        x0c = x1 - w
        fill = _mix((255, 255, 255), (12, 62, 58), 0.07)
        edge = _mix((255, 255, 255), (12, 62, 58), 0.16)
        draw.rounded_rectangle([x0c, top, x1, top + h], radius=14, fill=fill, outline=edge, width=1)
        put(x1 - 18, top + 14, value, chip_value, INK)
        put(x1 - 18, top + 56, label, micro, DIM)

    stroke = _mix((255, 255, 255), (12, 62, 58), 0.22)
    draw.line([(60, height - 92), (width - 60, height - 92)], fill=stroke, width=1)
    draw.text((60, height - 58), "JobVision Jobposts — Iran Labor Market Analytics", font=latin, fill=DIM)
    put(width - 60, height - 58, "github.com/arashalidadi", latin, GOLD)

    card.save(OUT / "og-cover.png", "PNG", optimize=True)
    card.resize((600, 315), Image.LANCZOS).save(str(ROOT / "outputs" / "cache" / "og_small.png"))


if __name__ == "__main__":
    n = optimize_figures()
    print(f"optimized {n} figures -> {OUT.relative_to(ROOT)}")
    social_card()
    print("social card: written")
