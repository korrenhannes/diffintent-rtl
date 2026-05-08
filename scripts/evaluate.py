from __future__ import annotations

import argparse
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import INTENT_LABELS
from src.data.dataset import DatasetConfig
from src.data.tokenizer import Vocabulary
from src.training.runtime import build_dataloaders, build_model
from src.training.trainer import Trainer, TrainerConfig
from src.utils.config import load_and_merge_configs
from src.utils.io import read_jsonl
from src.utils.logging import configure_logging
from src.utils.seed import resolve_device


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data-config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--vocab", required=True)
    parser.add_argument("--split-path", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    config = load_and_merge_configs(args.data_config, args.config)
    logger = configure_logging(ROOT / "outputs" / "logs" / f"{args.run_name}_eval.log")
    device = resolve_device(args.device)
    vocab = Vocabulary.load(args.vocab)
    examples = read_jsonl(args.split_path)
    if not examples:
        raise RuntimeError(f"No examples found in split path: {args.split_path}")

    keep_context_lines = config.get(
        "keep_context_override",
        config["preprocessing"]["keep_context_lines"],
    )
    dataset_config = DatasetConfig(
        max_lines_per_diff=config["preprocessing"]["max_lines_per_diff"],
        max_tokens_per_line=config["preprocessing"]["max_tokens_per_line"],
        max_total_tokens_flat=config["preprocessing"]["max_total_tokens_flat"],
        keep_context_lines=keep_context_lines,
        text_source=config["text_source"],
    )

    _, _, eval_loader = build_dataloaders(
        train_examples=examples,
        val_examples=examples,
        test_examples=examples,
        vocab=vocab,
        dataset_config=dataset_config,
        representation=config.get("representation", "flat"),
        batch_size=config.get("training", {}).get("batch_size", 8),
    )
    model = build_model(
        model_type=config["model_type"],
        vocab=vocab,
        config=config,
        num_intent_classes=len(INTENT_LABELS),
    ).to(device)
    checkpoint = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    trainer = Trainer(
        model=model,
        device=device,
        optimizer=optimizer,
        config=TrainerConfig(
            epochs=1,
            learning_rate=1e-4,
            weight_decay=0.0,
            lambda_hole=1.0,
            task_mode=config.get("training", {}).get("task_mode", "multitask"),
            early_stopping_patience=1,
            run_name=args.run_name,
            checkpoint_dir=ROOT / "outputs" / "checkpoints",
            metrics_dir=ROOT / "outputs" / "metrics",
            predictions_dir=ROOT / "outputs" / "predictions",
            figures_dir=ROOT / "outputs" / "figures",
            log_history_path=ROOT / "outputs" / "logs" / f"{args.run_name}_eval_history.json",
        ),
    )
    metrics, predictions = trainer.predict(eval_loader)
    logger.info("metrics=%s", metrics)
    logger.info("num_predictions=%s", len(predictions))


if __name__ == "__main__":
    main()

