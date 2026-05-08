from __future__ import annotations

import re
from typing import Any


INTENT_PATTERNS = {
    "bug_fix": [
        "fix",
        "bug",
        "wrong",
        "regression",
        "incorrect",
        "issue",
        "repair",
        "fail",
        "failure",
    ],
    "feature_or_behavior_change": [
        "add",
        "implement",
        "support",
        "enable",
        "introduce",
        "new",
        "feature",
    ],
    "refactor_cleanup": [
        "refactor",
        "cleanup",
        "rename",
        "move",
        "style",
        "tidy",
        "simplify",
        "remove unused",
    ],
    "configuration_timing": [
        "clock",
        "reset",
        "timing",
        "param",
        "parameter",
        "width",
        "config",
        "fsm",
        "latency",
    ],
}

GENERIC_MESSAGES = {
    "update",
    "misc",
    "cleanup",
    "fixup",
    "changes",
}


def _count_pattern_matches(message: str, patterns: list[str]) -> int:
    count = 0
    for pattern in patterns:
        escaped = re.escape(pattern)
        if " " in pattern:
            count += len(re.findall(escaped, message))
        else:
            count += len(re.findall(rf"\b{escaped}\w*\b", message))
    return count


def assign_intent_label(commit_message: str) -> tuple[str | None, str]:
    """Weak-label a commit message or return a discard reason."""

    message = commit_message.strip().lower()
    if not message:
        return None, "empty_commit_message"
    if message in GENERIC_MESSAGES:
        return None, "generic_commit_message"
    if message.startswith("revert") or "this reverts commit" in message:
        return None, "revert_commit_message"

    scores = {
        label: _count_pattern_matches(message, patterns)
        for label, patterns in INTENT_PATTERNS.items()
    }
    max_score = max(scores.values())
    if max_score <= 0:
        return None, "no_intent_keyword_match"

    winners = [label for label, score in scores.items() if score == max_score and score > 0]
    if len(winners) > 1:
        return None, "ambiguous_multiple_max_labels"

    non_zero_labels = [label for label, score in scores.items() if score > 0]
    if len(non_zero_labels) > 1 and max_score == 1:
        return None, "ambiguous_multiple_weak_labels"

    return winners[0], "ok"


def label_raw_examples(
    raw_examples: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Assign weak labels and separate discarded examples."""

    kept: list[dict[str, Any]] = []
    discarded: list[dict[str, Any]] = []
    reason_counts: dict[str, int] = {}

    for record in raw_examples:
        label, reason = assign_intent_label(record["commit_message"])
        if label is None:
            discarded_record = dict(record)
            discarded_record["discard_reason"] = reason
            discarded.append(discarded_record)
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            continue

        kept_record = dict(record)
        kept_record["intent_label"] = label
        kept.append(kept_record)

    return kept, discarded, reason_counts

