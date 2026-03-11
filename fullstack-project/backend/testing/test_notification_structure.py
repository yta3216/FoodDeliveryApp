"""
Testing the general implementation of notifications.
"""

from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest
from app.main import app
from app.repositories.notification_repo import load_notifications
from app.services.notification_service import Notification

client = TestClient(app)

# common notification
@pytest.fixture
def notification():
    return Notification("test message", ["user1", "user2"])

# mock database
@pytest.fixture
def mock_load(mocker):
    return mocker.patch("app.services.notification_service.load_notifications")

# test creation
def test_create(notification):
    assert notification.message == "test message"
    assert notification.user_ids == ["user1", "user2"]
    assert notification.is_read == False

# test getting id with both an empty database an one with an entry
@pytest.mark.parametrize(
        "existing_db, expected_id",
        [
            ([], 1),
            ([{"id": 1}], 2),
        ],
)
def test_get_next_id(mock_load, notification, existing_db, expected_id):
    mock_load.return_value = existing_db
    assert notification._get_next_id() == expected_id

# test converting Notification class to the pydantic model
def test_to_model(notification):
    notification_model = notification.to_model()
    assert notification_model.message == "test message"
    assert notification_model.user_ids == ["user1", "user2"]
    assert notification_model.is_read == False

# test saving notification to db
def test_save(mock_load, notification):
    mock_load.return_value = []
    notification.save()
    notifs = load_notifications()
    for notif in notifs:
        if notif["id"] == notification.id:
            loaded_notif = notif
    assert loaded_notif["message"] == notification.message

# test marking notification as read
def test_read_notif(mock_load, notification):
    mock_load.return_value = []
    notification.save()
    notification.read_notification()
    notifs = load_notifications()
    for notif in notifs:
        if notif["id"] == notification.id:
            loaded_notif = notif
    assert loaded_notif["is_read"] == True

# test that http 404 status is raised when notification not found
def test_read_missing_notif(mock_load, notification):
    mock_load.return_value = []
    with pytest.raises(HTTPException) as e:
        notification.read_notification()
    assert e.value.status_code == 404
