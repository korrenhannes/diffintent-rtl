from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.data.diff_parser import LINE_TYPE_TO_ID
from src.utils.io import read_json, write_json


SPECIAL_TOKENS = [
    "<PAD>",
    "<UNK>",
    "<MSG>",
    "<FILE>",
    "<HUNK>",
    "<CTX>",
    "<DEL>",
    "<ADD>",
]

TOKEN_PATTERN = re.compile(
    r"`[A-Za-z_][A-Za-z0-9_$]*"
    r"|\d+'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+"
    r"|'[01xXzZ]"
    r"|==|!=|<=|>=|&&|\|\||<<|>>|::|->|=>|\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=|~\^|\^~"
    r"|[A-Za-z_][A-Za-z0-9_$]*"
    r"|0x[0-9a-fA-F_]+"
    r"|\d+\.\d+"
    r"|\d+"
    r"|[][(){};:,.?@#~+\-*/%&|^!=<>]",
)

MESSAGE_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*|\d+")


def tokenize_sv_text(text: str) -> list[str]:
    """Tokenize SystemVerilog-like text."""

    return TOKEN_PATTERN.findall(text)


def tokenize_message(text: str) -> list[str]:
    """Tokenize commit-message text."""

    return [token.lower() for token in MESSAGE_PATTERN.findall(text)]


def tokenize_path(text: str) -> list[str]:
    """Split a path into useful path tokens."""

    pieces = re.split(r"[\\/._-]+", text)
    return [piece for piece in pieces if piece]


def typed_line_to_tokens(line: dict[str, object], include_line_type_token: bool = True) -> list[str]:
    """Convert a typed diff line into a token sequence."""

    line_type = str(line["type"])
    text = str(line["text"])
    tokens: list[str] = [f"<{line_type}>"] if include_line_type_token else []
    if line_type == "FILE":
        tokens.extend(tokenize_path(text))
    elif line_type == "HUNK":
        tokens.extend(tokenize_message(text))
    else:
        tokens.extend(tokenize_sv_text(text))
    return tokens


def typed_lines_to_flat_tokens(typed_lines: list[dict[str, object]]) -> list[str]:
    """Flatten typed diff lines into a single token stream."""

    flat_tokens: list[str] = []
    for line in typed_lines:
        flat_tokens.extend(typed_line_to_tokens(line, include_line_type_token=True))
    return flat_tokens


def typed_lines_to_line_tokens(typed_lines: list[dict[str, object]]) -> list[list[str]]:
    """Convert typed diff lines into per-line token sequences."""

    return [typed_line_to_tokens(line, include_line_type_token=False) for line in typed_lines]


def typed_lines_to_line_type_ids(typed_lines: list[dict[str, object]]) -> list[int]:
    """Map typed diff lines to numeric line-type IDs."""

    return [LINE_TYPE_TO_ID[str(line["type"])] for line in typed_lines]


@dataclass
class Vocabulary:
    """Simple token vocabulary."""

    token_to_id: dict[str, int]

    @property
    def id_to_token(self) -> list[str]:
        return [token for token, _ in sorted(self.token_to_id.items(), key=lambda item: item[1])]

    @property
    def pad_id(self) -> int:
        return self.token_to_id["<PAD>"]

    @property
    def unk_id(self) -> int:
        return self.token_to_id["<UNK>"]

    def encode(self, tokens: Iterable[str], max_length: int | None = None) -> list[int]:
        """Encode tokens as IDs."""

        ids = [self.token_to_id.get(token, self.unk_id) for token in tokens]
        if max_length is not None:
            ids = ids[:max_length]
        return ids

    def save(self, path: Path | str) -> None:
        """Persist the vocabulary to disk."""

        write_json(path, {"token_to_id": self.token_to_id})

    @classmethod
    def load(cls, path: Path | str) -> "Vocabulary":
        """Load a persisted vocabulary."""

        payload = read_json(path)
        return cls(token_to_id=dict(payload["token_to_id"]))


def build_vocabulary(
    token_sequences: Iterable[Iterable[str]],
    min_frequency: int = 1,
    max_size: int | None = None,
) -> Vocabulary:
    """Create a vocabulary from token sequences."""

    counter: Counter[str] = Counter()
    for sequence in token_sequences:
        counter.update(sequence)

    sorted_items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    tokens = list(SPECIAL_TOKENS)
    for token, frequency in sorted_items:
        if frequency < min_frequency or token in tokens:
            continue
        tokens.append(token)
        if max_size is not None and len(tokens) >= max_size:
            break

    token_to_id = {token: index for index, token in enumerate(tokens)}
    return Vocabulary(token_to_id=token_to_id)

