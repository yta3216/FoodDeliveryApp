import sys
import shutil
from pathlib import Path
import pytest

# Add the backend directory to sys.path so pytest can find 'app'
sys.path.insert(0, str(Path(__file__).parent))

USER_DATA_PATH = Path(__file__).resolve().parent / "app" / "data" / "users.json"
BACKUP_PATH = USER_DATA_PATH.with_suffix(".backup")

@pytest.fixture(scope="session", autouse=True)
def backup_and_restore_user_data():
    """Backup users.json before tests, restore after."""
    # Backup
    if USER_DATA_PATH.exists():
        shutil.copy(USER_DATA_PATH, BACKUP_PATH)
    
    yield  # Run all tests
    
    # Restore
    if BACKUP_PATH.exists():
        shutil.copy(BACKUP_PATH, USER_DATA_PATH)
        BACKUP_PATH.unlink()