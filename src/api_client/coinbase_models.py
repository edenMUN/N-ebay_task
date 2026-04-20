from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class CoinbaseAPIError(RuntimeError):
    """Raised when the Coinbase API returns an unexpected payload or status."""


@dataclass(frozen=True)
class CoinbaseSpotPayload:
    """Normalized spot price response from Coinbase v2 prices API."""

    base: str
    currency: str
    amount: str
    raw: Mapping[str, Any]

    @classmethod
    def from_api_json(cls, payload: Mapping[str, Any]) -> CoinbaseSpotPayload:
        try:
            data = payload["data"]
            base = str(data["base"])
            currency = str(data["currency"])
            amount = str(data["amount"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CoinbaseAPIError("Malformed Coinbase spot response") from exc
        return cls(base=base, currency=currency, amount=amount, raw=payload)
