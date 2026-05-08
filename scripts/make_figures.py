from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import statistics
import sys

import matplotlib.pyplot as plt

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


def _parse_run_name(run_name: str) -> tuple[str, int | None]:
    match = re.search(r"_seed(\d+)$", run_name)
    seed = int(match.group(1)) if match else None
    setting = re.sub(r"_seed\d+$", "", run_name)
    return setting, seed


def _filter_scope(rows: list[dict], scope: str) -> list[dict]:
    prefix = f"{scope}_"
    return [row for row in rows if row["setting_name"].startswith(prefix)]


def _aggregate(rows: list[dict]) -> list[dict]:
    grouped = {}
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
            }
        )
    return aggregated


def _write_csv(path: Path, rows: list[dict]) -> None:
    ensure_dir(path.parent)
    if not rows:
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write("")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _plot_bar(rows: list[dict], metric_key: str, title: str, output_path: Path) -> None:
    if not rows:
        return
    names = [row["setting_name"] for row in rows]
    values = [row[metric_key] for row in rows]
    fig, ax = plt.subplots(figsize=(max(8, len(rows) * 1.2), 4.5))
    ax.bar(names, values, color="#4C78A8")
    ax.set_ylabel(metric_key)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    ensure_dir(output_path.parent)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-dir", default=str(ROOT / "outputs" / "metrics"))
    parser.add_argument("--figures-dir", default=str(ROOT / "outputs" / "figures"))
    args = parser.parse_args()

    logger = configure_logging(ROOT / "outputs" / "logs" / "make_figures.log")
    metrics_dir = Path(args.metrics_dir)
    figures_dir = Path(args.figures_dir)

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
                "hole_accuracy": metrics["hole"]["accuracy"],
                "hole_f1": metrics["hole"]["f1"],
                "hole_auroc": metrics["hole"]["auroc"],
            }
        )

    aggregated = _aggregate(rows)
    main_rows_all = [
        row for row in aggregated if not any(keyword in row["setting_name"] for keyword in ABLATION_KEYWORDS)
    ]
    ablation_rows_all = [
        row for row in aggregated if any(keyword in row["setting_name"] for keyword in ABLATION_KEYWORDS)
    ]

    full_main_rows = _filter_scope(main_rows_all, "full")
    smoke_main_rows = _filter_scope(main_rows_all, "smoke")
    full_ablation_rows = _filter_scope(ablation_rows_all, "full")
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

    _plot_bar(
        main_rows,
        "intent_macro_f1_mean",
        "Main Results: Intent Macro-F1",
        figures_dir / "main_results_intent_macro_f1.png",
    )
    _plot_bar(
        main_rows,
        "hole_f1_mean",
        "Main Results: Hole F1",
        figures_dir / "main_results_hole_f1.png",
    )
    _plot_bar(
        ablation_rows,
        "intent_macro_f1_mean",
        "Ablations: Intent Macro-F1",
        figures_dir / "ablation_intent_macro_f1.png",
    )

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


if __name__ == "__main__":
    main()
