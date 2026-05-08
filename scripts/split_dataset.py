from __future__ import annotations

import argparse
from collections import Counter
from math import floor
from pathlib import Path
import sys

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.config import load_yaml_config
from src.utils.io import read_jsonl, write_json, write_jsonl
from src.utils.logging import configure_logging


def _group_examples(examples: list[dict]) -> list[list[dict]]:
    groups = {}
    for example in examples:
        groups.setdefault(example["pair_id"], []).append(example)
    return sorted(
        groups.values(),
        key=lambda group: group[0]["commit_date"],
    )


def _save_label_distribution_figure(examples: list[dict], output_path: Path) -> None:
    intent_counts = Counter(example["intent_label"] for example in examples)
    hole_counts = Counter(example["hole_label"] for example in examples)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(list(intent_counts.keys()), list(intent_counts.values()), color="#4C78A8")
    axes[0].set_title("Intent Labels")
    axes[0].tick_params(axis="x", rotation=30)
    axes[1].bar(list(hole_counts.keys()), list(hole_counts.values()), color="#F58518")
    axes[1].set_title("Hole Labels")
    axes[1].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def _save_diff_length_figure(examples: list[dict], output_path: Path) -> None:
    lengths = [int(example.get("diff_line_count", 0)) for example in examples]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(lengths, bins=min(20, max(len(lengths), 1)), color="#54A24B", edgecolor="black")
    ax.set_title("Normalized Diff Length Distribution")
    ax.set_xlabel("Typed lines per diff")
    ax.set_ylabel("Count")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    logger = configure_logging(ROOT / "outputs" / "logs" / "split_dataset.log")

    input_path = ROOT / config["paths"]["with_holes"]
    train_path = ROOT / config["paths"]["train_split"]
    val_path = ROOT / config["paths"]["val_split"]
    test_path = ROOT / config["paths"]["test_split"]
    stats_path = ROOT / config["paths"]["dataset_stats"]

    examples = read_jsonl(input_path)
    if not examples:
        raise RuntimeError(
            f"No examples found in {input_path}. "
            "Check the mining and filtering pipeline."
        )

    groups = _group_examples(examples)
    total_groups = len(groups)
    train_groups = floor(total_groups * config["split"]["train_ratio"])
    val_groups = floor(total_groups * config["split"]["val_ratio"])
    test_groups = total_groups - train_groups - val_groups

    train_group_list = groups[:train_groups]
    val_group_list = groups[train_groups : train_groups + val_groups]
    test_group_list = groups[train_groups + val_groups :]

    split_payloads = {
        "train": [example for group in train_group_list for example in group],
        "val": [example for group in val_group_list for example in group],
        "test": [example for group in test_group_list for example in group],
    }

    for split_name, payload in split_payloads.items():
        for example in payload:
            example["split"] = split_name

    write_jsonl(train_path, split_payloads["train"])
    write_jsonl(val_path, split_payloads["val"])
    write_jsonl(test_path, split_payloads["test"])

    stats = {
        "num_examples": len(examples),
        "num_groups": total_groups,
        "group_counts": {
            "train": len(train_group_list),
            "val": len(val_group_list),
            "test": len(test_group_list),
        },
        "example_counts": {
            split: len(payload) for split, payload in split_payloads.items()
        },
        "intent_distribution": dict(Counter(example["intent_label"] for example in examples)),
        "hole_distribution": dict(Counter(example["hole_label"] for example in examples)),
        "mutation_distribution": dict(
            Counter(example["mutation_type"] for example in examples)
        ),
        "avg_diff_line_count": (
            sum(int(example.get("diff_line_count", 0)) for example in examples) / len(examples)
        ),
    }
    write_json(stats_path, stats)

    _save_label_distribution_figure(
        examples,
        ROOT
        / config["paths"].get(
            "label_distribution_figure",
            "outputs/figures/dataset_label_distribution.png",
        ),
    )
    _save_diff_length_figure(
        examples,
        ROOT
        / config["paths"].get(
            "diff_length_distribution_figure",
            "outputs/figures/diff_length_distribution.png",
        ),
    )

    logger.info("input_path=%s", input_path)
    logger.info("train_path=%s", train_path)
    logger.info("val_path=%s", val_path)
    logger.info("test_path=%s", test_path)
    logger.info("stats=%s", stats)
    logger.info(
        "group_counts train=%s val=%s test=%s",
        len(train_group_list),
        len(val_group_list),
        test_groups,
    )


if __name__ == "__main__":
    main()
