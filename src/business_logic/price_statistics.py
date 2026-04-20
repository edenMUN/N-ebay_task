from __future__ import annotations

from typing import Iterable, Optional, Tuple

from src.business_logic.models import PriceSample


def max_price_usd(samples: Iterable[PriceSample]) -> Optional[Tuple[float, PriceSample]]:
    """
    Return (max_price, sample) for the highest USD observation.

    Returns None when the iterable is empty — callers should handle reporting skips.
    """
    best: Optional[Tuple[float, PriceSample]] = None
    for sample in samples:
        if best is None or sample.price_usd > best[0]:
            best = (sample.price_usd, sample)
    return best
