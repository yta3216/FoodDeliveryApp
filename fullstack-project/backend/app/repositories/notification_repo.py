""" This module handles notification data storage in the application. """

from pathlib import Path
import json
import os
from typing import List, Dict, Any

NOTIFICATION_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "notifications.json"

def load_notifications() -> List[Dict[str, Any]]:
    if not NOTIFICATION_DATA_PATH.exists():
        return []
    with NOTIFICATION_DATA_PATH.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        else:
            return json.loads(content)

def save_notifications(items: List[Dict[str, Any]]) -> None:
    tmp = NOTIFICATION_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, NOTIFICATION_DATA_PATH)
