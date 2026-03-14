""" This module handles notification data storage in the application. """

from pathlib import Path
import json
import os
from typing import Any

NOTIFICATION_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "notifications.json"

def load_notifications() -> list[dict[str, Any]]:
    """
    **Loads all saved notifications.**

    Parameters: None

    Returns:
    *   **list[dict[str, Any]]**: all notifications
    """
    if not NOTIFICATION_DATA_PATH.exists():
        return []
    with NOTIFICATION_DATA_PATH.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        else:
            return json.loads(content)

def save_notifications(items: list[dict[str, Any]]) -> None:
    """
    **Overwrites current saved list of notifications with the passed list of notifications.

    Parameters:
    *   **items** (list[dict[str, Any]]): notifications to save

    Returns: None
    """
    tmp = NOTIFICATION_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, NOTIFICATION_DATA_PATH)
