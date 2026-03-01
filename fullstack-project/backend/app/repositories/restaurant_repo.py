""" This module handles restaurant data storage in the application. """

from pathlib import Path
import json
import os
from typing import List, Dict, Any

RESTAURANT_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "restaurants.json"

def load_restaurants() -> List[Dict[str, Any]]:
    if not RESTAURANT_DATA_PATH.exists():
        return []
    with RESTAURANT_DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_restaurants(items: List[Dict[str, Any]]) -> None:
    tmp = RESTAURANT_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, RESTAURANT_DATA_PATH)
