"""5-fold cross-validation for the hardware-aware feature model.

Evaluates the RTL-feature Random Forest and the TF-IDF baseline under the same
StratifiedKFold protocol, reports mean +/- std macro-F1, and prints a per-class
breakdown of the most informative hardware cues. Produces a CV comparison figure.

Run (after building the medium dataset):
    python3 scripts/rtl_features_cv.py
"""
import json, re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import cross_val_score, StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "figures"; OUT.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "data" / "processed" / "opentitan_real_examples_medium.jsonl"
assert DATA.exists(), "Build the medium dataset first (extract_commits + build_dataset)."

INT = ["bug_fix", "feature_or_behavior_change", "refactor_cleanup", "configuration_timing"]
PAT = {"reset": r"\b(reset|rst)\b", "always_ff": r"\balways_ff\b", "always_comb": r"\balways_comb\b",
       "assign": r"\bassign\b", "parameter": r"\b(parameter|localparam|param)\b", "clock": r"\b(clk|clock)\b",
       "assertion": r"\b(assert|assume|cover)\b", "signal": r"\b(logic|wire|reg)\b",
       "casefsm": r"\b(case|state|fsm)\b", "ifelse": r"\b(if|else)\b", "module": r"\b(module|endmodule)\b",
       "comment": r"//", "todo": r"\b(todo|fixme)\b"}
NAMES = ["added", "removed", "net", "total", "add_remove_ratio"] + list(PAT.keys())


def feats(d):
    L = d.splitlines()
    a = sum(1 for l in L if l.startswith("+") and not l.startswith("+++"))
    r = sum(1 for l in L if l.startswith("-") and not l.startswith("---"))
    low = d.lower()
    return [a, r, a - r, a + r, a / (r + 1)] + [len(re.findall(p, low)) for p in PAT.values()]


rows = [json.loads(l) for l in open(DATA)]
X = np.array([feats(x["unified_diff"]) for x in rows], float)
y = np.array([INT.index(x["intent_label"]) for x in rows])
texts = [x["normalized_diff"] for x in rows]

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=13)
scorer = make_scorer(f1_score, average="macro", labels=range(4), zero_division=0)

rf = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=13)
s_rf = cross_val_score(rf, X, y, cv=cv, scoring=scorer)
tf = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=2000, class_weight="balanced"))
s_tf = cross_val_score(tf, texts, y, cv=cv, scoring=scorer)

print("=== 5-fold cross-validation (intent macro-F1) ===")
print(f"RTL feature model : {s_rf.mean():.3f} +/- {s_rf.std():.3f}   per-fold {np.round(s_rf,3).tolist()}")
print(f"TF-IDF baseline   : {s_tf.mean():.3f} +/- {s_tf.std():.3f}")

rf.fit(X, y)
imp = rf.feature_importances_
print("\n=== Top hardware features (importance) ===")
for i in np.argsort(imp)[::-1][:6]:
    print(f"  {NAMES[i]:<16} {imp[i]:.3f}")

print("\n=== Mean feature value per intent class ===")
key = ["added", "removed", "parameter", "comment"]
ki = [NAMES.index(k) for k in key]
print("class".ljust(26) + "".join(k.rjust(11) for k in key))
for c, name in enumerate(INT):
    m = X[y == c][:, ki].mean(axis=0)
    print(name.ljust(26) + "".join(f"{v:11.2f}" for v in m))

# figure: CV mean +/- std
fig, ax = plt.subplots(figsize=(6, 4.3))
labels = ["RTL features\n+ Random Forest", "TF-IDF\n(text)"]
means = [s_rf.mean(), s_tf.mean()]
stds = [s_rf.std(), s_tf.std()]
bars = ax.bar(labels, means, yerr=stds, capsize=8, color=["#2c7fb8", "#999999"])
for b, m in zip(bars, means):
    ax.text(b.get_x() + b.get_width()/2, m + 0.02, f"{m:.3f}", ha="center", fontweight="bold")
ax.set_ylabel("Intent macro-F1 (5-fold CV)")
ax.set_ylim(0, max(means) + max(stds) + 0.1)
ax.set_title("5-fold cross-validation: feature model vs text baseline")
fig.tight_layout(); fig.savefig(OUT / "rtl_features_cv.png", dpi=130)
print("\nSaved figure: outputs/figures/rtl_features_cv.png")
