from __future__ import annotations

from collections import defaultdict
from typing import Any


LINE_TYPE_ORDER = ["FILE", "HUNK", "CTX", "DEL", "ADD", "PAD"]
LINE_TYPE_TO_ID = {line_type: index for index, line_type in enumerate(LINE_TYPE_ORDER)}


def parse_unified_diff(unified_diff: str, file_path: str) -> list[dict[str, Any]]:
    """Convert a git unified diff into typed line records."""

    typed_lines: list[dict[str, Any]] = [
        {"type": "FILE", "text": file_path, "hunk_id": -1}
    ]
    current_hunk = -1

    for raw_line in unified_diff.splitlines():
        if (
            raw_line.startswith("diff --git")
            or raw_line.startswith("index ")
            or raw_line.startswith("--- ")
            or raw_line.startswith("+++ ")
        ):
            continue

        if raw_line.startswith("@@"):
            current_hunk += 1
            typed_lines.append(
                {"type": "HUNK", "text": raw_line, "hunk_id": current_hunk}
            )
            continue

        if raw_line.startswith("\\ No newline"):
            continue

        if raw_line.startswith("+"):
            typed_lines.append(
                {"type": "ADD", "text": raw_line[1:], "hunk_id": current_hunk}
            )
        elif raw_line.startswith("-"):
            typed_lines.append(
                {"type": "DEL", "text": raw_line[1:], "hunk_id": current_hunk}
            )
        elif raw_line.startswith(" "):
            typed_lines.append(
                {"type": "CTX", "text": raw_line[1:], "hunk_id": current_hunk}
            )

    return typed_lines


def typed_lines_to_text(typed_lines: list[dict[str, Any]]) -> str:
    """Render typed lines into the normalized text format used by the models."""

    return "\n".join(f"<{line['type']}> {line['text']}" for line in typed_lines)


def keep_only_changed_context(
    typed_lines: list[dict[str, Any]], keep_context_lines: bool = True
) -> list[dict[str, Any]]:
    """Optionally remove context lines while preserving file and hunk markers."""

    if keep_context_lines:
        return [dict(line) for line in typed_lines]
    return [dict(line) for line in typed_lines if line["type"] != "CTX"]


def truncate_typed_lines(
    typed_lines: list[dict[str, Any]],
    max_lines: int,
    keep_context_lines: bool = True,
) -> list[dict[str, Any]]:
    """Truncate long diffs while preferring changed lines and nearby context."""

    if max_lines <= 0:
        raise ValueError("max_lines must be positive.")

    filtered = keep_only_changed_context(typed_lines, keep_context_lines=keep_context_lines)
    if len(filtered) <= max_lines:
        return filtered

    essential_indices = [
        index
        for index, line in enumerate(filtered)
        if line["type"] in {"FILE", "HUNK", "ADD", "DEL"}
    ]

    if len(essential_indices) >= max_lines:
        keep = set(essential_indices[:max_lines])
        return [dict(line) for index, line in enumerate(filtered) if index in keep]

    changed_indices = [
        index
        for index, line in enumerate(filtered)
        if line["type"] in {"ADD", "DEL"}
    ]
    per_hunk_changed: dict[int, list[int]] = defaultdict(list)
    for index in changed_indices:
        per_hunk_changed[filtered[index]["hunk_id"]].append(index)

    context_candidates: list[tuple[int, int, int]] = []
    for index, line in enumerate(filtered):
        if line["type"] != "CTX":
            continue
        nearby = per_hunk_changed.get(line["hunk_id"], [])
        if nearby:
            distance = min(abs(index - changed_index) for changed_index in nearby)
        else:
            distance = 10**9
        context_candidates.append((distance, index, line["hunk_id"]))

    context_candidates.sort(key=lambda item: (item[0], item[1]))
    keep = set(essential_indices)
    remaining = max_lines - len(keep)
    for _, index, _ in context_candidates[:remaining]:
        keep.add(index)

    return [dict(line) for index, line in enumerate(filtered) if index in keep]


def normalize_diff(
    unified_diff: str,
    file_path: str,
    max_lines_per_diff: int,
    keep_context_lines: bool = True,
) -> tuple[list[dict[str, Any]], str]:
    """Parse, truncate, and render a unified diff into normalized form."""

    typed_lines = parse_unified_diff(unified_diff=unified_diff, file_path=file_path)
    typed_lines = truncate_typed_lines(
        typed_lines=typed_lines,
        max_lines=max_lines_per_diff,
        keep_context_lines=keep_context_lines,
    )
    return typed_lines, typed_lines_to_text(typed_lines)

