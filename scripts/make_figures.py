from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_curve, roc_curve

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.io import ensure_dir
from src.utils.logging import configure_logging


ABLATION_KEYWORDS = [
    "no_line_type",
    "no_multitask",
    "no_context",
    "message_only",
    "ablation",
]

SETTING_LABELS = {
    "full_tfidf_lr": "TF-IDF + LR",
    "full_mlp": "Bag-of-Tokens MLP",
    "full_bigru": "Flat BiGRU",
    "full_hierarchical_transformer": "Hierarchical Transformer",
    "full_hierarchical_no_line_type": "No Line-Type Embeddings",
    "full_hierarchical_no_context": "No Context Lines",
    "full_hierarchical_no_multitask_intent": "Intent-Only Training",
    "full_hierarchical_no_multitask_hole": "Hole-Only Training",
    "full_tfidf_message_only": "Message-Only TF-IDF",
    "smoke_tfidf_lr": "Smoke TF-IDF + LR",
    "smoke_mlp": "Smoke MLP",
    "smoke_bigru": "Smoke BiGRU",
    "smoke_hierarchical_transformer": "Smoke Hierarchical Transformer",
}

INTENT_LABELS = [
    "bug_fix",
    "feature_or_behavior_change",
    "refactor_cleanup",
    "configuration_timing",
]

INTENT_DISPLAY = {
    "bug_fix": "Bug Fix",
    "feature_or_behavior_change": "Feature / Behavior",
    "refactor_cleanup": "Refactor / Cleanup",
    "configuration_timing": "Config / Timing",
}

MUTATION_DISPLAY = {
    "drop_added_line": "Drop Added Line",
    "remove_added_guard_or_assertion": "Remove Guard / Assertion",
    "remove_reset_or_default_assignment": "Remove Reset / Default",
    "flip_binary_constant": "Flip Binary Constant",
    "flip_comparison_operator": "Flip Comparison",
    "flip_logical_operator": "Flip Logical Operator",
    "drop_hunk": "Drop Hunk",
    "none": "Complete",
}

MAIN_MODEL_ORDER = [
    "full_tfidf_lr",
    "full_mlp",
    "full_bigru",
    "full_hierarchical_transformer",
]

ABLATION_ORDER = [
    "full_hierarchical_no_line_type",
    "full_hierarchical_no_context",
    "full_hierarchical_no_multitask_intent",
    "full_hierarchical_no_multitask_hole",
    "full_tfidf_message_only",
]

DETAIL_SETTINGS = [
    "full_tfidf_lr",
    "full_hierarchical_transformer",
    "full_hierarchical_no_line_type",
    "full_hierarchical_no_context",
]


def _setup_style() -> None:
    plt.style.use("default")
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.titlesize": 14,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _parse_run_name(run_name: str) -> tuple[str, int | None]:
    match = re.search(r"_seed(\d+)$", run_name)
    seed = int(match.group(1)) if match else None
    setting = re.sub(r"_seed\d+$", "", run_name)
    return setting, seed


def _filter_scope(rows: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    prefix = f"{scope}_"
    return [row for row in rows if row["setting_name"].startswith(prefix)]


def _ordered(rows: list[dict[str, Any]], order: list[str]) -> list[dict[str, Any]]:
    rank = {name: index for index, name in enumerate(order)}
    return sorted(rows, key=lambda row: rank.get(row["setting_name"], len(rank)))


def _metric_field(metric_name: str) -> tuple[str, str | None]:
    mapping = {
        "intent_macro_f1": ("intent_macro_f1_mean", "intent_macro_f1_std"),
        "hole_f1": ("hole_f1_mean", "hole_f1_std"),
        "hole_auroc": ("hole_auroc_mean", "hole_auroc_std"),
    }
    return mapping[metric_name]


def _display_name(setting_name: str) -> str:
    return SETTING_LABELS.get(setting_name, setting_name)


def _aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["setting_name"], []).append(row)

    aggregated = []
    for setting_name, items in sorted(grouped.items()):
        intent_values = [item["intent_macro_f1"] for item in items]
        hole_values = [item["hole_f1"] for item in items]
        auroc_values = [item["hole_auroc"] for item in items if item["hole_auroc"] is not None]
        aggregated.append(
            {
                "setting_name": setting_name,
                "num_runs": len(items),
                "intent_accuracy_mean": statistics.mean(item["intent_accuracy"] for item in items),
                "intent_macro_f1_mean": statistics.mean(intent_values),
                "intent_macro_f1_std": statistics.pstdev(intent_values) if len(intent_values) > 1 else 0.0,
                "hole_accuracy_mean": statistics.mean(item["hole_accuracy"] for item in items),
                "hole_f1_mean": statistics.mean(hole_values),
                "hole_f1_std": statistics.pstdev(hole_values) if len(hole_values) > 1 else 0.0,
                "hole_auroc_mean": statistics.mean(auroc_values) if auroc_values else None,
                "hole_auroc_std": statistics.pstdev(auroc_values) if len(auroc_values) > 1 else 0.0,
            }
        )
    return aggregated


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _load_rows(metrics_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for metrics_path in sorted(metrics_dir.glob("*_test_metrics.json")):
        run_name = metrics_path.name[: -len("_test_metrics.json")]
        setting_name, seed = _parse_run_name(run_name)
        with metrics_path.open("r", encoding="utf-8") as handle:
            metrics = json.load(handle)
        rows.append(
            {
                "run_name": run_name,
                "setting_name": setting_name,
                "seed": seed,
                "intent_accuracy": metrics["intent"]["accuracy"],
                "intent_macro_f1": metrics["intent"]["macro_f1"],
                "intent_weighted_f1": metrics["intent"]["weighted_f1"],
                "intent_per_class": metrics["intent"]["per_class"],
                "intent_confusion_matrix": metrics["intent"]["confusion_matrix"],
                "intent_labels": metrics["intent"]["labels"],
                "hole_accuracy": metrics["hole"]["accuracy"],
                "hole_precision": metrics["hole"]["precision"],
                "hole_recall": metrics["hole"]["recall"],
                "hole_f1": metrics["hole"]["f1"],
                "hole_auroc": metrics["hole"]["auroc"],
                "hole_pr_auc": metrics["hole"]["pr_auc"],
                "hole_confusion_matrix": metrics["hole"]["confusion_matrix"],
                "hole_labels": metrics["hole"]["labels"],
            }
        )
    return rows


def _load_prediction_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return rows


def _load_test_metadata(path: Path) -> dict[str, dict[str, Any]]:
    metadata = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            metadata[payload["example_id"]] = payload
    return metadata


def _load_processed_examples(path: Path) -> list[dict[str, Any]]:
    examples = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            examples.append(json.loads(line))
    return examples


def _select_representative_run(rows: list[dict[str, Any]], setting_name: str) -> dict[str, Any]:
    candidates = [row for row in rows if row["setting_name"] == setting_name]
    if len(candidates) == 1:
        return candidates[0]

    mean_intent = statistics.mean(row["intent_macro_f1"] for row in candidates)
    mean_hole = statistics.mean(row["hole_f1"] for row in candidates)
    auroc_values = [row["hole_auroc"] for row in candidates if row["hole_auroc"] is not None]
    mean_auroc = statistics.mean(auroc_values) if auroc_values else None

    def distance(row: dict[str, Any]) -> float:
        score = abs(row["intent_macro_f1"] - mean_intent) + abs(row["hole_f1"] - mean_hole)
        if mean_auroc is not None and row["hole_auroc"] is not None:
            score += abs(row["hole_auroc"] - mean_auroc)
        return score

    return min(candidates, key=distance)


def _save(fig: plt.Figure, *paths: Path) -> None:
    for path in paths:
        ensure_dir(path.parent)
        fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_dataset_overview(
    dataset_stats: dict[str, Any],
    test_metadata: dict[str, dict[str, Any]],
    output_path: Path,
) -> None:
    intent_distribution = dataset_stats["intent_distribution"]
    hole_distribution = dataset_stats["hole_distribution"]
    mutation_distribution = {
        key: value
        for key, value in dataset_stats["mutation_distribution"].items()
        if key != "none"
    }

    test_mutation_counts: Counter[str] = Counter()
    for item in test_metadata.values():
        if item["hole_label"] == "synthetic_hole":
            test_mutation_counts[item["mutation_type"]] += 1

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    intent_items = list(intent_distribution.items())
    axes[0, 0].bar(
        [INTENT_DISPLAY.get(name, name) for name, _ in intent_items],
        [count for _, count in intent_items],
        color="#4C78A8",
    )
    axes[0, 0].set_title("Intent Label Distribution")
    axes[0, 0].tick_params(axis="x", rotation=20)
    axes[0, 0].set_ylabel("Count")

    hole_items = list(hole_distribution.items())
    axes[0, 1].bar(
        [MUTATION_DISPLAY.get(name, name) for name, _ in hole_items],
        [count for _, count in hole_items],
        color=["#59A14F", "#E15759"],
    )
    axes[0, 1].set_title("Hole Label Distribution")
    axes[0, 1].set_ylabel("Count")

    mutation_items = sorted(mutation_distribution.items(), key=lambda item: item[1], reverse=True)
    axes[1, 0].bar(
        [MUTATION_DISPLAY.get(name, name) for name, _ in mutation_items],
        [count for _, count in mutation_items],
        color="#F28E2B",
    )
    axes[1, 0].set_title("Synthetic Mutation Distribution (Full Dataset)")
    axes[1, 0].tick_params(axis="x", rotation=35)
    axes[1, 0].set_ylabel("Count")

    test_items = sorted(test_mutation_counts.items(), key=lambda item: item[1], reverse=True)
    axes[1, 1].bar(
        [MUTATION_DISPLAY.get(name, name) for name, _ in test_items],
        [count for _, count in test_items],
        color="#B07AA1",
    )
    axes[1, 1].set_title("Synthetic Mutation Distribution (Test Split)")
    axes[1, 1].tick_params(axis="x", rotation=35)
    axes[1, 1].set_ylabel("Count")

    fig.suptitle("Dataset Overview", y=1.02)
    _save(fig, output_path)


def _plot_diff_length_distribution(
    processed_examples: list[dict[str, Any]],
    output_path: Path,
) -> None:
    complete_lengths = [
        example["diff_line_count"]
        for example in processed_examples
        if example["hole_label"] == "complete"
    ]
    synthetic_lengths = [
        example["diff_line_count"]
        for example in processed_examples
        if example["hole_label"] == "synthetic_hole"
    ]

    max_value = max(complete_lengths + synthetic_lengths)
    bins = np.linspace(0, max_value, 30)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.hist(
        complete_lengths,
        bins=bins,
        alpha=0.65,
        label="Complete",
        color="#4C78A8",
        density=True,
    )
    ax.hist(
        synthetic_lengths,
        bins=bins,
        alpha=0.6,
        label="Synthetic Hole",
        color="#E15759",
        density=True,
    )
    ax.set_xlabel("Diff Line Count")
    ax.set_ylabel("Density")
    ax.set_title("Diff Length Distribution")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(frameon=False)
    _save(fig, output_path)


def _plot_grouped_horizontal_bars(
    rows: list[dict[str, Any]],
    metric_names: list[str],
    title: str,
    output_path: Path,
    baseline_row: dict[str, Any] | None = None,
) -> None:
    if not rows:
        return

    ordered_rows = rows
    fig, axes = plt.subplots(1, len(metric_names), figsize=(5.8 * len(metric_names), 5.4), sharey=True)
    if len(metric_names) == 1:
        axes = [axes]

    labels = [_display_name(row["setting_name"]) for row in ordered_rows]
    positions = np.arange(len(ordered_rows))

    for ax, metric_name in zip(axes, metric_names):
        mean_field, std_field = _metric_field(metric_name)
        values = [row[mean_field] if row[mean_field] is not None else np.nan for row in ordered_rows]
        errors = [row[std_field] if std_field and row[std_field] is not None else 0.0 for row in ordered_rows]
        bars = ax.barh(positions, values, xerr=errors, color="#4C78A8", alpha=0.9)
        ax.set_title(metric_name.replace("_", " ").title())
        ax.set_yticks(positions)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlim(0.0, max(1.0, np.nanmax(values) + 0.1))
        ax.grid(axis="x", linestyle="--", alpha=0.35)
        if baseline_row is not None:
            baseline_value = baseline_row[mean_field]
            ax.axvline(baseline_value, linestyle="--", color="#E15759", linewidth=1.5)
        for bar, value in zip(bars, values):
            ax.text(value + 0.01, bar.get_y() + bar.get_height() / 2, f"{value:.3f}", va="center")

    fig.suptitle(title, y=1.02)
    _save(fig, output_path)


def _normalize_confusion(matrix: list[list[int]]) -> np.ndarray:
    array = np.asarray(matrix, dtype=float)
    row_sums = array.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return array / row_sums


def _plot_confusion_panel(
    panel_rows: list[dict[str, Any]],
    matrix_key: str,
    labels_key: str,
    title: str,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, len(panel_rows), figsize=(5.5 * len(panel_rows), 4.8))
    if len(panel_rows) == 1:
        axes = [axes]

    for ax, row in zip(axes, panel_rows):
        matrix = _normalize_confusion(row[matrix_key])
        image = ax.imshow(matrix, cmap="Blues", vmin=0.0, vmax=1.0)
        labels = row[labels_key]
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_yticklabels(labels)
        ax.set_title(_display_name(row["setting_name"]))
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="black")

    fig.colorbar(image, ax=axes, fraction=0.025, pad=0.04)
    fig.suptitle(title, y=1.03)
    _save(fig, output_path)


def _plot_per_class_intent_f1(
    rows: list[dict[str, Any]],
    setting_names: list[str],
    output_path: Path,
) -> None:
    selected_rows = [_select_representative_run(rows, name) for name in setting_names]
    x = np.arange(len(INTENT_LABELS))
    width = 0.24

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    for index, row in enumerate(selected_rows):
        values = [row["intent_per_class"][label]["f1"] for label in INTENT_LABELS]
        ax.bar(
            x + (index - (len(selected_rows) - 1) / 2) * width,
            values,
            width=width,
            label=_display_name(row["setting_name"]),
        )

    ax.set_xticks(x)
    ax.set_xticklabels([INTENT_DISPLAY[label] for label in INTENT_LABELS], rotation=15)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("F1")
    ax.set_title("Per-Class Intent F1 (Representative Full Runs)")
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    _save(fig, output_path)


def _plot_hole_curves(
    predictions_dir: Path,
    rows: list[dict[str, Any]],
    output_path: Path,
    curve_type: str,
) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.8))

    for setting_name in MAIN_MODEL_ORDER:
        row = _select_representative_run(rows, setting_name)
        predictions = _load_prediction_rows(
            predictions_dir / f"{row['run_name']}_test_predictions.jsonl"
        )
        y_true = np.array([item["true_hole"] for item in predictions])
        y_score = np.array([item["hole_probs"][1] for item in predictions])

        if curve_type == "roc":
            x_values, y_values, _ = roc_curve(y_true, y_score)
            label = f"{_display_name(setting_name)} (AUROC={row['hole_auroc']:.3f})"
            ax.plot(x_values, y_values, linewidth=2.0, label=label)
        else:
            precision, recall, _ = precision_recall_curve(y_true, y_score)
            label = f"{_display_name(setting_name)} (PR-AUC={row['hole_pr_auc']:.3f})"
            ax.plot(recall, precision, linewidth=2.0, label=label)

    if curve_type == "roc":
        ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1.0)
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title("Hole Detection ROC Curves")
    else:
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.set_title("Hole Detection Precision-Recall Curves")

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.grid(linestyle="--", alpha=0.35)
    ax.legend(frameon=False, loc="lower left")
    _save(fig, output_path)


def _mutation_recall_by_run(
    predictions: list[dict[str, Any]],
    test_metadata: dict[str, dict[str, Any]],
) -> dict[str, float]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for prediction in predictions:
        meta = test_metadata[prediction["example_id"]]
        if meta["hole_label"] != "synthetic_hole":
            continue
        grouped[meta["mutation_type"]].append(int(prediction["pred_hole"] == 1))
    return {
        mutation_type: float(sum(values) / len(values))
        for mutation_type, values in grouped.items()
    }


def _plot_mutation_recall(
    predictions_dir: Path,
    rows: list[dict[str, Any]],
    test_metadata: dict[str, dict[str, Any]],
    output_path: Path,
) -> None:
    selected_settings = [
        "full_tfidf_lr",
        "full_hierarchical_transformer",
        "full_hierarchical_no_line_type",
        "full_hierarchical_no_context",
    ]
    selected_rows = [_select_representative_run(rows, name) for name in selected_settings]

    support = Counter()
    for item in test_metadata.values():
        if item["hole_label"] == "synthetic_hole":
            support[item["mutation_type"]] += 1
    mutation_order = [
        mutation
        for mutation, count in support.most_common()
        if count > 0
    ]

    x = np.arange(len(mutation_order))
    width = 0.18
    fig, ax = plt.subplots(figsize=(12, 5.8))

    for index, row in enumerate(selected_rows):
        predictions = _load_prediction_rows(
            predictions_dir / f"{row['run_name']}_test_predictions.jsonl"
        )
        recall_by_mutation = _mutation_recall_by_run(predictions, test_metadata)
        values = [recall_by_mutation.get(mutation, 0.0) for mutation in mutation_order]
        ax.bar(
            x + (index - (len(selected_rows) - 1) / 2) * width,
            values,
            width=width,
            label=_display_name(row["setting_name"]),
        )

    labels = [
        f"{MUTATION_DISPLAY.get(mutation, mutation)}\n(n={support[mutation]})"
        for mutation in mutation_order
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Recall on Synthetic Holes")
    ax.set_title("Hole Recall by Mutation Type")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(frameon=False)
    _save(fig, output_path)


def _pairwise_ordering_stats(predictions: list[dict[str, Any]]) -> tuple[float, float]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prediction in predictions:
        grouped[prediction["pair_id"]].append(prediction)

    total_pairs = 0
    ordered_pairs = 0
    margins: list[float] = []
    for items in grouped.values():
        real_items = [item for item in items if item["true_hole"] == 0]
        synthetic_items = [item for item in items if item["true_hole"] == 1]
        if len(real_items) != 1 or len(synthetic_items) != 1:
            continue
        total_pairs += 1
        real_score = real_items[0]["hole_probs"][1]
        synthetic_score = synthetic_items[0]["hole_probs"][1]
        if synthetic_score > real_score:
            ordered_pairs += 1
        margins.append(synthetic_score - real_score)

    accuracy = ordered_pairs / total_pairs if total_pairs else 0.0
    average_margin = statistics.mean(margins) if margins else 0.0
    return accuracy, average_margin


def _plot_pairwise_ordering(
    predictions_dir: Path,
    rows: list[dict[str, Any]],
    output_path: Path,
) -> None:
    selected_rows = [_select_representative_run(rows, name) for name in DETAIL_SETTINGS]
    labels = [_display_name(row["setting_name"]) for row in selected_rows]
    accuracies = []
    margins = []

    for row in selected_rows:
        predictions = _load_prediction_rows(
            predictions_dir / f"{row['run_name']}_test_predictions.jsonl"
        )
        accuracy, margin = _pairwise_ordering_stats(predictions)
        accuracies.append(accuracy)
        margins.append(margin)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    axes[0].bar(labels, accuracies, color="#4C78A8")
    axes[0].set_ylim(0.0, 1.0)
    axes[0].set_ylabel("Pairwise Ordering Accuracy")
    axes[0].set_title("Synthetic Pair Ranking")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].grid(axis="y", linestyle="--", alpha=0.35)
    for label, value in zip(labels, accuracies):
        axes[0].text(label, value + 0.02, f"{value:.3f}", ha="center")

    axes[1].bar(labels, margins, color="#F28E2B")
    axes[1].axhline(0.0, color="black", linewidth=1.0)
    axes[1].set_ylabel("Average Synthetic - Real Hole Score")
    axes[1].set_title("Pairwise Hole-Score Margin")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(axis="y", linestyle="--", alpha=0.35)
    for label, value in zip(labels, margins):
        axes[1].text(label, value + 0.01, f"{value:.3f}", ha="center")

    _save(fig, output_path)


def _write_figure_index(path: Path, entries: list[tuple[str, str]]) -> None:
    lines = ["# Figure Index", ""]
    for filename, description in entries:
        lines.append(f"- `{filename}`: {description}")
    ensure_dir(path.parent)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-dir", default=str(ROOT / "outputs" / "metrics"))
    parser.add_argument("--figures-dir", default=str(ROOT / "outputs" / "figures"))
    parser.add_argument("--predictions-dir", default=str(ROOT / "outputs" / "predictions"))
    parser.add_argument("--report-figures-dir", default=str(ROOT / "report" / "figures"))
    parser.add_argument("--dataset-stats", default=str(ROOT / "outputs" / "metrics" / "dataset_stats.json"))
    parser.add_argument("--test-split", default=str(ROOT / "data" / "splits" / "test.jsonl"))
    parser.add_argument("--processed-dataset", default=str(ROOT / "data" / "processed" / "opentitan_with_holes.jsonl"))
    args = parser.parse_args()

    _setup_style()

    logger = configure_logging(ROOT / "outputs" / "logs" / "make_figures.log")
    metrics_dir = Path(args.metrics_dir)
    figures_dir = Path(args.figures_dir)
    predictions_dir = Path(args.predictions_dir)
    report_figures_dir = Path(args.report_figures_dir)
    dataset_stats = json.loads(Path(args.dataset_stats).read_text(encoding="utf-8"))
    test_metadata = _load_test_metadata(Path(args.test_split))
    processed_examples = _load_processed_examples(Path(args.processed_dataset))

    rows = _load_rows(metrics_dir)
    aggregated = _aggregate(rows)
    main_rows_all = [
        row for row in aggregated if not any(keyword in row["setting_name"] for keyword in ABLATION_KEYWORDS)
    ]
    ablation_rows_all = [
        row for row in aggregated if any(keyword in row["setting_name"] for keyword in ABLATION_KEYWORDS)
    ]

    full_main_rows = _ordered(_filter_scope(main_rows_all, "full"), MAIN_MODEL_ORDER)
    smoke_main_rows = _filter_scope(main_rows_all, "smoke")
    full_ablation_rows = _ordered(_filter_scope(ablation_rows_all, "full"), ABLATION_ORDER)
    smoke_ablation_rows = _filter_scope(ablation_rows_all, "smoke")

    main_rows = full_main_rows or main_rows_all
    ablation_rows = full_ablation_rows or ablation_rows_all

    _write_csv(metrics_dir / "all_test_results.csv", rows)
    _write_csv(metrics_dir / "main_results.csv", main_rows)
    _write_csv(metrics_dir / "ablation_results.csv", ablation_rows)
    _write_csv(metrics_dir / "full_main_results.csv", full_main_rows)
    _write_csv(metrics_dir / "full_ablation_results.csv", full_ablation_rows)
    _write_csv(metrics_dir / "smoke_main_results.csv", smoke_main_rows)
    _write_csv(metrics_dir / "smoke_ablation_results.csv", smoke_ablation_rows)

    figure_index: list[tuple[str, str]] = []

    dataset_figure = report_figures_dir / "figure_dataset_overview.png"
    _plot_dataset_overview(dataset_stats, test_metadata, dataset_figure)
    figure_index.append((dataset_figure.name, "Intent labels, hole labels, overall synthetic mutation counts, and test-set mutation counts."))

    diff_length_figure = report_figures_dir / "figure_diff_length_distribution.png"
    _plot_diff_length_distribution(processed_examples, diff_length_figure)
    figure_index.append((diff_length_figure.name, "Distribution of diff lengths in the processed full dataset, separated by complete and synthetic-hole examples."))

    main_results_figure = report_figures_dir / "figure_main_results.png"
    _plot_grouped_horizontal_bars(
        rows=full_main_rows,
        metric_names=["intent_macro_f1", "hole_f1", "hole_auroc"],
        title="Main Results on the Full Experiment",
        output_path=main_results_figure,
    )
    figure_index.append((main_results_figure.name, "Three-panel comparison of intent macro-F1, hole F1, and hole AUROC for the four main full models."))

    hierarchical_baseline = next(
        row for row in full_main_rows if row["setting_name"] == "full_hierarchical_transformer"
    )
    ablation_results_figure = report_figures_dir / "figure_ablation_results.png"
    _plot_grouped_horizontal_bars(
        rows=full_ablation_rows,
        metric_names=["intent_macro_f1", "hole_f1", "hole_auroc"],
        title="Ablation Results on the Full Experiment",
        output_path=ablation_results_figure,
        baseline_row=hierarchical_baseline,
    )
    figure_index.append((ablation_results_figure.name, "Ablation results with dashed baseline from the full hierarchical Transformer."))

    per_class_figure = report_figures_dir / "figure_intent_per_class_f1.png"
    _plot_per_class_intent_f1(
        rows=rows,
        setting_names=[
            "full_tfidf_lr",
            "full_hierarchical_transformer",
            "full_hierarchical_no_line_type",
        ],
        output_path=per_class_figure,
    )
    figure_index.append((per_class_figure.name, "Per-class intent F1 for the best intent baseline, the proposed model, and the no-line-type ablation."))

    roc_figure = report_figures_dir / "figure_hole_roc_curves.png"
    _plot_hole_curves(predictions_dir, rows, roc_figure, curve_type="roc")
    figure_index.append((roc_figure.name, "ROC curves for hole detection using representative full runs of the four main models."))

    pr_figure = report_figures_dir / "figure_hole_pr_curves.png"
    _plot_hole_curves(predictions_dir, rows, pr_figure, curve_type="pr")
    figure_index.append((pr_figure.name, "Precision-recall curves for hole detection using representative full runs of the four main models."))

    mutation_figure = report_figures_dir / "figure_hole_mutation_recall.png"
    _plot_mutation_recall(predictions_dir, rows, test_metadata, mutation_figure)
    figure_index.append((mutation_figure.name, "Hole recall by synthetic mutation type for representative full runs."))

    pairwise_figure = report_figures_dir / "figure_pairwise_hole_ranking.png"
    _plot_pairwise_ordering(predictions_dir, rows, pairwise_figure)
    figure_index.append((pairwise_figure.name, "Pairwise ranking accuracy and average hole-score margin between each synthetic mutation and its paired complete example."))

    representative_intent_rows = [
        _select_representative_run(rows, "full_tfidf_lr"),
        _select_representative_run(rows, "full_hierarchical_transformer"),
    ]
    intent_confusion_figure = report_figures_dir / "figure_intent_confusion_panels.png"
    _plot_confusion_panel(
        representative_intent_rows,
        matrix_key="intent_confusion_matrix",
        labels_key="intent_labels",
        title="Intent Confusion Matrices (Row-Normalized)",
        output_path=intent_confusion_figure,
    )
    figure_index.append((intent_confusion_figure.name, "Row-normalized intent confusion matrices for the best intent baseline and the proposed model."))

    representative_hole_rows = [
        _select_representative_run(rows, "full_tfidf_lr"),
        _select_representative_run(rows, "full_hierarchical_transformer"),
        _select_representative_run(rows, "full_hierarchical_no_line_type"),
    ]
    hole_confusion_figure = report_figures_dir / "figure_hole_confusion_panels.png"
    _plot_confusion_panel(
        representative_hole_rows,
        matrix_key="hole_confusion_matrix",
        labels_key="hole_labels",
        title="Hole Confusion Matrices (Row-Normalized)",
        output_path=hole_confusion_figure,
    )
    figure_index.append((hole_confusion_figure.name, "Row-normalized hole confusion matrices for TF-IDF, the proposed model, and the no-line-type ablation."))

    # Keep legacy output figures used elsewhere in the repo.
    _plot_grouped_horizontal_bars(
        rows=full_main_rows,
        metric_names=["intent_macro_f1"],
        title="Main Results: Intent Macro-F1",
        output_path=figures_dir / "main_results_intent_macro_f1.png",
    )
    _plot_grouped_horizontal_bars(
        rows=full_main_rows,
        metric_names=["hole_f1"],
        title="Main Results: Hole F1",
        output_path=figures_dir / "main_results_hole_f1.png",
    )
    _plot_grouped_horizontal_bars(
        rows=full_ablation_rows,
        metric_names=["intent_macro_f1"],
        title="Ablations: Intent Macro-F1",
        output_path=figures_dir / "ablation_intent_macro_f1.png",
    )

    _write_figure_index(report_figures_dir / "FIGURE_INDEX.md", figure_index)

    logger.info("test_metric_files=%s", len(rows))
    logger.info(
        "main_rows=%s ablation_rows=%s full_main_rows=%s full_ablation_rows=%s smoke_main_rows=%s smoke_ablation_rows=%s",
        len(main_rows),
        len(ablation_rows),
        len(full_main_rows),
        len(full_ablation_rows),
        len(smoke_main_rows),
        len(smoke_ablation_rows),
    )
    logger.info("report_figures=%s", len(figure_index))


if __name__ == "__main__":
    main()
