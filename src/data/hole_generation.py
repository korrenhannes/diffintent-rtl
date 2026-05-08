from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from src.data.diff_parser import typed_lines_to_text


COMPARISON_REPLACEMENTS = [
    ("==", "!="),
    ("!=", "=="),
    ("<=", ">"),
    (">=", "<"),
    ("<", ">="),
    (">", "<="),
]

LOGICAL_REPLACEMENTS = [("&&", "||"), ("||", "&&")]

CONSTANT_REPLACEMENTS = [
    ("1'b0", "1'b1"),
    ("1'b1", "1'b0"),
    ("'0", "'1"),
    ("'1", "'0"),
]


def _clone_lines(typed_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [deepcopy(line) for line in typed_lines]


def _has_real_change(typed_lines: list[dict[str, Any]]) -> bool:
    return any(
        line["type"] in {"ADD", "DEL"} and str(line["text"]).strip()
        for line in typed_lines
    )


def _remove_line(
    typed_lines: list[dict[str, Any]],
    predicate,
    mutation_type: str,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
    for index, line in enumerate(typed_lines):
        if line["type"] == "ADD" and predicate(str(line["text"])):
            mutated = _clone_lines(typed_lines)
            removed = mutated.pop(index)
            if _has_real_change(mutated):
                return mutated, {
                    "mutation_type": mutation_type,
                    "target_text": removed["text"],
                    "line_index": index,
                }
    return None, None


def _replace_in_add_line(
    typed_lines: list[dict[str, Any]],
    replacements: list[tuple[str, str]],
    mutation_type: str,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
    for index, line in enumerate(typed_lines):
        if line["type"] != "ADD":
            continue
        original = str(line["text"])
        for old, new in replacements:
            if old not in original:
                continue
            mutated = _clone_lines(typed_lines)
            mutated[index]["text"] = original.replace(old, new, 1)
            if mutated[index]["text"] != original and _has_real_change(mutated):
                return mutated, {
                    "mutation_type": mutation_type,
                    "target_text": original,
                    "mutated_text": mutated[index]["text"],
                    "line_index": index,
                }
    return None, None


def _drop_hunk(
    typed_lines: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
    hunk_ids = []
    for line in typed_lines:
        if line["type"] == "HUNK":
            hunk_id = int(line["hunk_id"])
            if hunk_id not in hunk_ids:
                hunk_ids.append(hunk_id)
    if len(hunk_ids) < 2:
        return None, None

    drop_hunk_id = hunk_ids[-1]
    mutated = [
        deepcopy(line)
        for line in typed_lines
        if int(line["hunk_id"]) != drop_hunk_id or line["type"] == "FILE"
    ]
    if not _has_real_change(mutated):
        return None, None
    return mutated, {"mutation_type": "drop_hunk", "drop_hunk_id": drop_hunk_id}


def _mutate_new_code(example: dict[str, Any], metadata: dict[str, Any]) -> str:
    """Best-effort update of the new-code text for simple line-level mutations."""

    new_code = str(example.get("new_code", ""))
    if not new_code:
        return new_code

    lines = new_code.splitlines()
    mutation_type = metadata["mutation_type"]
    target_text = str(metadata.get("target_text", ""))
    mutated_text = str(metadata.get("mutated_text", ""))

    def _reassemble(parts: list[str]) -> str:
        text = "\n".join(parts)
        if new_code.endswith("\n"):
            text += "\n"
        return text

    if mutation_type in {
        "remove_added_guard_or_assertion",
        "remove_reset_or_default_assignment",
        "drop_added_line",
    }:
        for index, line in enumerate(lines):
            if line.rstrip() == target_text.rstrip():
                del lines[index]
                return _reassemble(lines)
        return new_code

    if mutation_type in {
        "flip_comparison_operator",
        "flip_logical_operator",
        "flip_binary_constant",
    }:
        for index, line in enumerate(lines):
            if line.rstrip() == target_text.rstrip():
                lines[index] = mutated_text
                return _reassemble(lines)
        return new_code.replace(target_text, mutated_text, 1)

    if mutation_type == "drop_hunk":
        return new_code

    return new_code


def generate_synthetic_hole(example: dict[str, Any]) -> dict[str, Any] | None:
    """Create one synthetic-hole example from a real example."""

    typed_lines = example["typed_lines"]
    candidates = [
        lambda lines: _remove_line(
            lines,
            lambda text: bool(re.search(r"\b(if|assert|assume|cover)\b", text)),
            "remove_added_guard_or_assertion",
        ),
        lambda lines: _remove_line(
            lines,
            lambda text: bool(
                re.search(r"\b(reset|rst|default)\b", text)
                and ("<=" in text or "=" in text)
            ),
            "remove_reset_or_default_assignment",
        ),
        lambda lines: _remove_line(
            lines,
            lambda text: bool(text.strip()),
            "drop_added_line",
        ),
        _drop_hunk,
        lambda lines: _replace_in_add_line(
            lines,
            COMPARISON_REPLACEMENTS,
            "flip_comparison_operator",
        ),
        lambda lines: _replace_in_add_line(
            lines,
            LOGICAL_REPLACEMENTS,
            "flip_logical_operator",
        ),
        lambda lines: _replace_in_add_line(
            lines,
            CONSTANT_REPLACEMENTS,
            "flip_binary_constant",
        ),
    ]

    for mutator in candidates:
        mutated_lines, metadata = mutator(typed_lines)
        if mutated_lines is None or metadata is None:
            continue

        normalized_diff = typed_lines_to_text(mutated_lines)
        if not normalized_diff.strip():
            continue

        pair_id = example["pair_id"]
        synthetic = dict(example)
        synthetic["typed_lines"] = mutated_lines
        synthetic["normalized_diff"] = normalized_diff
        synthetic["hole_label"] = "synthetic_hole"
        synthetic["is_synthetic"] = True
        synthetic["origin_commit_hash"] = example["commit_hash"]
        synthetic["origin_file_path"] = example["file_path"]
        synthetic["mutation_type"] = metadata["mutation_type"]
        synthetic["pair_id"] = pair_id
        synthetic["example_id"] = f"{pair_id}::synthetic::{metadata['mutation_type']}"
        synthetic["synthetic_metadata"] = metadata
        synthetic["new_code"] = _mutate_new_code(example, metadata)
        return synthetic

    return None

