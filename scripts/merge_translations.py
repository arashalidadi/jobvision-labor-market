"""Merge the translated chunks into content/en/{cells,strings}.json (stage 3 helper)."""
import json
from pathlib import Path

ROOT = Path(r"C:/Users/Saeid/Desktop/Data-Scientist-d-learn/JobVision")
TODO = ROOT / "content" / "en" / "_todo"
OUT = ROOT / "content" / "en" / "_out"
DEST = ROOT / "content" / "en"


def merge(kind: str) -> tuple[int, list[str]]:
    merged: dict[str, str] = {}
    order: list[str] = []
    for part in range(1, 9):
        source = TODO / f"{kind}_{part:02d}.json"
        target = OUT / f"{kind}_{part:02d}.en.json"
        if not source.exists():
            continue
        keys = json.loads(source.read_text(encoding="utf-8"))
        order.extend(keys.keys())
        if not target.exists():
            print(f"  warning: {target.name} missing — {len(keys)} keys left as source text")
            continue
        merged.update(json.loads(target.read_text(encoding="utf-8")))
    ordered = {key: merged[key] for key in order if key in merged}
    (DEST / f"{kind}.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    missing = [key for key in order if key not in merged]
    return len(ordered), missing


if __name__ == "__main__":
    for kind in ("cells", "strings"):
        count, missing = merge(kind)
        print(f"{kind}: merged {count} entries | unmatched {len(missing)}")
