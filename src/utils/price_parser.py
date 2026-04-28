import re


def parse_price_to_float(raw_price: str) -> float:
    if not raw_price:
        raise ValueError("Cannot parse empty price string")

    cleaned = re.sub(r"[^\d.,]", "", raw_price).strip()
    if not cleaned:
        raise ValueError(f"Could not parse price from: {raw_price}")

    # Handle both "1,234.56" and "1.234,56"-style formats.
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        if cleaned.count(",") == 1 and len(cleaned.split(",")[-1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")

    return float(cleaned)
