import json
from pathlib import Path

DELIVERIES_FILE = Path(__file__).parent.parent / "data" / "deliveries.json"

def load_deliveries() -> list:
    if not DELIVERIES_FILE.exists():
        return []
    try:
        raw = DELIVERIES_FILE.read_bytes()
        if not raw.strip():
            return []
        # strip any bom and decode
        for encoding in ("utf-8-sig", "utf-16", "utf-8", "cp1252"):
            try:
                content = raw.decode(encoding).strip()
                if content:
                    return json.loads(content)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return []
    except Exception:
        return []

def save_deliveries(deliveries: list) -> None:
    with open(DELIVERIES_FILE, "w", encoding="utf-8") as f:
        json.dump(deliveries, f, indent=2)