from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CollectionSettings:
    """Controls sampling cadence and window length (defaults: 60 samples × 60s)."""

    target_samples: int = 60
    interval_seconds: float = 60.0
