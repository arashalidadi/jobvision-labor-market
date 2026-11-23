"""Prepare the English translation work files from the notebook (stage 3 helper)."""
import json
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(r"C:/Users/Saeid/Desktop/Data-Scientist-d-learn/JobVision")
TODO = ROOT / "content" / "en" / "_todo"
FA = re.compile(r"[\u0600-\u06FF]")


def strip_wrapper(source: str) -> str:
    text = source.strip()
    text = re.sub(r"^<div[^>]*dir=\"rtl\"[^>]*>\s*", "", text)
    text = re.sub(r"\s*</div>\s*$", "", text)
    return text


def main() -> None:
    if TODO.exists():
        shutil.rmtree(TODO)
    TODO.mkdir(parents=True)

    notebook = json.loads((ROOT / "jobvision_analysis.ipynb").read_text(encoding="utf-8"))
    cells = notebook["cells"]

    # ---- markdown cells, grouped in 8 chunks (keeps section context together)
    section_title = ""
    md_cells = []
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            continue
        text = strip_wrapper("".join(cell["source"]))
        heading = re.search(r"^#\s+(.+)$", text, flags=re.M)
        if heading:
            section_title = heading.group(1).strip()
        if not text.strip():
            continue
        md_cells.append(dict(cell=index, section=section_title, text=text))

    parts = 8
    per_part = (len(md_cells) + parts - 1) // parts
    for part in range(parts):
        chunk = md_cells[part * per_part:(part + 1) * per_part]
        if not chunk:
            continue
        payload = {str(item["cell"]): item["text"] for item in chunk}
        meta = {str(item["cell"]): item["section"] for item in chunk}
        (TODO / f"cells_{part + 1:02d}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        (TODO / f"cells_{part + 1:02d}.meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- Persian strings inside table / metric outputs
    strings = set()
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        for output in cell.get("outputs", []):
            raw = (output.get("data") or {}).get("text/html")
            if not raw:
                continue
            soup = BeautifulSoup("".join(raw), "html.parser")
            for element in soup.select(".jv-caption, .jv-note, .jv-metrics-title, "
                                       ".jv-metrics li, table.jv th, table.jv td"):
                text = re.sub(r"\s+", " ", element.get_text(" ", strip=True))
                if text and FA.search(text):
                    strings.add(text)
    ordered = sorted(strings)
    bundle = 5
    size = (len(ordered) + bundle - 1) // bundle
    chunks = []
    for part in range(bundle):
        chunk = ordered[part * size:(part + 1) * size]
        if not chunk:
            continue
        payload = {item: "" for item in chunk}
        (TODO / f"strings_{part + 1:02d}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        chunks.append(len(chunk))
    (TODO / "README.md").write_text(
        f"""# English translation work files (generated)

- `cells_01.json` … `cells_08.json` — Persian markdown of analysis cells, keyed by notebook cell index.
- `cells_XX.meta.json` — the notebook section each cell belongs to (context).
- `strings_01.json` … `strings_{len(chunks):02d}.json` — Persian phrases that appear inside tables,
  metric blocks, captions and notes (keys are Persian, fill in English values).
- `glossary.md` — preferred terminology; keep it consistent.

Totals: {len(md_cells)} markdown cells, {len(ordered)} Persian strings.
Chunk sizes (strings): {chunks}
""", encoding="utf-8")
    print("cells:", len(md_cells), "| strings:", len(ordered), "| chunks:", parts, len(chunks))
    print("wrote", TODO)


if __name__ == "__main__":
    main()
