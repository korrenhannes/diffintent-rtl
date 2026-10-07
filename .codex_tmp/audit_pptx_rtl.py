#!/usr/bin/env python3
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def main(path: str) -> None:
    failures = []
    mixed_paragraphs = 0
    hebrew = re.compile(r"[\u0590-\u05ff]")
    latin = re.compile(r"[A-Za-z]")
    with zipfile.ZipFile(path) as archive:
        slides = sorted(
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        for slide in slides:
            root = ET.fromstring(archive.read(slide))
            for paragraph in root.iter(A + "p"):
                text = "".join(node.text or "" for node in paragraph.iter(A + "t"))
                props = paragraph.find(A + "pPr")
                rtl = props is not None and props.get("rtl") == "1"
                if hebrew.search(text) and latin.search(text):
                    mixed_paragraphs += 1
                    if not rtl:
                        failures.append(f"{slide}: mixed paragraph is not RTL: {text!r}")
                    if text.count("\u2066") != 1 or text.count("\u2069") != 1:
                        failures.append(f"{slide}: mixed paragraph lacks one balanced LTR isolate: {text!r}")
                    if re.search(r"[\u0590-\u05ff][A-Za-z]|[A-Za-z][\u0590-\u05ff]", text):
                        failures.append(f"{slide}: Hebrew and English touch without spacing: {text!r}")
                    if re.search(r"[\u0590-\u05ff]-[A-Za-z]|[A-Za-z]-[\u0590-\u05ff]", text):
                        failures.append(f"{slide}: Hebrew prefix is attached to English: {text!r}")
                    for run in paragraph.findall(A + "r"):
                        run_text = "".join(node.text or "" for node in run.iter(A + "t"))
                        run_props = run.find(A + "rPr")
                        lang = "" if run_props is None else run_props.get("lang", "")
                        if hebrew.search(run_text) and latin.search(run_text):
                            failures.append(f"{slide}: a single run mixes scripts: {run_text!r}")
                        if hebrew.search(run_text) and not lang.startswith("he"):
                            failures.append(f"{slide}: Hebrew run has language {lang!r}: {run_text!r}")
                        if latin.search(run_text) and not lang.startswith("en"):
                            failures.append(f"{slide}: English run has language {lang!r}: {run_text!r}")
                if hebrew.search(text) and not rtl:
                    failures.append(f"{slide}: Hebrew paragraph is not RTL: {text!r}")
                if latin.search(text) and not hebrew.search(text) and rtl:
                    failures.append(f"{slide}: English-only paragraph is RTL: {text!r}")
    assert len(slides) == 17, f"expected 17 slides, found {len(slides)}"
    assert mixed_paragraphs >= 5, f"expected at least 5 correctly mixed paragraphs, found {mixed_paragraphs}"
    assert not failures, "\n".join(failures)
    print(f"PASS: {len(slides)} slides; {mixed_paragraphs} mixed RTL paragraphs use separate Hebrew and English runs")


if __name__ == "__main__":
    main(sys.argv[1])
