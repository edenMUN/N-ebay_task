from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from src.business_logic.collection_settings import CollectionSettings
from src.utils.smtp_mailer import SmtpSettings


def _split_emails(raw: str) -> List[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class AppSettings:
    """Application configuration loaded from environment (after optional ``.env``)."""

    data_dir: Path
    json_relative_path: str
    chart_relative_path: str
    spot_url: str
    collection: CollectionSettings
    smtp: SmtpSettings
    business_log_file: Path | None

    @property
    def json_path(self) -> Path:
        return self.data_dir / self.json_relative_path

    @property
    def chart_path(self) -> Path:
        return self.data_dir / self.chart_relative_path


def load_app_settings(env_file: str | None = ".env") -> AppSettings:
    """
    Load settings from the process environment.

    When ``env_file`` is provided and exists, variables are populated via ``python-dotenv`` first.
    """
    if env_file:
        path = Path(env_file)
        if path.is_file():
            load_dotenv(path)

    data_dir = Path(os.environ.get("BPI_DATA_DIR", "data")).resolve()
    json_name = os.environ.get("BPI_JSON_FILE", "bpi_series.json")
    chart_name = os.environ.get("BPI_CHART_FILE", "bpi_chart.png")
    spot_url = os.environ.get("BPI_SPOT_URL", "https://api.coinbase.com/v2/prices/BTC-USD/spot")

    target_samples = int(os.environ.get("BPI_TARGET_SAMPLES", "60"))
    interval_seconds = float(os.environ.get("BPI_INTERVAL_SECONDS", "60"))
    log_raw = os.environ.get("BPI_BUSINESS_LOG_FILE", "").strip()
    business_log_file = Path(log_raw).resolve() if log_raw else None

    smtp_host = os.environ.get("SMTP_HOST", "localhost")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    mail_from = os.environ.get("REPORT_EMAIL_FROM", "bpi-monitor@example.com")
    mail_to_raw = os.environ.get("REPORT_EMAIL_TO", "qa@example.com")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    smtp = SmtpSettings(
        host=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_password,
        mail_from=mail_from,
        mail_to=_split_emails(mail_to_raw),
        use_tls=use_tls,
    )

    return AppSettings(
        data_dir=data_dir,
        json_relative_path=json_name,
        chart_relative_path=chart_name,
        spot_url=spot_url,
        collection=CollectionSettings(target_samples=target_samples, interval_seconds=interval_seconds),
        smtp=smtp,
        business_log_file=business_log_file,
    )
