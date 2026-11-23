"""Regenerate notebooks/jobvision_colab.ipynb from jobvision_analysis.ipynb.

The Colab copy is byte-for-byte the same analysis (all outputs cleared) plus two
setup cells at the top: one installs the pinned requirements, the next downloads
the dataset from Hugging Face into /content/ where the loader looks for it.

    python scripts/build_colab_notebook.py
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "jobvision_analysis.ipynb"
TARGET = ROOT / "notebooks" / "jobvision_colab.ipynb"

SETUP_CELLS = [
    {
        "cell_type": "markdown",
        "metadata": {"id": "colab-banner"},
        "source": [
            "# تحلیل بازار کار ایران — نسخه Google Colab\n",
            "\n",
            "این نسخه از نوت‌بوک اصلی ساخته شده است: همان تحلیل، همان شماره جدول‌ها و نمودارها. دو سلول\n",
            "تنظیمی زیر وابستگی‌ها را نصب می‌کنند و داده را از Hugging Face در `/content` دانلود می‌کنند.\n",
            "\n",
            "**ترتیب اجرا:** Runtime → Run all. کل مسیر با CPU و حدود ۱۲ گیگابایت رم در چند دقیقه اجرا می‌شود.\n",
            "\n",
            "مخزن: https://github.com/arashalidadi/jobvision-labor-market — لایسنس داده: CC BY-NC 4.0\n",
        ],
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": "colab-setup"},
        "outputs": [],
        "source": [
            "# نصب وابستگی‌های پروژه (نسخه‌های دقیق از requirements-lock.txt)\n",
            "REPO = 'https://raw.githubusercontent.com/arashalidadi/jobvision-labor-market/main'\n",
            "!pip install -q -r {REPO}/requirements.txt\n",
            "\n",
            "import sys\n",
            "print(sys.version)\n",
        ],
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": "colab-dataset"},
        "outputs": [],
        "source": [
            "# دانلود داده خام در /content (تنها بار اول لازم است؛ حدود ۳۷۴ مگابایت)\n",
            "from pathlib import Path\n",
            "\n",
            "DATA = Path('/content/JobVision_Jobposts_Dataset.csv')\n",
            "if not DATA.exists():\n",
            "    !pip install -q huggingface_hub\n",
            "    from huggingface_hub import hf_hub_download\n",
            "    path = hf_hub_download(\n",
            "        repo_id='JobVision/JobVision_Jobposts_Dataset',\n",
            "        filename='JobVision_Jobposts_Dataset.csv',\n",
            "        repo_type='dataset',\n",
            "        local_dir='/content',\n",
            "    )\n",
            "    DATA = Path(path)\n",
            "print(f'{DATA} — {DATA.stat().st_size / 1024**2:,.0f} MB')\n",
            "\n",
            "# نوت‌بوک، خروجی نمودارها را در outputs/figures ذخیره می‌کند\n",
            "Path('/content/outputs/figures').mkdir(parents=True, exist_ok=True)\n",
        ],
    },
]


def strip_outputs(nb: dict) -> dict:
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
    return nb


def main() -> None:
    nb = json.loads(SOURCE.read_text(encoding="utf-8"))
    nb = strip_outputs(nb)
    setup = copy.deepcopy(SETUP_CELLS)
    nb["cells"] = setup + nb["cells"]
    nb["metadata"]["colab"] = {"provenance": [], "toc_visible": True}
    nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "name": "python3"}
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    size = TARGET.stat().st_size / 1024
    print(f"wrote {TARGET.relative_to(ROOT)} — {len(nb['cells'])} cells, {size:,.0f} KB")


if __name__ == "__main__":
    main()
