"""Build a Google-Slides-importable PPTX from the slide content."""
import re
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from slides_content import SLIDES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "jobvision_presentation.pptx"

TEAL = RGBColor(0x2F, 0x7F, 0x7A)
DARK = RGBColor(0x16, 0x30, 0x2E)
MUTED = RGBColor(0x4C, 0x66, 0x63)
GOLD = RGBColor(0xC9, 0x97, 0x4B)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def add_rtl_paragraph(text_frame, text, size, color, bold=False, space_after=6, first=False):
    paragraph = text_frame.paragraphs[0] if first else text_frame.add_paragraph()
    paragraph.alignment = PP_ALIGN.RIGHT
    paragraph.space_after = Pt(space_after)
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Tahoma"
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("rtl", "1")
    return paragraph


def strip_html(fragment):
    text = re.sub(r"<br\s*/?>", "\n", fragment)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


for number, slide in enumerate(SLIDES, start=1):
    page = prs.slides.add_slide(blank)
    has_image = bool(slide.get("image"))
    text_width = Inches(6.2) if has_image else Inches(11.6)

    kicker_box = page.shapes.add_textbox(Inches(0.7), Inches(0.35), Inches(11.9), Inches(0.4))
    add_rtl_paragraph(kicker_box.text_frame, slide.get("kicker", ""), 12, TEAL, bold=True, first=True)

    title_box = page.shapes.add_textbox(Inches(0.7), Inches(0.75), Inches(11.9), Inches(1.1))
    add_rtl_paragraph(title_box.text_frame, slide["title"], 28, DARK, bold=True, first=True)

    top = 2.0
    if slide.get("stats"):
        stat_width = 11.9 / len(slide["stats"])
        for index, (value, label) in enumerate(slide["stats"]):
            box = page.shapes.add_textbox(Inches(0.7 + index * stat_width), Inches(1.95),
                                          Inches(stat_width - 0.2), Inches(1.0))
            add_rtl_paragraph(box.text_frame, value, 22, TEAL, bold=True, first=True, space_after=0)
            add_rtl_paragraph(box.text_frame, label, 10, MUTED, space_after=0)
        top = 3.1

    body_box = page.shapes.add_textbox(Inches(0.7), Inches(top), text_width, Inches(4.4))
    frame = body_box.text_frame
    frame.word_wrap = True
    lines = []
    for line in strip_html(slide["body"]).split("\n"):
        lines.append(line)
    first = True
    for line in lines:
        if not line:
            continue
        add_rtl_paragraph(frame, line, 15, DARK, first=first, space_after=8)
        first = False

    if has_image:
        image = ROOT / slide["image"]
        page.shapes.add_picture(str(image), Inches(7.1), Inches(2.1), width=Inches(5.6))

    if slide.get("note"):
        note_box = page.shapes.add_textbox(Inches(0.7), Inches(6.85), Inches(11.9), Inches(0.4))
        add_rtl_paragraph(note_box.text_frame, strip_html(slide["note"]), 9, MUTED, first=True)

    bar = page.shapes.add_shape(1, Inches(0), Inches(7.38), prs.slide_width, Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = GOLD
    bar.line.fill.background()

prs.save(OUT)
print("wrote", OUT, "slides", len(prs.slides.__iter__.__self__._sldIdLst))