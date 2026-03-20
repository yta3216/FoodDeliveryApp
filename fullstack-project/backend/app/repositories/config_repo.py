""" This module handles app config storage. """

from pathlib import Path
import json
import os

CONFIG_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "config.json"

# TODO: update all other files that declare global variables to use config instead
default = {
    "tax_rate": 0.12
}

def load_config() -> dict:
    """
    **Loads all saved configs.**

    Parameters: None

    Returns:
    *   **dict**: all configs
    """
    if not CONFIG_DATA_PATH.exists():
        return default
    with CONFIG_DATA_PATH.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return default
        else:
            return json.loads(content)

def save_config(items: dict) -> None:
    """
    **Overwrites current saved configs with the passed configs.

    Parameters:
    *   **items** (dict): configs to save

    Returns: None
    """
    tmp = CONFIG_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_DATA_PATH)
