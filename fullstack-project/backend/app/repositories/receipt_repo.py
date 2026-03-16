""" This module handles receipt data storage in the application. """

from pathlib import Path
import json
import os
from typing import List, Dict, Any

RECEIPT_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "receipts.json"


def load_receipts() -> List[Dict[str, Any]]:

    """
    **Loads all saved receipts from reciepts.json**

    Parameters: None

    Returns:
    *   **list[dict[str, Any]]**: a list of all saved reciepts. Return empty list if DNE or empty.
    """

    if not RECEIPT_DATA_PATH.exists():
        return []
    with RECEIPT_DATA_PATH.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def save_receipts(items: List[Dict[str, Any]]) -> None:
    
    """
    Saves the provided list of receipts to receipts.json.
    Uses a temporary file to prevent data corruption on write failure.
 
    Parameters:
        items (list[dict]): the full list of receipts to save
 
    Returns: None
    """
    tmp = RECEIPT_DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, RECEIPT_DATA_PATH)