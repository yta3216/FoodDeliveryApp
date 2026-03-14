import json
from pathlib import Path

DELIVERIES_FILE = Path(__file__).parent.parent / "data" / "deliveries.json"
DRIVERS_FILE = Path(__file__).parent.parent / "data" / "drivers.json"

def load_deliveries() -> list:
    if not DELIVERIES_FILE.exists():
        return []
    with open(DELIVERIES_FILE, "r") as f:
        return json.load(f)

def save_deliveries(deliveries: list) -> None:
    with open(DELIVERIES_FILE, "w") as f:
        json.dump(deliveries, f, indent=2)

def load_drivers() -> list:
    if not DRIVERS_FILE.exists():
        return []
    with open(DRIVERS_FILE, "r") as f:
        return json.load(f)

def save_drivers(drivers: list) -> None:
    with open(DRIVERS_FILE, "w") as f:
        json.dump(drivers, f, indent=2)