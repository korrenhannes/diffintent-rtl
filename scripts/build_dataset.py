from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.diff_parser import normalize_diff
from src.data.labeling import label_raw_examples
from src.utils.config import load_yaml_config
from src.utils.io import read_jsonl, write_json, write_jsonl
from src.utils.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    logger = configure_logging(ROOT / "outputs" / "logs" / "build_dataset.log")

    raw_path = ROOT / config["paths"]["raw_candidates"]
    real_path = ROOT / config["paths"]["real_examples"]
    discarded_path = ROOT / config["paths"]["discarded_examples"]
    stats_path = ROOT / "outputs" / "logs" / "build_dataset_stats.json"

    raw_examples = read_jsonl(raw_path)
    kept, discarded, discard_reason_counts = label_raw_examples(raw_examples)

    processed = []
    processing_counts: Counter[str] = Counter()
    for record in kept:
        typed_lines, normalized_diff = normalize_diff(
            unified_diff=record["unified_diff"],
            file_path=record["file_path"],
            max_lines_per_diff=config["preprocessing"]["max_lines_per_diff"],
            keep_context_lines=True,
        )
        if not any(line["type"] in {"ADD", "DEL"} for line in typed_lines):
            processing_counts["skip_no_changed_lines_after_normalization"] += 1
            continue

        pair_id = f"{record['commit_hash']}::{record['file_path']}"
        processed.append(
            {
                **record,
                "typed_lines": typed_lines,
                "normalized_diff": normalized_diff,
                "hole_label": "complete",
                "is_synthetic": False,
                "mutation_type": "none",
                "origin_commit_hash": record["commit_hash"],
                "origin_file_path": record["file_path"],
                "pair_id": pair_id,
                "example_id": f"{pair_id}::real",
                "diff_line_count": len(typed_lines),
            }
        )
        processing_counts["examples_kept"] += 1

    write_jsonl(real_path, processed)
    write_jsonl(discarded_path, discarded)
    write_json(
        stats_path,
        {
            "raw_examples": len(raw_examples),
            "labeled_examples": len(kept),
            "discarded_examples": len(discarded),
            "discard_reason_counts": discard_reason_counts,
            "processing_counts": dict(processing_counts),
        },
    )

    logger.info("input_path=%s", raw_path)
    logger.info("real_examples_path=%s", real_path)
    logger.info("discarded_examples_path=%s", discarded_path)
    logger.info("examples_processed=%s", len(processed))
    logger.info("discard_reason_counts=%s", discard_reason_counts)
    logger.info("processing_counts=%s", dict(processing_counts))


if __name__ == "__main__":
    main()

