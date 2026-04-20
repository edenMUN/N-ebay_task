from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

import requests

from src.api_client.coinbase_btc_usd_spot_page import CoinbaseBtcUsdSpotPage
from src.api_client.coinbase_models import CoinbaseAPIError, CoinbaseSpotPayload


class CoinbaseBtcUsdSpotSteps:
    """Page Object steps: real HTTP GET against the configured Coinbase spot page."""

    def __init__(self, page: CoinbaseBtcUsdSpotPage, session: Optional[requests.Session] = None) -> None:
        self._page = page
        self._session = session

    @property
    def page(self) -> CoinbaseBtcUsdSpotPage:
        return self._page

    def execute_get_spot_request(self) -> Mapping[str, Any]:
        """GET spot price; return parsed JSON (2xx only)."""
        response = self._execute_get()
        response.raise_for_status()
        try:
            parsed: Any = response.json()
        except ValueError as exc:
            raise CoinbaseAPIError("Response body is not valid JSON") from exc
        if not isinstance(parsed, MutableMapping):
            raise CoinbaseAPIError("Top-level JSON must be an object")
        return parsed

    def fetch_spot_payload(self) -> CoinbaseSpotPayload:
        """GET and validate structure; return typed payload."""
        return CoinbaseSpotPayload.from_api_json(self.execute_get_spot_request())

    def _execute_get(self) -> requests.Response:
        url = self._page.spot_url
        timeout = self._page.timeout_seconds
        if self._session is not None:
            return self._session.get(url, timeout=timeout)
        return requests.get(url, timeout=timeout)
