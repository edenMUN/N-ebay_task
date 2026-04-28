import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


def _apply_env_overrides(test_data: Dict[str, Any]) -> Dict[str, Any]:
    credentials = test_data.setdefault("credentials", {})
    env_username = os.getenv("EBAY_USERNAME")
    env_password = os.getenv("EBAY_PASSWORD")

    if env_username:
        credentials["username"] = env_username
    if env_password:
        credentials["password"] = env_password

    return test_data


def get_env_credentials() -> Dict[str, str]:
    load_dotenv()
    username = (os.getenv("EBAY_USERNAME") or "").strip()
    password = (os.getenv("EBAY_PASSWORD") or "").strip()

    if not username or not password:
        raise ValueError(
            "Missing eBay credentials in environment. "
            "Set EBAY_USERNAME and EBAY_PASSWORD in .env."
        )
    return {"username": username, "password": password}


def data_file_for_env(env: str) -> str:
    """Resolve JSON path: default -> data/data.json; else -> data/data.<env>.json."""
    normalized = (env or "default").strip().lower()
    if normalized in ("", "default"):
        return "data/data.json"
    return f"data/data.{normalized}.json"


def load_test_data(
    data_file: str = "data/data.json",
    *,
    dotenv_suffix: str | None = None,
) -> Dict[str, Any]:
    load_dotenv()
    suffix = (dotenv_suffix or "default").strip().lower()
    if suffix not in ("", "default"):
        env_path = Path(f".env.{suffix}")
        if env_path.is_file():
            load_dotenv(env_path, override=True)
    file_path = Path(data_file)
    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {data_file}")

    with file_path.open("r", encoding="utf-8") as handle:
        loaded_data = json.load(handle)
    return _apply_env_overrides(loaded_data)
