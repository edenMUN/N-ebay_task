from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.business_logic.models import PriceSample, PriceSeriesDocument


class JsonPriceSeriesRepository:
    """Append-only JSON persistence for BPI samples (durable per fetch)."""

    def __init__(self, json_path: Path, logger: logging.Logger) -> None:
        self._path = json_path
        self._logger = logger

    @property
    def path(self) -> Path:
        return self._path

    def load_document(self) -> PriceSeriesDocument:
        if not self._path.exists():
            self._logger.info("No existing JSON at %s; starting empty series.", self._path)
            return PriceSeriesDocument()
        raw_text = self._path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
        doc = PriceSeriesDocument.from_json_dict(payload)
        self._logger.info("Loaded %d samples from %s.", len(doc.samples), self._path)
        return doc

    def save_document(self, document: PriceSeriesDocument) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(document.to_json_dict(), indent=2), encoding="utf-8")
        tmp_path.replace(self._path)
        self._logger.info("Persisted %d samples to %s.", len(document.samples), self._path)

    def append_sample(self, sample: PriceSample, document: Optional[PriceSeriesDocument] = None) -> PriceSeriesDocument:
        """Load (or reuse) document, append sample, save atomically."""
        doc = document if document is not None else self.load_document()
        doc.samples.append(sample)
        self._logger.info(
            "Appending sample captured_at=%s price_usd=%.2f (total=%d).",
            sample.captured_at.isoformat(),
            sample.price_usd,
            len(doc.samples),
        )
        self.save_document(doc)
        return doc

    def reset(self) -> None:
        if self._path.exists():
            self._path.unlink()
            self._logger.info("Removed existing series file %s.", self._path)
