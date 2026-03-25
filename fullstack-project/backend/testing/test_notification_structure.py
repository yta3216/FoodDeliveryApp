"""
Testing the general implementation of notifications.
"""

from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest
from app.main import app
from app.repositories.notification_repo import load_notifications
from app.services.notification_service import Notification
from .test_password_updates import register_user

client = TestClient(app)

# common notification
@pytest.fixture
def notification():
    return Notification("test message", ["user1", "user2"])

# notification for an actual user
@pytest.fixture
def real_notification(register_user):
    return Notification("testing testing 1 2 3", [register_user.get("user_id")])

# mock database
@pytest.fixture
def mock_load(mocker):
    return mocker.patch("app.services.notification_service.load_notifications")

# test creation
def test_create(notification):
    assert notification.message == "test message"
    assert notification.user_ids == ["user1", "user2"]
    assert notification.is_read == {"user1": False, "user2": False}

# test creation with empty user list
    with pytest.raises(HTTPException) as e:
        notification = Notification("test message 2", [])
    assert e.value.status_code == 400

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
    assert notification_model.is_read == {"user1": False, "user2": False}

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
    notification.mark_as_read("user1")
    notifs = load_notifications()
    for notif in notifs:
        if notif["id"] == notification.id:
            loaded_notif = notif
    assert loaded_notif["is_read"].get("user1") == True

# test that HTTP 404 status is raised when notification not found
def test_read_missing_notif(mock_load, notification):
    mock_load.return_value = []
    with pytest.raises(HTTPException) as e:
        notification.mark_as_read("user1")
    assert e.value.status_code == 404

# test that HTTP 404 status is raised when user is not a recipient
def read_notif_not_recipient(mock_load, notification):
    mock_load.return_value = []
    notification.save()
    with pytest.raises(HTTPException) as e:
        notification.mark_as_read("user5")
    assert e.value.status_code == 404

# test reading notification from route
def test_read_notif_route(real_notification, register_user):
    real_notification.save()
    user_id = register_user.get("user_id")
    auth_token = register_user.get("token")

    response = client.patch(f"/user/{user_id}/notifications/{real_notification.id}/read",
                            headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    
    notifs = load_notifications()
    for notif in notifs:
        if notif.get("id") == real_notification.id:
            assert notif.get("is_read").get(user_id) == True
