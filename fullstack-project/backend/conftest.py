import sys
import shutil
from pathlib import Path
import pytest

# Add the backend directory to sys.path so pytest can find 'app'
sys.path.insert(0, str(Path(__file__).parent))

DATA_PATH = Path(__file__).resolve().parent / "app" / "data"

@pytest.fixture(autouse=True)
def backup_and_restore_data():
    """Backup json files before tests, restore after."""
    json_files = list(DATA_PATH.glob("*.json"))
    
    # Backup
    for f in json_files:
        shutil.copy(f, f.with_suffix(".backup"))

    yield  # Run all tests

    # Restore
    for f in json_files:
        backup = f.with_suffix(".backup")
        shutil.copy(backup, f)
        backup.unlink()