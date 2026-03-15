""" This module handles order data storage in the application. """

from pathlib import Path
import json
import os
from typing import Any

ORDER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.json"

def load_orders() -> list[dict[str, Any]]:
    """
    **Loads all saved orders.**

    Parameters: None

    Returns:
    *    **list[dict[str, Any]]**: all orders
    """
    if not ORDER_DATA_PATH.exists():
        return []
    with ORDER_DATA_PATH.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        else:
            return json.loads(content)

def save_orders(items: list[dict[str, Any]]) -> None:
    """
    **Overwrites current saved list of order with the passed list of orders.**

    Parameters:
        items (list[dict[str, Any]]): orders to save

    Returns:
        None
    """
    tmp = ORDER_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ORDER_DATA_PATH)
