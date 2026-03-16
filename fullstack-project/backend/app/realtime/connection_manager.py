""" 
This class keeps track of WebSocket connections. 
It follows the "Singleton" design pattern, as there should be only one instance in the application.
"""

from fastapi import WebSocket

from app.schemas.notification_schema import Notification_Response

class ConnectionManager:
    """
    This class defines the attributes and behaviour of the connection manager for this application.

    The connection manager keeps track of active WebSocket connections, and uses the Singleton
    design pattern to ensure that only one instance is maintained at a time, and thus all requests
    to the connection manager refer to the same instance.

    Attributes:
        _instance (ConnectionManger): the active connection manager object
        active_connections (dict[str, list[WebSocket]]): a dictionary storing user ids and their active WebSocket connections
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new ConnectionManager. ensures only one instance is ever active at a time.

        Parameters: None

        Returns:
            ConnectionManager: the connection manager instance
        """
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance.active_connections = {}
        return cls._instance
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """
        Adds a new WebSocket connection to the connection manager.

        Parameters:
            user_id (str): the identifier of the user who is now connected
            websocket (WebSocket): the new WebSocket connection object

        Returns: None
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        """
        Disconnects a WebSocket connection from the connection manager.

        Parameters:
            user_id (str): the identifier of the user who is to be disconnected
            websocket (WebSocket): the disconnected WebSocket connection object

        Returns: None
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

    async def send_message(self, user_id: str, notification: Notification_Response):
        """
        Sends a notification to the provided user if they have an active WebSocket connection.

        Parameters:
            user_id (str): the identifier of the user to send the notification to
            notification (Notification_Response): the notification to send

        Returns: None
        """
        if user_id not in self.active_connections:
            return
        for websocket in self.active_connections[user_id]:
            await websocket.send_json(notification.model_dump())
        