from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.io import read_json, write_text
from src.utils.logging import configure_logging


def _csv_to_markdown(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return "_No results available yet._"
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return "_No rows available._"
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def _result_scope(main_results_path: Path, ablation_results_path: Path) -> str:
    text = ""
    for path in (main_results_path, ablation_results_path):
        if path.exists():
            text += path.read_text(encoding="utf-8")
    if "full_" in text:
        return "full"
    if "smoke_" in text:
        return "smoke"
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-stats", default=str(ROOT / "outputs" / "metrics" / "dataset_stats.json"))
    parser.add_argument("--main-results", default=str(ROOT / "outputs" / "metrics" / "main_results.csv"))
    parser.add_argument("--ablation-results", default=str(ROOT / "outputs" / "metrics" / "ablation_results.csv"))
    args = parser.parse_args()

    logger = configure_logging(ROOT / "outputs" / "logs" / "make_report_assets.log")
    dataset_stats = read_json(args.dataset_stats) if Path(args.dataset_stats).exists() else {}
    dataset_stats_json = json.dumps(dataset_stats, indent=2, ensure_ascii=False)
    main_results_path = Path(args.main_results)
    ablation_results_path = Path(args.ablation_results)
    main_results_md = _csv_to_markdown(main_results_path)
    ablation_results_md = _csv_to_markdown(ablation_results_path)
    result_scope = _result_scope(main_results_path, ablation_results_path)
    if result_scope == "full":
        result_scope_text = "These tables summarize the available full-run aggregates."
    elif result_scope == "smoke":
        result_scope_text = "These tables summarize the available smoke-run aggregates."
    else:
        result_scope_text = "These tables summarize the available aggregated outputs."

    assets_text = f"""# Final Report Assets

## Dataset Statistics

```json
{dataset_stats_json}
```

## Main Results

{main_results_md}

## Ablation Results

{ablation_results_md}

{result_scope_text}

## Figures

- `outputs/figures/dataset_label_distribution.png`
- `outputs/figures/diff_length_distribution.png`
- `outputs/figures/main_results_intent_macro_f1.png`
- `outputs/figures/main_results_hole_f1.png`
- model-specific confusion matrices in `outputs/figures/`
"""
    write_text(ROOT / "report" / "final_report_assets.md", assets_text)

    report_text = f"""# DiffIntent-RTL Final Report Draft

## 1. Motivation and Problem Definition

DiffIntent-RTL studies whether deep learning can classify the intent of SystemVerilog RTL changes and identify suspicious incomplete changes from OpenTitan commit diffs. The two tasks are multi-class intent prediction and binary implementation-hole detection.

## 2. Related Work

The project is motivated by prior work on code-change representation and patch modeling, including CC2Vec, PatchNet, DeepJIT, and CodeReviewer. The implementation adapts these ideas to hardware RTL diffs with a lightweight PyTorch pipeline suitable for a course project.

## 3. Data Description

The dataset is mined from the OpenTitan repository and filtered to modified `hw/**/rtl/*.sv` files while excluding generated, vendor, test, and DV paths. Weak labels are derived from commit-message patterns, and synthetic holes are generated from accepted changes through controlled mutations.

Current dataset statistics:

```json
{dataset_stats_json}
```

## 4. Models and Hyperparameters

- TF-IDF + logistic regression baseline
- Bag-of-tokens MLP
- Flat BiGRU with attention pooling
- Diff-aware hierarchical Transformer with line-type embeddings and multi-task heads

The codebase stores exact run configs in `outputs/checkpoints/*_config.yaml`.

## 5. Experiments

The repository supports smoke and full experiment modes. Smoke mode uses small mining limits and two training epochs per neural run. Full mode uses the planned larger preprocessing and training limits.

## 6. Results

### Main Results

{main_results_md}

### Ablation Results

{ablation_results_md}

{result_scope_text}

## 7. Analysis

The intended analysis compares the hierarchical diff-aware model against flat baselines and against the no-line-type ablation. Additional analysis should inspect class confusion, weak-label noise, mutation-type failure modes, and commit-message leakage from the message-only setting.

## 8. Limitations and Future Work

- Weak intent labels depend on commit-message heuristics.
- Synthetic holes approximate incompleteness but do not guarantee real bug semantics.
- Models currently operate on normalized diff structure rather than full semantic HDL graphs.
- Future work could add stronger manual validation, broader repositories, and semantics-aware RTL representations.

## 9. Team Contribution Placeholders

- Team member 1: [fill in]
- Team member 2: [fill in]

## 10. References

- lowRISC OpenTitan repository
- CC2Vec
- PatchNet
- DeepJIT
- CodeReviewer
"""
    write_text(ROOT / "report" / "final_report.md", report_text)
    logger.info("report assets updated")


if __name__ == "__main__":
    main()
