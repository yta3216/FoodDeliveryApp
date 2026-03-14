""" This file handles restaurant data storage in the application. """

from pathlib import Path
import json
import os
from typing import Any

RESTAURANT_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "restaurants.json"

def load_restaurants() -> list[dict[str, Any]]:
    """
    **Loads all saved restaurants.**

    Parameters: None

    Returns:
    *    **list[dict[str, Any]]**: all restaurants stored in restaurants.json
    """
    if not RESTAURANT_DATA_PATH.exists():
        return []
    with RESTAURANT_DATA_PATH.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        else:
            return json.loads(content)

def save_restaurants(items: list[dict[str, Any]]) -> None:
    """
    **Overwrites the current saved list of restaurants with the passed list of restaurants.**

    Parameters:
    *   **items** (list[dict[str, Any]]): restaurants to save

    Returns: None
    """
    tmp = RESTAURANT_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, RESTAURANT_DATA_PATH)
