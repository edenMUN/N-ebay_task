from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def _logger_has_stream(logger: logging.Logger) -> bool:
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            return True
    return False


def _logger_has_file_for_path(logger: logging.Logger, path: Path) -> bool:
    resolved = path.resolve()
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            try:
                if Path(handler.baseFilename).resolve() == resolved:
                    return True
            except OSError:
                continue
    return False


def configure_automation_logging(
    *,
    level: int = logging.INFO,
    business_log_file: Optional[Path] = None,
    log_format: Optional[str] = None,
) -> None:
    """
    Configure console logging for ``bpi.*`` and optional file logging for ``bpi.business.*``.

    File logs capture business-layer actions; console captures the wider ``bpi`` namespace
    (including ``bpi.utils``) for operators.
    """
    if log_format is None:
        log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format)

    bpi = logging.getLogger("bpi")
    bpi.setLevel(level)
    if not _logger_has_stream(bpi):
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(formatter)
        bpi.addHandler(stream)

    if business_log_file is not None:
        business = logging.getLogger("bpi.business")
        business.setLevel(level)
        business_log_file.parent.mkdir(parents=True, exist_ok=True)
        if not _logger_has_file_for_path(business, business_log_file):
            file_handler = logging.FileHandler(business_log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            business.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger (typically under ``bpi``)."""
    return logging.getLogger(name)
