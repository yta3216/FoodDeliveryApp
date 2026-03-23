""" This module handles app config storage. """

from pathlib import Path
import json
import os

CONFIG_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "config.json"

# TODO: update all other files that declare global variables to use config instead
default = {
    # defaults for receipt/payment workflow
    "GLOBAL_TAX_RATE": 0.12,

    # defaults for delivery_service
    "BIKE_SPEED_KMH": 20.0,
    "CAR_SPEED_KMH": 50.0,
    "BIKE_MAX_DISTANCE_KMH": 5.0,

    # defaults for user service
    "RESET_TOKEN_EXPIRY": 900, # 15 minutes
    "SESSION_TOKEN_EXPIRY": 86400 # 24 hours
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
