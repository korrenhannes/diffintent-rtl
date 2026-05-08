from __future__ import annotations

import os
import platform
from functools import partial
from typing import Any, Iterable

from torch.utils.data import DataLoader

from src.data.collate import collate_flat, collate_hierarchical
from src.data.dataset import DatasetConfig, DiffIntentDataset
from src.data.diff_parser import truncate_typed_lines
from src.data.tokenizer import (
    Vocabulary,
    build_vocabulary,
    tokenize_message,
    typed_lines_to_flat_tokens,
    typed_lines_to_line_tokens,
)
from src.models.bigru import FlatBiGRU
from src.models.hierarchical_transformer import HierarchicalDiffTransformer
from src.models.mlp import BagOfTokensMLP


def _prepare_typed_lines(
    example: dict[str, Any],
    max_lines_per_diff: int,
    keep_context_lines: bool,
) -> list[dict[str, Any]]:
    return truncate_typed_lines(
        typed_lines=example["typed_lines"],
        max_lines=max_lines_per_diff,
        keep_context_lines=keep_context_lines,
    )


def training_token_sequences(
    examples: list[dict[str, Any]],
    representation: str,
    text_source: str,
    max_lines_per_diff: int,
    keep_context_lines: bool,
) -> Iterable[list[str]]:
    """Yield token sequences for vocabulary construction."""

    for example in examples:
        if text_source == "message":
            yield tokenize_message(example["commit_message"])
            continue

        typed_lines = _prepare_typed_lines(
            example=example,
            max_lines_per_diff=max_lines_per_diff,
            keep_context_lines=keep_context_lines,
        )
        if representation == "flat":
            yield typed_lines_to_flat_tokens(typed_lines)
        else:
            for line_tokens in typed_lines_to_line_tokens(typed_lines):
                yield line_tokens


def build_vocab_for_examples(
    examples: list[dict[str, Any]],
    representation: str,
    text_source: str,
    max_lines_per_diff: int,
    keep_context_lines: bool,
    min_frequency: int = 1,
    max_size: int | None = None,
) -> Vocabulary:
    """Build a training vocabulary from the train split only."""

    sequences = training_token_sequences(
        examples=examples,
        representation=representation,
        text_source=text_source,
        max_lines_per_diff=max_lines_per_diff,
        keep_context_lines=keep_context_lines,
    )
    return build_vocabulary(
        token_sequences=sequences,
        min_frequency=min_frequency,
        max_size=max_size,
    )


def build_dataloaders(
    train_examples: list[dict[str, Any]],
    val_examples: list[dict[str, Any]],
    test_examples: list[dict[str, Any]],
    vocab: Vocabulary,
    dataset_config: DatasetConfig,
    representation: str,
    batch_size: int,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Construct train/val/test dataloaders."""

    dataset_kwargs = {
        "vocab": vocab,
        "config": dataset_config,
        "representation": representation,
    }
    train_dataset = DiffIntentDataset(train_examples, **dataset_kwargs)
    val_dataset = DiffIntentDataset(val_examples, **dataset_kwargs)
    test_dataset = DiffIntentDataset(test_examples, **dataset_kwargs)

    if representation == "flat" or dataset_config.text_source == "message":
        collate_fn = partial(collate_flat, pad_id=vocab.pad_id)
    else:
        collate_fn = partial(collate_hierarchical, pad_id=vocab.pad_id)

    default_num_workers = "0" if platform.system() == "Darwin" else "2"
    num_workers = int(os.environ.get("DIFFINTENT_NUM_WORKERS", default_num_workers))
    persistent_workers = (
        num_workers > 0
        and os.environ.get("DIFFINTENT_PERSISTENT_WORKERS", "0") == "1"
    )

    return (
        DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            collate_fn=collate_fn,
            num_workers=num_workers,
            persistent_workers=persistent_workers,
        ),
        DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            collate_fn=collate_fn,
            num_workers=num_workers,
            persistent_workers=persistent_workers,
        ),
        DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            collate_fn=collate_fn,
            num_workers=num_workers,
            persistent_workers=persistent_workers,
        ),
    )


def build_model(
    model_type: str,
    vocab: Vocabulary,
    config: dict[str, Any],
    num_intent_classes: int,
):
    """Instantiate a configured model."""

    model_config = config["model"]
    if model_type == "mlp":
        return BagOfTokensMLP(
            vocab_size=len(vocab.token_to_id),
            embedding_dim=model_config["embedding_dim"],
            hidden_dim=model_config["hidden_dim"],
            dropout=model_config["dropout"],
            num_intent_classes=num_intent_classes,
            pad_id=vocab.pad_id,
        )

    if model_type == "bigru":
        return FlatBiGRU(
            vocab_size=len(vocab.token_to_id),
            embedding_dim=model_config["embedding_dim"],
            hidden_dim=model_config["hidden_dim"],
            num_layers=model_config["num_layers"],
            dropout=model_config["dropout"],
            num_intent_classes=num_intent_classes,
            pad_id=vocab.pad_id,
        )

    if model_type == "hierarchical_transformer":
        preprocessing = config["preprocessing"]
        return HierarchicalDiffTransformer(
            vocab_size=len(vocab.token_to_id),
            pad_id=vocab.pad_id,
            num_intent_classes=num_intent_classes,
            token_embedding_dim=model_config["token_embedding_dim"],
            line_type_embedding_dim=model_config["line_type_embedding_dim"],
            line_hidden_dim=model_config["line_hidden_dim"],
            transformer_layers=model_config["transformer_layers"],
            transformer_heads=model_config["transformer_heads"],
            transformer_ff_dim=model_config["transformer_ff_dim"],
            dropout=model_config["dropout"],
            max_tokens_per_line=preprocessing["max_tokens_per_line"],
            max_lines_per_diff=preprocessing["max_lines_per_diff"],
            use_line_type_embeddings=model_config.get(
                "use_line_type_embeddings", True
            ),
        )

    raise ValueError(f"Unsupported model_type: {model_type}")
