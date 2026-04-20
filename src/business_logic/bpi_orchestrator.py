from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from src.api_client.coinbase_btc_usd_spot_steps import CoinbaseBtcUsdSpotSteps
from src.api_client.coinbase_models import CoinbaseSpotPayload
from src.business_logic.chart_service import BPIChartService
from src.business_logic.collection_settings import CollectionSettings
from src.business_logic.models import PriceSample, utc_now
from src.business_logic.price_statistics import max_price_usd
from src.business_logic.price_storage import JsonPriceSeriesRepository
from src.utils.smtp_mailer import SmtpMailer, SmtpSettings

SleepFn = Callable[[float], None]
NowFn = Callable[[], datetime]


class BPIMonitorOrchestrator:
    """Runs collection (JSON), then BPI chart + SMTP report. All progress is logged via ``logger``."""

    def __init__(
        self,
        spot_steps: CoinbaseBtcUsdSpotSteps,
        repository: JsonPriceSeriesRepository,
        chart_service: BPIChartService,
        mailer: SmtpMailer,
        collection: CollectionSettings,
        chart_output_path: Path,
        logger: logging.Logger,
        sleep_fn: SleepFn,
        now_fn: Optional[NowFn] = None,
    ) -> None:
        self._spot_steps = spot_steps
        self._repository = repository
        self._chart_service = chart_service
        self._mailer = mailer
        self._collection = collection
        self._chart_output_path = chart_output_path
        self._logger = logger
        self._sleep_fn = sleep_fn
        self._now_fn = now_fn or utc_now

    def run_full_cycle(self, smtp: SmtpSettings, clear_series_before_run: bool = True) -> Path:
        if clear_series_before_run:
            self._logger.info("Clearing prior JSON series before run.")
            self._repository.reset()

        self._run_collection_phase()
        return self._run_post_collection_phase(smtp)

    def _run_collection_phase(self) -> None:
        self._logger.info(
            "Starting collection: %d samples every %.1f seconds.",
            self._collection.target_samples,
            self._collection.interval_seconds,
        )
        for index in range(1, self._collection.target_samples + 1):
            self._fetch_and_persist_sample()
            self._logger.info("Collection progress %d/%d.", index, self._collection.target_samples)
            if index < self._collection.target_samples:
                self._sleep_fn(self._collection.interval_seconds)
        self._logger.info("Collection phase complete.")

    def _fetch_and_persist_sample(self) -> PriceSample:
        self._logger.info("HTTP GET: fetching BTC-USD spot from Coinbase.")
        payload: CoinbaseSpotPayload = self._spot_steps.fetch_spot_payload()
        price = float(payload.amount)
        self._logger.info("Extracted BTC-USD spot price: %.2f", price)
        sample = PriceSample(captured_at=self._now_fn(), price_usd=price)
        self._repository.append_sample(sample)
        self._logger.info("Saved sample to JSON (total persisted in this run).")
        return sample

    def _run_post_collection_phase(self, smtp: SmtpSettings) -> Path:
        self._logger.info("Starting post-collection: max price, BPI chart, email.")
        document = self._repository.load_document()
        peak = max_price_usd(document.samples)
        if peak is None:
            raise RuntimeError("No samples in JSON; cannot build BPI report.")

        max_value, at_sample = peak
        self._logger.info(
            "Maximum BTC-USD in window: %.2f at %s.",
            max_value,
            at_sample.captured_at.isoformat(),
        )

        chart_path = self._chart_service.render(document.samples, self._chart_output_path)
        self._logger.info(
            "Sending email with max price and chart attachment (recipients=%s).",
            ", ".join(smtp.mail_to),
        )
        self._mailer.send_bpi_report(
            smtp=smtp,
            max_price_usd=max_value,
            max_at=at_sample.captured_at,
            chart_path=chart_path,
        )
        self._logger.info("Email sent successfully.")
        self._logger.info("Post-collection finished.")
        return chart_path
