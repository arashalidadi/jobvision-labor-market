"""Merge the translated chunks into content/en/{cells,strings}.json.

Cells: every markdown cell of the notebook, keyed by cell index (must be complete).
Strings: table titles, captions, axis labels and metric labels keyed by their Persian text —
previous translations are kept, newly added keys come from the extra chunks, and pure
number/percent labels are converted locally (no translation needed).
"""
import json
import re
from pathlib import Path

ROOT = Path(r"C:/Users/Saeid/Desktop/Data-Scientist-d-learn/JobVision")
TODO = ROOT / "content" / "en" / "_todo"
OUT = ROOT / "content" / "en" / "_out"
DEST = ROOT / "content" / "en"

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٬", "0123456789,")
NUMERIC_ONLY = re.compile(r"^[\d۰-۹٫٬,.\s٪%±+\-–—/()]+$")


def local_number(text: str) -> str:
    """Labels that are only numbers/percent signs need digit conversion, not translation."""
    return text.translate(FA_DIGITS)


def merge_cells() -> tuple[int, list[str]]:
    merged: dict[str, str] = {}
    order: list[str] = []
    for part in range(1, 9):
        source = TODO / f"cells_{part:02d}.json"
        target = OUT / f"cells_{part:02d}.en.json"
        if not source.exists():
            continue
        keys = json.loads(source.read_text(encoding="utf-8"))
        order.extend(keys.keys())
        if target.exists():
            merged.update(json.loads(target.read_text(encoding="utf-8")))
    ordered = {key: merged[key] for key in order if key in merged}
    (DEST / "cells.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(ordered), [key for key in order if key not in merged]


def merge_strings() -> tuple[int, list[str], int]:
    previous = json.loads((DEST / "strings.json").read_text(encoding="utf-8")) if (DEST / "strings.json").exists() else {}
    extra: dict[str, str] = {}
    for name in ("strings_extra_1", "strings_extra_2"):
        path = OUT / f"{name}.en.json"
        if path.exists():
            extra.update({key: value for key, value in json.loads(path.read_text(encoding="utf-8")).items() if value})

    order: list[str] = []
    merged: dict[str, str] = {}
    local = 0
    for part in range(1, 6):
        source = TODO / f"strings_{part:02d}.json"
        if not source.exists():
            continue
        for key in json.loads(source.read_text(encoding="utf-8")):
            if key in merged:
                continue
            order.append(key)
            if key in previous and previous[key]:
                merged[key] = previous[key]
            elif key in extra:
                merged[key] = extra[key]
            elif NUMERIC_ONLY.match(key):
                merged[key] = local_number(key)
                local += 1
    ordered = {key: merged[key] for key in order if key in merged}
    (DEST / "strings.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(ordered), [key for key in order if key not in merged], local


if __name__ == "__main__":
    cell_count, cell_missing = merge_cells()
    print(f"cells: merged {cell_count} | unmatched {len(cell_missing)}")
    if cell_missing:
        print("  first missing cell keys:", cell_missing[:10])
    string_count, string_missing, local_count = merge_strings()
    print(f"strings: merged {string_count} | unmatched {len(string_missing)} | numeric auto: {local_count}")
    if string_missing:
        print("  first unmatched strings:", [text[:60] for text in string_missing[:10]])