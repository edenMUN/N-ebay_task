from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoinbaseBtcUsdSpotPage:
    """
    Page Object: holds endpoint references only (no HTTP side effects).

    QA-style separation — URLs and timeouts are centralized for review and reuse.
    """

    spot_url: str = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    timeout_seconds: float = 30.0
