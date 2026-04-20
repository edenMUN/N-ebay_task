from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from src.api_client.coinbase_btc_usd_spot_page import CoinbaseBtcUsdSpotPage
from src.api_client.coinbase_btc_usd_spot_steps import CoinbaseBtcUsdSpotSteps
from src.business_logic.bpi_orchestrator import BPIMonitorOrchestrator
from src.business_logic.chart_service import BPIChartService
from src.business_logic.collection_settings import CollectionSettings
from src.business_logic.logging_helper import business_logger
from src.business_logic.price_storage import JsonPriceSeriesRepository
from src.utils.config import AppSettings, load_app_settings
from src.utils.logging_factory import configure_automation_logging, get_logger
from src.utils.smtp_mailer import SmtpMailer


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BPI monitor: collect BTC-USD, save JSON, chart, email.")
    parser.add_argument("--interval-seconds", type=float, default=None, help="Override collection interval.")
    parser.add_argument("--target-samples", type=int, default=None, help="Override number of samples (default 60).")
    parser.add_argument("--env-file", type=str, default=".env", help="Dotenv path (skip if missing).")
    parser.add_argument("--no-clear-series", action="store_true", help="Do not delete JSON before run.")
    return parser


def _collection_from_args(base: AppSettings, args: argparse.Namespace) -> CollectionSettings:
    return CollectionSettings(
        target_samples=int(args.target_samples) if args.target_samples is not None else base.collection.target_samples,
        interval_seconds=float(args.interval_seconds)
        if args.interval_seconds is not None
        else base.collection.interval_seconds,
    )


def run_from_args(args: argparse.Namespace | None = None) -> Path:
    parsed = args or _build_parser().parse_args()
    env_path: str | None = parsed.env_file
    settings = load_app_settings(env_file=env_path if Path(env_path).is_file() else None)
    collection = _collection_from_args(settings, parsed)

    configure_automation_logging(level=logging.INFO, business_log_file=settings.business_log_file)
    get_logger("bpi.run").info(
        "BPI run | samples=%s interval_s=%s data_dir=%s",
        collection.target_samples,
        collection.interval_seconds,
        settings.data_dir,
    )

    page = CoinbaseBtcUsdSpotPage(spot_url=settings.spot_url, timeout_seconds=30.0)
    steps = CoinbaseBtcUsdSpotSteps(page=page)
    repository = JsonPriceSeriesRepository(settings.json_path, logger=business_logger("storage"))
    chart_service = BPIChartService(logger=business_logger("chart"))
    mailer = SmtpMailer()

    orchestrator = BPIMonitorOrchestrator(
        spot_steps=steps,
        repository=repository,
        chart_service=chart_service,
        mailer=mailer,
        collection=collection,
        chart_output_path=settings.chart_path,
        logger=business_logger("orchestrator"),
        sleep_fn=time.sleep,
    )

    chart_path = orchestrator.run_full_cycle(smtp=settings.smtp, clear_series_before_run=not parsed.no_clear_series)
    get_logger("bpi.run").info("Done. Chart: %s", chart_path)
    return chart_path


if __name__ == "__main__":
    run_from_args()
