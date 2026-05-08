from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from torch.utils.data import Dataset

from src.data import HOLE_LABELS, INTENT_LABELS
from src.data.diff_parser import truncate_typed_lines
from src.data.tokenizer import (
    Vocabulary,
    tokenize_message,
    typed_lines_to_flat_tokens,
    typed_lines_to_line_tokens,
    typed_lines_to_line_type_ids,
)


INTENT_TO_ID = {label: index for index, label in enumerate(INTENT_LABELS)}
HOLE_TO_ID = {label: index for index, label in enumerate(HOLE_LABELS)}


@dataclass
class DatasetConfig:
    max_lines_per_diff: int
    max_tokens_per_line: int
    max_total_tokens_flat: int
    keep_context_lines: bool = True
    text_source: str = "diff"


class DiffIntentDataset(Dataset):
    """PyTorch dataset for flat and hierarchical diff inputs."""

    def __init__(
        self,
        examples: list[dict[str, Any]],
        vocab: Vocabulary,
        config: DatasetConfig,
        representation: str,
    ) -> None:
        self.examples = examples
        self.vocab = vocab
        self.config = config
        self.representation = representation
        self.items = [self._prepare_item(example) for example in self.examples]

    def __len__(self) -> int:
        return len(self.items)

    def _prepare_typed_lines(self, example: dict[str, Any]) -> list[dict[str, Any]]:
        return truncate_typed_lines(
            typed_lines=example["typed_lines"],
            max_lines=self.config.max_lines_per_diff,
            keep_context_lines=self.config.keep_context_lines,
        )

    def _prepare_item(self, example: dict[str, Any]) -> dict[str, Any]:
        item: dict[str, Any] = {
            "intent_label": INTENT_TO_ID[example["intent_label"]],
            "hole_label": HOLE_TO_ID[example["hole_label"]],
            "example_id": example["example_id"],
            "commit_hash": example["commit_hash"],
            "file_path": example["file_path"],
            "commit_message": example["commit_message"],
            "pair_id": example["pair_id"],
        }

        if self.config.text_source == "message":
            message_tokens = tokenize_message(example["commit_message"])
            token_ids = self.vocab.encode(
                message_tokens, max_length=self.config.max_total_tokens_flat
            )
            item["token_ids"] = token_ids
            item["line_token_ids"] = [token_ids]
            item["line_type_ids"] = [0]
            return item

        typed_lines = self._prepare_typed_lines(example)

        if self.representation == "flat":
            flat_tokens = typed_lines_to_flat_tokens(typed_lines)
            item["token_ids"] = self.vocab.encode(
                flat_tokens, max_length=self.config.max_total_tokens_flat
            )
            return item

        if self.representation == "hierarchical":
            line_tokens = typed_lines_to_line_tokens(typed_lines)
            line_types = typed_lines_to_line_type_ids(typed_lines)
            item["line_token_ids"] = [
                self.vocab.encode(tokens, max_length=self.config.max_tokens_per_line)
                for tokens in line_tokens[: self.config.max_lines_per_diff]
            ]
            item["line_type_ids"] = line_types[: self.config.max_lines_per_diff]
            return item

        raise ValueError(f"Unsupported representation: {self.representation}")

    def __getitem__(self, index: int) -> dict[str, Any]:
        return self.items[index]
