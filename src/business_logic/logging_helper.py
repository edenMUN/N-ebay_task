from __future__ import annotations

import logging


BUSINESS_LOGGER_PREFIX = "bpi.business"


def business_logger(suffix: str) -> logging.Logger:
    """
    Child logger under ``bpi.business`` so file/console routing can target BL only.

    ``suffix`` should be a short submodule token, e.g. ``"orchestrator"``.
    """
    name = f"{BUSINESS_LOGGER_PREFIX}.{suffix}"
    return logging.getLogger(name)
