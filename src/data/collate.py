from __future__ import annotations

from typing import Any

import torch


def collate_flat(batch: list[dict[str, Any]], pad_id: int) -> dict[str, Any]:
    """Pad flat token sequences."""

    max_length = max(len(item["token_ids"]) for item in batch)
    token_ids = torch.full((len(batch), max_length), pad_id, dtype=torch.long)
    attention_mask = torch.zeros((len(batch), max_length), dtype=torch.bool)

    for batch_index, item in enumerate(batch):
        ids = item["token_ids"]
        token_ids[batch_index, : len(ids)] = torch.tensor(ids, dtype=torch.long)
        attention_mask[batch_index, : len(ids)] = True

    return {
        "token_ids": token_ids,
        "attention_mask": attention_mask,
        "intent_labels": torch.tensor(
            [item["intent_label"] for item in batch], dtype=torch.long
        ),
        "hole_labels": torch.tensor(
            [item["hole_label"] for item in batch], dtype=torch.long
        ),
        "metadata": batch,
    }


def collate_hierarchical(batch: list[dict[str, Any]], pad_id: int) -> dict[str, Any]:
    """Pad hierarchical line/token sequences."""

    max_lines = max(len(item["line_token_ids"]) for item in batch)
    max_tokens = max(
        max(len(tokens) for tokens in item["line_token_ids"])
        if item["line_token_ids"]
        else 1
        for item in batch
    )

    line_token_ids = torch.full(
        (len(batch), max_lines, max_tokens), pad_id, dtype=torch.long
    )
    line_token_mask = torch.zeros((len(batch), max_lines, max_tokens), dtype=torch.bool)
    line_mask = torch.zeros((len(batch), max_lines), dtype=torch.bool)
    line_type_ids = torch.zeros((len(batch), max_lines), dtype=torch.long)

    for batch_index, item in enumerate(batch):
        for line_index, tokens in enumerate(item["line_token_ids"]):
            if not tokens:
                continue
            line_token_ids[batch_index, line_index, : len(tokens)] = torch.tensor(
                tokens, dtype=torch.long
            )
            line_token_mask[batch_index, line_index, : len(tokens)] = True
            line_mask[batch_index, line_index] = True
        line_type_ids[batch_index, : len(item["line_type_ids"])] = torch.tensor(
            item["line_type_ids"], dtype=torch.long
        )

    return {
        "line_token_ids": line_token_ids,
        "line_token_mask": line_token_mask,
        "line_mask": line_mask,
        "line_type_ids": line_type_ids,
        "intent_labels": torch.tensor(
            [item["intent_label"] for item in batch], dtype=torch.long
        ),
        "hole_labels": torch.tensor(
            [item["hole_label"] for item in batch], dtype=torch.long
        ),
        "metadata": batch,
    }
