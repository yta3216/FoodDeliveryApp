""" This module handles menu data storage in the application. """

from pathlib import Path
import json
import os
from typing import List, Dict, Any

MENU_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "menus.json"

def load_menus() -> List[Dict[str, Any]]:
    if not MENU_DATA_PATH.exists():
        return []
    with MENU_DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_menus(items: List[Dict[str, Any]]) -> None:
    tmp = MENU_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, MENU_DATA_PATH)
