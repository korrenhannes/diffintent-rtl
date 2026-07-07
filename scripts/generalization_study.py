"""Generalization study: reproduces the cross-project comparison and the
weak-labeler improvement, producing both proof figures.

Prerequisite: the raw mined files must exist for both projects, i.e. run:
    python scripts/extract_commits.py --config configs/data_opentitan_smoke.yaml
    python scripts/extract_commits.py --config configs/data_caliptra_smoke.yaml

Then run:
    python scripts/generalization_study.py
"""
import json
import re
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# --- the ORIGINAL keyword lists (baseline labeler) ---
ORIGINAL = {
    "bug_fix": ["fix", "bug", "wrong", "regression", "incorrect", "issue", "repair", "fail", "failure"],
    "feature_or_behavior_change": ["add", "implement", "support", "enable", "introduce", "new", "feature"],
    "refactor_cleanup": ["refactor", "cleanup", "rename", "move", "style", "tidy", "simplify", "remove unused"],
    "configuration_timing": ["clock", "reset", "timing", "param", "parameter", "width", "config", "fsm", "latency"],
}
# --- the IMPROVED keyword lists (our contribution) ---
IMPROVED = {
    "bug_fix": ORIGINAL["bug_fix"] + ["correct", "resolve", "patch", "restore", "hotfix", "defect", "broken", "crash"],
    "feature_or_behavior_change": ORIGINAL["feature_or_behavior_change"] + ["enhance", "improve", "optimize", "extend", "behavior", "behaviour", "update", "disable", "change", "modify", "modular"],
    "refactor_cleanup": ORIGINAL["refactor_cleanup"] + ["restructure", "reorganize", "reorganise", "deduplicate", "format"],
    "configuration_timing": ORIGINAL["configuration_timing"] + ["frequency", "constraint", "pipeline", "threshold"],
}
INT = ["bug_fix", "feature_or_behavior_change", "refactor_cleanup", "configuration_timing"]


def matches(message, patterns):
    c = 0
    for p in patterns:
        esc = re.escape(p)
        if " " in p:
            c += len(re.findall(esc, message))
        else:
            c += len(re.findall(rf"\b{esc}\w*\b", message))
    return c


def label(message, rules):
    m = message.strip().lower()
    if not m or m in {"update", "misc", "cleanup", "fixup", "changes"}:
        return None
    if m.startswith("revert"):
        return None
    scores = {k: matches(m, v) for k, v in rules.items()}
    mx = max(scores.values())
    if mx <= 0:
        return None
    winners = [k for k, s in scores.items() if s == mx]
    if len(winners) > 1:
        return None
    return winners[0]


def analyze(raw_path, rules):
    raw = [json.loads(l) for l in open(raw_path)]
    labels = [label(r["commit_message"], rules) for r in raw]
    kept = [l for l in labels if l is not None]
    discard_pct = 100 * (1 - len(kept) / len(raw)) if raw else 0
    dist = {k: kept.count(k) for k in INT}
    return len(raw), len(kept), discard_pct, dist


repos = {"OpenTitan": RAW / "opentitan_rtl_commits_smoke.jsonl",
         "Caliptra": RAW / "caliptra_rtl_commits_smoke.jsonl"}

print("=== Generalization & labeler-improvement study ===")
res = {}
for name, path in repos.items():
    raw, kept_o, disc_o, _ = analyze(path, ORIGINAL)
    _, kept_i, disc_i, dist_i = analyze(path, IMPROVED)
    res[name] = {"raw": raw, "disc_o": disc_o, "disc_i": disc_i, "dist": dist_i, "kept_i": kept_i}
    print(f"\n{name}: mined={raw}")
    print(f"  discard (original labeler): {disc_o:.0f}%")
    print(f"  discard (improved labeler): {disc_i:.0f}%")

# Figure 1: before/after discard
fig, ax = plt.subplots(figsize=(7, 4.5))
x = np.arange(len(repos)); w = 0.36
before = [res[r]["disc_o"] for r in repos]
after = [res[r]["disc_i"] for r in repos]
b1 = ax.bar(x - w/2, before, w, label="Before (original)", color="#bbbbbb")
b2 = ax.bar(x + w/2, after, w, label="After (improved)", color="#2c7fb8")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+1, f"{int(b.get_height())}%", ha="center", fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(list(repos))
ax.set_ylabel("% discarded by weak labeler"); ax.set_ylim(0, max(before)+15)
ax.set_title("Improved weak labeling reduces discards\nand narrows the cross-project gap")
ax.legend(); fig.tight_layout()
fig.savefig(OUT / "labeler_improvement.png", dpi=130); plt.close(fig)

# Figure 2: intent distribution (improved labeler)
fig, ax = plt.subplots(figsize=(7, 4.5))
SHORT = ["bug fix", "feature", "refactor", "config/timing"]
xc = np.arange(4)
for k, r in enumerate(repos):
    tot = res[r]["kept_i"] or 1
    pct = [100*res[r]["dist"][lbl]/tot for lbl in INT]
    ax.bar(xc + (k-0.5)*w, pct, w, label=r, color=["#377eb8", "#e41a1c"][k])
ax.set_xticks(xc); ax.set_xticklabels(SHORT, rotation=20, ha="right")
ax.set_ylabel("% of examples"); ax.set_title("Change-type profile differs by project")
ax.legend(); fig.tight_layout()
fig.savefig(OUT / "generalization_compare.png", dpi=130); plt.close(fig)

print("\nSaved figures: outputs/figures/labeler_improvement.png, generalization_compare.png")
