"""Error analysis for intent classification: confusion matrix + per-class F1.

Reads saved test predictions and produces:
  - a confusion matrix figure per model
  - a per-class F1 comparison figure
  - a printed per-class report
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "outputs" / "predictions"
OUT = ROOT / "outputs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

INTENT_LABELS = ["bug_fix", "feature_or_behavior_change", "refactor_cleanup", "configuration_timing"]
SHORT = ["bug fix", "feature", "refactor", "config/timing"]

MODELS = {
    "TF-IDF + LR": "full_tfidf_lr_seed13_test_predictions.jsonl",
    "Hierarchical Transformer": "full_hierarchical_transformer_seed13_test_predictions.jsonl",
}


def load(path):
    rows = [json.loads(l) for l in open(path)]
    y_true = [r["true_intent"] for r in rows]
    y_pred = [r["pred_intent"] for r in rows]
    return np.array(y_true), np.array(y_pred)


def plot_confusion(y_true, y_pred, title, fname):
    cm = confusion_matrix(y_true, y_pred, labels=range(4))
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(4)); ax.set_yticks(range(4))
    ax.set_xticklabels(SHORT, rotation=30, ha="right"); ax.set_yticklabels(SHORT)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title(f"Intent confusion matrix — {title}")
    for i in range(4):
        for j in range(4):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout(); fig.savefig(OUT / fname, dpi=130); plt.close(fig)
    return cm


def per_class(y_true, y_pred):
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=range(4), zero_division=0)
    return f, s


results = {}
for name, fn in MODELS.items():
    yt, yp = load(PRED / fn)
    cm = plot_confusion(yt, yp, name, f"erroranalysis_confusion_{fn.split('_seed')[0]}.png")
    f, s = per_class(yt, yp)
    results[name] = (f, s)
    print(f"\n=== {name} ===")
    print(f"{'class':<26}{'F1':>8}{'support':>10}")
    for i, lbl in enumerate(INTENT_LABELS):
        print(f"{lbl:<26}{f[i]:>8.3f}{s[i]:>10}")
    print(f"{'macro-F1':<26}{f.mean():>8.3f}")

# per-class F1 comparison figure
fig, ax = plt.subplots(figsize=(7, 4.5))
x = np.arange(4); w = 0.38
for k, (name, (f, s)) in enumerate(results.items()):
    ax.bar(x + (k - 0.5) * w, f, w, label=name)
ax.set_xticks(x); ax.set_xticklabels(SHORT, rotation=20, ha="right")
ax.set_ylabel("F1 score"); ax.set_ylim(0, 1)
ax.set_title("Per-class intent F1: simple vs deep model")
ax.legend(); fig.tight_layout()
fig.savefig(OUT / "erroranalysis_perclass_f1.png", dpi=130); plt.close(fig)
print("\nSaved figures to outputs/figures/")
