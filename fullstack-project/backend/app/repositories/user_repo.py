"""This module handles user data storage in the application."""

from pathlib import Path
import json
import os
from typing import List, Dict, Any

USER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "users.json"

def load_users() -> List[Dict[str, Any]]:
    if not USER_DATA_PATH.exists():
        return []
    with USER_DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_users(items: List[Dict[str, Any]]) -> None:
    tmp = USER_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USER_DATA_PATH)