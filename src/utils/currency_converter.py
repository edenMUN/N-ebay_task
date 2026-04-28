from __future__ import annotations

import re

# Static rates are sufficient for deterministic test assertions.
# Base recommendation: keep these values aligned with business expectations.
_FX_RATES: dict[tuple[str, str], float] = {
    ("ILS", "GBP"): 1 / 4.8,
    ("GBP", "ILS"): 4.8,
    ("USD", "ILS"): 3.7,
    ("ILS", "USD"): 1 / 3.7,
    ("USD", "GBP"): 0.79,
    ("GBP", "USD"): 1 / 0.79,
    ("EUR", "ILS"): 4.0,
    ("ILS", "EUR"): 1 / 4.0,
}

_SYMBOL_TO_CODE = {
    "£": "GBP",
    "₪": "ILS",
    "$": "USD",
    "€": "EUR",
}


def extract_currency_code(raw_text: str) -> str | None:
    if not raw_text:
        return None

    code_match = re.search(r"\b([A-Z]{3})\b", raw_text)
    if code_match:
        return code_match.group(1)

    for symbol, code in _SYMBOL_TO_CODE.items():
        if symbol in raw_text:
            return code
    return None


def convert_amount(amount: float, from_currency: str, to_currency: str) -> float:
    from_code = (from_currency or "").upper()
    to_code = (to_currency or "").upper()
    if from_code == to_code:
        return amount

    rate = _FX_RATES.get((from_code, to_code))
    if rate is None:
        raise ValueError(f"Missing FX rate for {from_code}->{to_code}")
    return amount * rate
