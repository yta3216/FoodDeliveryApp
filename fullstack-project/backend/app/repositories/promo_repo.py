"""This module handles promo code data storage in the application"""

from pathlib import Path
import json
import os
from typing import Any

PROMO_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "promo_codes.json"

def load_promos_codes() -> list[dict[str, Any]]:
    """
    **Loads all saved promo codes.**

    Parameters: None

    Returns:
    *    **list[dict[str, Any]]**: all promo codes
    """
    if not PROMO_DATA_PATH.exists():
        return []
    with PROMO_DATA_PATH.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        else:
            return json.loads(content)

def save_promos_codes(items: list[dict[str, Any]]) -> None:
    """
    **Overwrites current saved list of promo codes with the passed list of promo codes.**

    Parameters:
        items (list[dict[str, Any]]): promo codes to save

    Returns:
        None
    """
    tmp = PROMO_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PROMO_DATA_PATH)