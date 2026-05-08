from __future__ import annotations

import logging
from pathlib import Path

from src.utils.io import ensure_dir


def configure_logging(log_path: Path | str | None = None) -> logging.Logger:
    """Configure a root logger with stdout and optional file output."""

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_path is not None:
        path_obj = Path(log_path)
        ensure_dir(path_obj.parent)
        file_handler = logging.FileHandler(path_obj, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

