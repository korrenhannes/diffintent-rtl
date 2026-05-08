from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
)

from src.data import HOLE_LABELS, INTENT_LABELS
from src.utils.io import ensure_dir


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if np.isnan(numeric) or np.isinf(numeric):
        return None
    return numeric


def compute_intent_metrics(
    y_true: list[int],
    y_pred: list[int],
    label_names: list[str] | None = None,
) -> dict[str, Any]:
    """Compute robust multiclass intent metrics."""

    labels = list(range(len(label_names or INTENT_LABELS)))
    names = label_names or INTENT_LABELS
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )
    confusion = confusion_matrix(y_true, y_pred, labels=labels)

    per_class = {}
    for index, name in enumerate(names):
        per_class[name] = {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }

    _, _, macro_f1_values, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    _, _, weighted_f1_values, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(macro_f1_values),
        "weighted_f1": float(weighted_f1_values),
        "per_class": per_class,
        "confusion_matrix": confusion.tolist(),
        "labels": names,
    }


def compute_hole_metrics(
    y_true: list[int],
    y_pred: list[int],
    y_prob: list[float],
) -> dict[str, Any]:
    """Compute robust binary metrics for hole detection."""

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=[0, 1],
        average="binary",
        zero_division=0,
    )
    confusion = confusion_matrix(y_true, y_pred, labels=[0, 1])

    try:
        auroc = _safe_float(roc_auc_score(y_true, y_prob))
    except ValueError:
        auroc = None

    try:
        pr_precision, pr_recall, _ = precision_recall_curve(y_true, y_prob)
        pr_auc = _safe_float(auc(pr_recall, pr_precision))
    except ValueError:
        pr_auc = None

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "auroc": auroc,
        "pr_auc": pr_auc,
        "support": {
            HOLE_LABELS[0]: int(confusion[0].sum()),
            HOLE_LABELS[1]: int(confusion[1].sum()),
        },
        "confusion_matrix": confusion.tolist(),
        "labels": HOLE_LABELS,
    }


def plot_confusion_matrix(
    matrix: list[list[int]] | np.ndarray,
    labels: list[str],
    path: Path | str,
    title: str,
) -> None:
    """Save a confusion-matrix figure."""

    ensure_dir(Path(path).parent)
    array = np.asarray(matrix)
    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(array, cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)

    for row in range(array.shape[0]):
        for col in range(array.shape[1]):
            ax.text(col, row, str(array[row, col]), ha="center", va="center")

    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)

