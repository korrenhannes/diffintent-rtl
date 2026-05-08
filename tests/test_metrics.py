from __future__ import annotations

from src.training.metrics import compute_hole_metrics, compute_intent_metrics


def test_metrics_handle_degenerate_cases() -> None:
    intent_metrics = compute_intent_metrics([0, 0, 0], [0, 0, 0])
    assert "macro_f1" in intent_metrics
    assert intent_metrics["confusion_matrix"][0][0] == 3

    hole_metrics = compute_hole_metrics([0, 0, 0], [0, 0, 0], [0.1, 0.2, 0.3])
    assert "f1" in hole_metrics
    assert hole_metrics["auroc"] is None

