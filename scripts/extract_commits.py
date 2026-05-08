from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.git_mining import extract_candidate_examples
from src.utils.config import load_yaml_config
from src.utils.io import write_json, write_jsonl
from src.utils.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    log_path = ROOT / "outputs" / "logs" / "extract_commits.log"
    logger = configure_logging(log_path)

    repo_path = ROOT / config["repo"]["local_path"]
    output_path = ROOT / config["paths"]["raw_candidates"]
    stats_path = ROOT / "outputs" / "logs" / "extract_commits_stats.json"

    logger.info("repo_path=%s", repo_path)
    logger.info("output_path=%s", output_path)

    examples, stats = extract_candidate_examples(
        repo_dir=repo_path,
        max_commits=config["mining"]["max_commits"],
        max_examples=config["mining"]["max_examples"],
        max_rtl_files_per_commit=config["mining"]["max_rtl_files_per_commit"],
        prefer_single_rtl_file=config["mining"]["prefer_single_rtl_file"],
        max_diff_lines=config["mining"]["max_diff_lines"],
        strict_rtl_only=config["mining"]["strict_rtl_only"],
    )
    write_jsonl(output_path, examples)
    write_json(stats_path, stats)

    logger.info("examples_kept=%s", len(examples))
    logger.info("stats=%s", stats)


if __name__ == "__main__":
    main()

