""" testing WebSocket connections and actions """

from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest
from app.main import app
from app.realtime.connection_manager import ConnectionManager
from app.services.notification_service import Notification
from app.routers.websocket_router import connection_manager as cm
from testing.test_authorization import register_and_login

client = TestClient(app)

# pass a brand new connection manager. won't work with the router though
@pytest.fixture 
def test_cm(): 
    ConnectionManager._instance = None 
    return ConnectionManager()

# test connection manager creation
def test_cm_create(test_cm):
    assert test_cm.active_connections == {}

# ensure only one instance of connection manager can exist
def test_singleton(test_cm):
    test_cm.active_connections = {"connection 1": []}
    test_cm2 = ConnectionManager()
    assert test_cm2.active_connections == {"connection 1": []}

# test connecting a websocket for the first time
def test_connect():
    token, user_id = register_and_login("testuser246@testing.com")
    with client.websocket_connect(
        f"/ws/{user_id}", 
        headers={"Authorization": f"Bearer {token}"}
    ):
        assert user_id in cm.active_connections
        assert len(cm.active_connections[user_id]) == 1

# test connecting a second device for the same user
def test_connect_second():
    cm._instance = None
    token, user_id = register_and_login("testuser266@testing.com")
    with client.websocket_connect(
        f"/ws/{user_id}", 
        headers={"Authorization": f"Bearer {token}"}
    ):
        with client.websocket_connect(
        f"/ws/{user_id}", 
        headers={"Authorization": f"Bearer {token}"}
        ):
            assert user_id in cm.active_connections
            assert len(cm.active_connections[user_id]) == 2

# test sending a message to user
@pytest.mark.anyio
async def test_send_message():
    cm._instance = None
    token, user_id = register_and_login("testuser789@testing.com")
    with client.websocket_connect(
        f"/ws/{user_id}", 
        headers={"Authorization": f"Bearer {token}"}
    ) as websocket:
        
        notification = Notification("test message", [user_id])
        await notification.send_to_users()

        assert websocket.receive_json()["message"] == "test message"
