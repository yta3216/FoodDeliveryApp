""" 
This class keeps track of WebSocket connections. 
It follows the "Singleton" design pattern, as there should be only one instance in the application.
"""

from fastapi import WebSocket

from app.schemas.notification_schema import Notification_Response

class ConnectionManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance.active_connections = {}
        return cls._instance
    
    # connect a new websocket
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    # disconnect a websocket
    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections.remove(websocket)

    # send notification to a user
    async def send_message(self, user_id: str, notification: Notification_Response):
        if user_id not in self.active_connections:
            return
        for websocket in self.active_connections[user_id]:
            await websocket.send_json(notification)
        