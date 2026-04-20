from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from src.business_logic.models import PriceSample


class BPIChartService:
    """Build a time-series chart from collected samples."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def render(self, samples: list[PriceSample], output_path: Path, title: str = "Bitcoin Price Index (BPI)") -> Path:
        if not samples:
            raise ValueError("Cannot render an empty sample set")

        self._logger.info("Building BPI chart with %d points -> %s.", len(samples), output_path)

        ordered = sorted(samples, key=lambda s: s.captured_at)
        times = [s.captured_at for s in ordered]
        prices = [s.price_usd for s in ordered]

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(times, prices, marker="o", linewidth=1, markersize=3)
        ax.set_title(title)
        ax.set_xlabel("Time (UTC)")
        ax.set_ylabel("USD")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        fig.autofmt_xdate()
        ax.grid(True, linestyle="--", alpha=0.35)
        fig.tight_layout()
        fig.savefig(output_path, dpi=150)
        plt.close(fig)

        self._logger.info("Chart written to %s.", output_path.resolve())
        return output_path
