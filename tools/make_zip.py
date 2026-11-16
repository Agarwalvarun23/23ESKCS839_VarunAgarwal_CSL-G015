"""Package the report PDF and source code for submission.

Usage:
    python tools/make_zip.py
"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "23ESKCS839_VarunAgarwal_CSL-G15"
INCLUDE = ["README.md", "requirements.txt", "salting_demo", "data", "results",
           "screenshots", "tools", f"report/{NAME}.pdf", f"report/{NAME}.docx"]


def files():
    for item in INCLUDE:
        path = ROOT / item
        paths = [path] if path.is_file() else sorted(path.rglob("*"))
        for p in paths:
            if p.is_file() and "__pycache__" not in p.parts:
                yield p


def main():
    out = ROOT / "report" / f"{NAME}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files():
            z.write(p, Path(NAME) / p.relative_to(ROOT))
    print(f"Saved {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
