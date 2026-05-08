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
from src.training.runtime import build_dataloaders, build_model, build_vocab_for_examples
from src.training.trainer import Trainer, TrainerConfig
from src.utils.config import load_and_merge_configs, save_yaml_config
from src.utils.io import read_jsonl
from src.utils.logging import configure_logging
from src.utils.seed import resolve_device, seed_everything


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data-config", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--epochs-override", type=int, default=None)
    parser.add_argument("--task-mode-override", default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = load_and_merge_configs(args.data_config, args.config)

    if args.epochs_override is not None:
        config["training"]["epochs"] = args.epochs_override
    if args.task_mode_override is not None:
        config["training"]["task_mode"] = args.task_mode_override

    seed_everything(args.seed)
    log_path = ROOT / "outputs" / "logs" / f"{args.run_name}.log"
    logger = configure_logging(log_path)
    device = resolve_device(args.device)

    train_examples = read_jsonl(ROOT / config["paths"]["train_split"])
    val_examples = read_jsonl(ROOT / config["paths"]["val_split"])
    test_examples = read_jsonl(ROOT / config["paths"]["test_split"])
    if not train_examples or not val_examples or not test_examples:
        raise RuntimeError("One or more dataset splits are empty.")

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

    vocab = build_vocab_for_examples(
        examples=train_examples,
        representation=config["representation"],
        text_source=config["text_source"],
        max_lines_per_diff=dataset_config.max_lines_per_diff,
        keep_context_lines=dataset_config.keep_context_lines,
        min_frequency=config["vocab"]["min_frequency"],
        max_size=config["vocab"]["max_size"],
    )
    vocab_path = ROOT / "outputs" / "checkpoints" / f"{args.run_name}_vocab.json"
    vocab.save(vocab_path)

    train_loader, val_loader, test_loader = build_dataloaders(
        train_examples=train_examples,
        val_examples=val_examples,
        test_examples=test_examples,
        vocab=vocab,
        dataset_config=dataset_config,
        representation=config["representation"],
        batch_size=config["training"]["batch_size"],
    )

    model = build_model(
        model_type=config["model_type"],
        vocab=vocab,
        config=config,
        num_intent_classes=len(INTENT_LABELS),
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config["training"]["learning_rate"],
        weight_decay=config["training"]["weight_decay"],
    )

    save_yaml_config(
        {
            **config,
            "runtime": {
                "run_name": args.run_name,
                "seed": args.seed,
                "device": str(device),
                "vocab_path": str(vocab_path.relative_to(ROOT)),
            },
        },
        ROOT / "outputs" / "checkpoints" / f"{args.run_name}_config.yaml",
    )

    logger.info("run_name=%s", args.run_name)
    logger.info("seed=%s", args.seed)
    logger.info("device=%s", device)
    logger.info("train_examples=%s val_examples=%s test_examples=%s", len(train_examples), len(val_examples), len(test_examples))
    logger.info("keep_context_lines=%s", dataset_config.keep_context_lines)

    trainer = Trainer(
        model=model,
        device=device,
        optimizer=optimizer,
        config=TrainerConfig(
            epochs=config["training"]["epochs"],
            learning_rate=config["training"]["learning_rate"],
            weight_decay=config["training"]["weight_decay"],
            lambda_hole=config["training"]["lambda_hole"],
            task_mode=config["training"]["task_mode"],
            early_stopping_patience=config["training"]["early_stopping_patience"],
            run_name=args.run_name,
            checkpoint_dir=ROOT / "outputs" / "checkpoints",
            metrics_dir=ROOT / "outputs" / "metrics",
            predictions_dir=ROOT / "outputs" / "predictions",
            figures_dir=ROOT / "outputs" / "figures",
            log_history_path=ROOT / "outputs" / "logs" / f"{args.run_name}_history.json",
        ),
    )
    trainer.fit(train_loader, val_loader, test_loader)


if __name__ == "__main__":
    main()

