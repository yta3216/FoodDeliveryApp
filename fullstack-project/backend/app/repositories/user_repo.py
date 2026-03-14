"""This module handles user data storage in the application."""

from pathlib import Path
import json
import os
from typing import Any

USER_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "users.json"

def load_users() -> list[dict[str, Any]]:
    """
    **Loads all saved users.**

    Parameters: None

    Returns:
    *   **list[dict[str, Any]]**: all users
    """
    if not USER_DATA_PATH.exists():
        return []
    with USER_DATA_PATH.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        else:
            return json.loads(content)

def save_users(items: list[dict[str, Any]]) -> None:
    """
    **Overwrites the current saved list of users with the passed list of users.**

    Parameters:
    *   **items** (list[dict[str, Any]]): users to save

    Returns: None
    """
    tmp = USER_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USER_DATA_PATH)