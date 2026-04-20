from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Mapping, MutableMapping, Sequence


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PriceSample:
    captured_at: datetime
    price_usd: float

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "captured_at": self.captured_at.isoformat(),
            "price_usd": self.price_usd,
        }

    @classmethod
    def from_json_dict(cls, row: Mapping[str, Any]) -> PriceSample:
        raw_ts = row["captured_at"]
        if isinstance(raw_ts, str):
            captured_at = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        elif isinstance(raw_ts, datetime):
            captured_at = raw_ts
        else:
            raise ValueError("captured_at must be ISO string or datetime")
        return cls(captured_at=captured_at, price_usd=float(row["price_usd"]))


@dataclass
class PriceSeriesDocument:
    """Serializable container for all samples in the current monitoring window."""

    samples: List[PriceSample] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return {"samples": [s.to_json_dict() for s in self.samples]}

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, Any]) -> PriceSeriesDocument:
        raw_samples = payload.get("samples", [])
        if not isinstance(raw_samples, Sequence):
            raise ValueError("samples must be a list")
        samples = [PriceSample.from_json_dict(dict(r)) for r in raw_samples]  # type: ignore[arg-type]
        return cls(samples=list(samples))

    @classmethod
    def from_mutable_json(cls, payload: MutableMapping[str, Any]) -> PriceSeriesDocument:
        return cls.from_json_dict(payload)
