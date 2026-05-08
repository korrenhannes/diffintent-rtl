from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.hole_generation import generate_synthetic_hole
from src.utils.config import load_yaml_config
from src.utils.io import read_jsonl, write_json, write_jsonl
from src.utils.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    logger = configure_logging(ROOT / "outputs" / "logs" / "generate_holes.log")

    real_path = ROOT / config["paths"]["real_examples"]
    output_path = ROOT / config["paths"]["with_holes"]
    stats_path = ROOT / "outputs" / "logs" / "generate_holes_stats.json"

    real_examples = read_jsonl(real_path)
    combined = []
    mutation_counts: Counter[str] = Counter()
    skipped = 0

    for example in real_examples:
        combined.append(example)
        synthetic = generate_synthetic_hole(example)
        if synthetic is None:
            skipped += 1
            continue
        combined.append(synthetic)
        mutation_counts[synthetic["mutation_type"]] += 1

    write_jsonl(output_path, combined)
    write_json(
        stats_path,
        {
            "real_examples": len(real_examples),
            "combined_examples": len(combined),
            "synthetic_examples": len(combined) - len(real_examples),
            "synthetic_skipped": skipped,
            "mutation_counts": dict(mutation_counts),
        },
    )

    logger.info("input_path=%s", real_path)
    logger.info("output_path=%s", output_path)
    logger.info("real_examples=%s", len(real_examples))
    logger.info("combined_examples=%s", len(combined))
    logger.info("synthetic_skipped=%s", skipped)
    logger.info("mutation_counts=%s", dict(mutation_counts))


if __name__ == "__main__":
    main()

