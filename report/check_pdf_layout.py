#!/usr/bin/env python3
"""Check the final PDF for the table split found during visual review."""

import subprocess
import sys
from pathlib import Path


path = Path(sys.argv[1] if len(sys.argv) > 1 else "report/DiffIntent_RTL_Final_Report_Hebrew.pdf")
text = subprocess.check_output(["pdftotext", "-layout", str(path), "-"]).decode("utf-8", "ignore")
pages = text.split("\f")
assert any("TF-IDF + LR" in page and "Hierarchical Transformer" in page for page in pages), (
    "model comparison table is split across PDF pages"
)
print(f"PASS: {path}")
