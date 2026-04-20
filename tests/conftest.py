"""Shared pytest hooks and fixtures for BPI automation tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.api_client.coinbase_btc_usd_spot_page import CoinbaseBtcUsdSpotPage
from src.api_client.coinbase_btc_usd_spot_steps import CoinbaseBtcUsdSpotSteps

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DOTENV_PATH = _PROJECT_ROOT / ".env"


def _load_dotenv_if_present() -> None:
    """Populate os.environ from ``.env`` when the file exists (idempotent)."""
    if _DOTENV_PATH.is_file():
        load_dotenv(_DOTENV_PATH, override=False)


# Collection-time bootstrap so ``os.getenv`` / ``skipif`` see the same values as runtime tests.
_load_dotenv_if_present()


@pytest.fixture(scope="session", autouse=True)
def load_test_env() -> None:
    """Ensure ``.env`` is applied for the whole session before any test runs."""
    _load_dotenv_if_present()


@pytest.fixture()
def coinbase_spot_page() -> CoinbaseBtcUsdSpotPage:
    """Live Coinbase spot API page object (real HTTP)."""
    return CoinbaseBtcUsdSpotPage()


@pytest.fixture()
def live_steps(coinbase_spot_page: CoinbaseBtcUsdSpotPage) -> CoinbaseBtcUsdSpotSteps:
    """Steps facade over the live Coinbase BTC-USD spot client."""
    return CoinbaseBtcUsdSpotSteps(coinbase_spot_page)
