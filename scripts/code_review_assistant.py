"""Code-review assistant for RTL diffs.

Trains two light TF-IDF + Logistic Regression models (intent + hole detection)
in a few seconds on CPU, then exposes a single `review(diff_text)` function that,
given a diff, returns:
  - the predicted change intent (bug fix / feature / refactor / config-timing)
  - a completeness warning if the change looks like it may be missing code

Run:
    python3 scripts/code_review_assistant.py
"""
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"

INTENT_LABELS = ["bug_fix", "feature_or_behavior_change", "refactor_cleanup", "configuration_timing"]
INTENT_NICE = {"bug_fix": "bug fix", "feature_or_behavior_change": "feature / behavior change",
               "refactor_cleanup": "refactor / cleanup", "configuration_timing": "configuration / timing"}


def _load(name_options):
    for n in name_options:
        p = PROC / n
        if p.exists():
            return [json.loads(l) for l in open(p)]
    raise FileNotFoundError("Run extract_commits + build_dataset first.")


# --- train intent model (on real labeled examples) ---
real = _load(["opentitan_real_examples_medium.jsonl", "opentitan_real_examples_smoke.jsonl"])
intent_model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)),
                             LogisticRegression(max_iter=2000, class_weight="balanced"))
intent_model.fit([r["normalized_diff"] for r in real], [r["intent_label"] for r in real])

# --- train hole model (on complete vs synthetic-hole examples) ---
holes = _load(["opentitan_with_holes_medium.jsonl", "opentitan_with_holes_smoke.jsonl"])
hole_model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)),
                           LogisticRegression(max_iter=2000, class_weight="balanced"))
hole_model.fit([r["normalized_diff"] for r in holes], [r["hole_label"] for r in holes])


def review(diff_text, normalized=None):
    """Return a short code-review opinion for a diff."""
    text = normalized or diff_text
    intent = intent_model.predict([text])[0]
    hole_prob = float(hole_model.predict_proba([text])[0][1])  # P(synthetic_hole)
    verdict = f"Predicted intent: {INTENT_NICE.get(intent, intent)}"
    if hole_prob >= 0.5:
        verdict += f"\n  \u26a0\ufe0f  This change looks possibly INCOMPLETE (hole score {hole_prob:.2f}) \u2014 reviewer should check."
    else:
        verdict += f"\n  \u2705 Looks complete (hole score {hole_prob:.2f})."
    return verdict


if __name__ == "__main__":
    print("=== Code-review assistant (demo) ===")
    # show both a few complete examples and a few synthetic-hole examples,
    # so the completeness warning is demonstrated in both directions
    complete = [r for r in holes if r.get("hole_label") == "complete"][:2]
    incomplete = [r for r in holes if r.get("hole_label") == "synthetic_hole"][:2]
    for tag, group in [("COMPLETE examples", complete), ("INCOMPLETE (synthetic-hole) examples", incomplete)]:
        print(f"\n========== {tag} ==========")
        for r in group:
            msg = r["commit_message"].splitlines()[0][:55]
            print(f"\n--- diff from commit: {msg} ---")
            print(review(r["unified_diff"], normalized=r["normalized_diff"]))
