from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def project_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[2]


def ensure_dir(path: Path | str) -> Path:
    """Create a directory if needed and return it as a Path."""

    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def read_json(path: Path | str) -> Any:
    """Read a JSON file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path | str, payload: Any) -> None:
    """Write JSON with pretty formatting."""

    path_obj = Path(path)
    ensure_dir(path_obj.parent)
    with path_obj.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    """Read a JSONL file into memory."""

    records: list[dict[str, Any]] = []
    path_obj = Path(path)
    if not path_obj.exists():
        return records
    with path_obj.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path | str, records: Iterable[dict[str, Any]]) -> None:
    """Write an iterable of dictionaries to JSONL."""

    path_obj = Path(path)
    ensure_dir(path_obj.parent)
    with path_obj.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_jsonl(path: Path | str, records: Iterable[dict[str, Any]]) -> None:
    """Append dictionaries to an existing JSONL file."""

    path_obj = Path(path)
    ensure_dir(path_obj.parent)
    with path_obj.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_text(path: Path | str, text: str) -> None:
    """Write plain text."""

    path_obj = Path(path)
    ensure_dir(path_obj.parent)
    with path_obj.open("w", encoding="utf-8") as handle:
        handle.write(text)

