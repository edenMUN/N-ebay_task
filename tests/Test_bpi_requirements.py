from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from src.api_client.coinbase_btc_usd_spot_steps import CoinbaseBtcUsdSpotSteps
from src.business_logic.chart_service import BPIChartService
from src.business_logic.logging_helper import business_logger
from src.business_logic.models import PriceSample, utc_now
from src.business_logic.price_statistics import max_price_usd
from src.business_logic.price_storage import JsonPriceSeriesRepository
from src.utils.config import load_app_settings
from src.utils.smtp_mailer import EmailSendResult, SmtpMailer


class Test_BPI_Requirements:
    def test_requirement_01_http_get_coinbase_spot_api(self, live_steps: CoinbaseBtcUsdSpotSteps) -> None:
        """HTTP GET to the Coinbase BTC-USD spot endpoint returns JSON."""
        body = live_steps.execute_get_spot_request()
        assert isinstance(body, dict)
        assert "data" in body
        assert body["data"].get("base") == "BTC"
        assert body["data"].get("currency") == "USD"

    def test_requirement_02_extract_bitcoin_price_usd(self, live_steps: CoinbaseBtcUsdSpotSteps) -> None:
        """Extract the current Bitcoin spot price in USD from the API response."""
        payload = live_steps.fetch_spot_payload()
        price_usd = float(payload.amount)
        assert price_usd > 0.0
        assert payload.currency == "USD"

    def test_requirement_03_collect_and_save_prices_to_json_on_interval(
        self,
        live_steps: CoinbaseBtcUsdSpotSteps,
        tmp_path: Path,
    ) -> None:
        """
        Collect spot USD price on a time interval and persist each observation to JSON.

        Production uses one sample per minute for 60 minutes (see ``run_automation.py`` / ``.env``).
        Here we use two live samples and a short pause to prove the same persistence path without a 60-minute wait.
        """
        log = business_logger("requirements")
        json_path = tmp_path / "bpi_window.json"
        repo = JsonPriceSeriesRepository(json_path, logger=log)

        payload_1 = live_steps.fetch_spot_payload()
        repo.append_sample(PriceSample(captured_at=utc_now(), price_usd=float(payload_1.amount)))
        time.sleep(2)
        payload_2 = live_steps.fetch_spot_payload()
        repo.append_sample(PriceSample(captured_at=utc_now(), price_usd=float(payload_2.amount)))

        doc = repo.load_document()
        assert len(doc.samples) == 2
        assert json_path.is_file()

    def test_requirement_04_generate_bpi_graph_after_collecting_data(
        self,
        live_steps: CoinbaseBtcUsdSpotSteps,
        tmp_path: Path,
    ) -> None:
        """After a series of prices exists, generate a Bitcoin Price Index (BPI) graph (PNG)."""
        log = business_logger("requirements")
        json_path = tmp_path / "bpi_for_chart.json"
        chart_path = tmp_path / "bpi_chart.png"
        repo = JsonPriceSeriesRepository(json_path, logger=log)

        for _ in range(2):
            p = live_steps.fetch_spot_payload()
            repo.append_sample(PriceSample(captured_at=utc_now(), price_usd=float(p.amount)))
            time.sleep(1)

        samples = repo.load_document().samples
        chart_service = BPIChartService(logger=log)
        out = chart_service.render(samples, chart_path)
        assert out == chart_path
        assert chart_path.is_file()

    @pytest.mark.skipif(
        not (os.getenv("SMTP_USER", "").strip() and os.getenv("SMTP_PASSWORD", "").strip()),
        reason="Set SMTP_USER and SMTP_PASSWORD (e.g. Gmail app password) to run the live email requirement.",
    )
    def test_requirement_05_send_email_max_price_and_bpi_graph(
        self,
        live_steps: CoinbaseBtcUsdSpotSteps,
        tmp_path: Path,
    ) -> None:
        """Send one email with the maximum BTC-USD in the window and the generated BPI graph (real SMTP)."""
        log = business_logger("requirements")
        json_path = tmp_path / "bpi_email.json"
        chart_path = tmp_path / "bpi_email.png"
        repo = JsonPriceSeriesRepository(json_path, logger=log)

        for _ in range(2):
            p = live_steps.fetch_spot_payload()
            repo.append_sample(PriceSample(captured_at=utc_now(), price_usd=float(p.amount)))
            time.sleep(1)

        document = repo.load_document()
        peak = max_price_usd(document.samples)
        assert peak is not None
        max_value, at_sample = peak

        chart_service = BPIChartService(logger=log)
        chart_service.render(document.samples, chart_path)

        settings = load_app_settings(env_file=".env" if Path(".env").is_file() else None)
        log.info("Sending live SMTP report for requirement 5.")
        result: EmailSendResult = SmtpMailer().send_bpi_report(
            smtp=settings.smtp,
            max_price_usd=max_value,
            max_at=at_sample.captured_at,
            chart_path=chart_path,
        )
        assert max_value > 0
        assert result.chart_attached == chart_path.name
