"""Logging setup: rotating file under ProgramData, plus an optional UI sink."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "defenderbye"


def data_dir() -> Path:
    base = os.environ.get("PROGRAMDATA", str(Path.home()))
    return Path(base) / "DefenderBye"


class _CallbackHandler(logging.Handler):
    def __init__(self, callback: Callable[[str], None]) -> None:
        super().__init__()
        self._callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        self._callback(self.format(record))


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def setup_logging(
    log_dir: Path | None = None, sink: Callable[[str], None] | None = None
) -> logging.Logger:
    logger = get_logger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            log_dir / "defenderbye.log", maxBytes=512_000, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    if sink is not None:
        ch = _CallbackHandler(sink)
        ch.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(ch)
    return logger
