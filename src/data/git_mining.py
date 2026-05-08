from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess
from typing import Any

from src.data.diff_parser import parse_unified_diff


EXCLUDED_PATH_PARTS = [
    "/dv/",
    "/test/",
    "/tests/",
    "/vendor/",
    "/third_party/",
    "/generated/",
    "/build/",
    "/out/",
]


def run_git_command(repo_dir: Path | str, args: list[str]) -> str:
    """Run a git command in the target repository."""

    completed = subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def ensure_git_repo(repo_dir: Path | str) -> None:
    """Raise a helpful error if a repository is missing."""

    repo_path = Path(repo_dir)
    if not repo_path.exists():
        raise FileNotFoundError(
            f"Repository path does not exist: {repo_path}. "
            "Run scripts/clone_repo.sh first."
        )
    if not (repo_path / ".git").exists():
        raise FileNotFoundError(
            f"Expected a git repository at {repo_path}, but .git was not found."
        )


def is_candidate_rtl_path(path: str, strict_rtl_only: bool = True) -> bool:
    """Check whether a changed path should be considered part of the dataset."""

    normalized = "/" + path.strip("/")
    if any(part in normalized for part in EXCLUDED_PATH_PARTS):
        return False
    if not path.startswith("hw/") or not path.endswith(".sv"):
        return False
    if strict_rtl_only:
        return "/rtl/" in normalized
    return True


def _parse_commit_log(raw_log: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for chunk in raw_log.split("\x1e"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split("\x1f")
        if len(parts) != 4:
            continue
        commit_hash, parents, commit_date, subject = parts
        records.append(
            {
                "commit_hash": commit_hash.strip(),
                "parents": parents.strip(),
                "commit_date": commit_date.strip(),
                "commit_message": subject.strip(),
            }
        )
    return records


def list_commits(repo_dir: Path | str, max_commits: int | None = None) -> list[dict[str, str]]:
    """Return commit metadata in chronological order."""

    raw_log = run_git_command(
        repo_dir,
        [
            "log",
            "--reverse",
            "--date=iso-strict",
            "--pretty=format:%H%x1f%P%x1f%cI%x1f%s%x1e",
            "--",
            "hw",
        ],
    )
    records = _parse_commit_log(raw_log)
    if max_commits is not None:
        return records[:max_commits]
    return records


def list_commits_with_changed_files(
    repo_dir: Path | str,
    max_commits: int | None = None,
) -> list[dict[str, Any]]:
    """Return commit metadata plus changed-file statuses in chronological order."""

    raw_log = run_git_command(
        repo_dir,
        [
            "log",
            "--reverse",
            "--date=iso-strict",
            "--name-status",
            "--pretty=format:\x1e%H\x1f%P\x1f%cI\x1f%s",
            "--",
            "hw",
        ],
    )
    records: list[dict[str, Any]] = []
    for chunk in raw_log.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        if not lines:
            continue
        header_parts = lines[0].split("\x1f")
        if len(header_parts) != 4:
            continue

        changed_files: list[tuple[str, str]] = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            status, path = parts[0], parts[-1]
            changed_files.append((status, path))

        commit_hash, parents, commit_date, subject = header_parts
        records.append(
            {
                "commit_hash": commit_hash.strip(),
                "parents": parents.strip(),
                "commit_date": commit_date.strip(),
                "commit_message": subject.strip(),
                "changed_files": changed_files,
            }
        )

    if max_commits is not None:
        return records[:max_commits]
    return records


def _read_file_at_revision(repo_dir: Path | str, revision: str, path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout


def _read_unified_diff(
    repo_dir: Path | str,
    parent_hash: str,
    commit_hash: str,
    path: str,
) -> str:
    return run_git_command(
        repo_dir,
        ["diff", "-U3", parent_hash, commit_hash, "--", path],
    )


def extract_candidate_examples(
    repo_dir: Path | str,
    max_commits: int | None,
    max_examples: int | None,
    max_rtl_files_per_commit: int,
    prefer_single_rtl_file: bool,
    max_diff_lines: int,
    strict_rtl_only: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Mine candidate OpenTitan RTL examples."""

    ensure_git_repo(repo_dir)
    stats: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []

    for commit in list_commits_with_changed_files(repo_dir, max_commits=max_commits):
        stats["commits_examined"] += 1
        parent_hashes = [token for token in commit["parents"].split() if token]
        if len(parent_hashes) != 1:
            stats["skip_merge_or_root_commit"] += 1
            continue

        commit_message = commit["commit_message"].strip()
        if not commit_message:
            stats["skip_empty_commit_message"] += 1
            continue
        if commit_message.lower().startswith("revert"):
            stats["skip_revert_commit"] += 1
            continue

        rtl_files = [
            path
            for status, path in commit["changed_files"]
            if status == "M" and is_candidate_rtl_path(path, strict_rtl_only=strict_rtl_only)
        ]
        if not rtl_files:
            stats["skip_no_candidate_rtl_files"] += 1
            continue
        if len(rtl_files) > max_rtl_files_per_commit:
            stats["skip_too_many_rtl_files"] += 1
            continue
        if prefer_single_rtl_file and len(rtl_files) != 1:
            stats["multi_rtl_commit_fallback"] += 1

        parent_hash = parent_hashes[0]
        for file_path in rtl_files:
            unified_diff = _read_unified_diff(
                repo_dir=repo_dir,
                parent_hash=parent_hash,
                commit_hash=commit["commit_hash"],
                path=file_path,
            )
            typed_lines = parse_unified_diff(unified_diff=unified_diff, file_path=file_path)
            if not any(line["type"] in {"ADD", "DEL"} for line in typed_lines):
                stats["skip_empty_diff_after_parse"] += 1
                continue
            if len(typed_lines) > max_diff_lines:
                stats["skip_diff_too_long"] += 1
                continue

            old_code = _read_file_at_revision(repo_dir, parent_hash, file_path)
            new_code = _read_file_at_revision(repo_dir, commit["commit_hash"], file_path)
            if not old_code or not new_code:
                stats["skip_missing_file_content"] += 1
                continue

            example = {
                "repo": "opentitan",
                "commit_hash": commit["commit_hash"],
                "parent_hash": parent_hash,
                "commit_date": commit["commit_date"],
                "file_path": file_path,
                "commit_message": commit_message,
                "old_code": old_code,
                "new_code": new_code,
                "unified_diff": unified_diff,
                "raw_diff_line_count": len(typed_lines),
            }
            candidates.append(example)
            stats["examples_kept"] += 1

            if max_examples is not None and len(candidates) >= max_examples:
                return candidates, dict(stats)

    return candidates, dict(stats)
