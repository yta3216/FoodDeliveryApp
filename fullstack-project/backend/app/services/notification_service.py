"""
This module defines notification class and its methods.
"""

from datetime import datetime
from fastapi import HTTPException

from app.repositories.notification_repo import load_notifications, save_notifications
from app.realtime.connection_manager import ConnectionManager
from app.schemas.notification_schema import Notification_Response

connection_manager = ConnectionManager()

class Notification():
    """
    Defines the attributes and behaviour of notifications in the system.

    Attributes:
        id (int): the identifier for the notification
        message (str): the body text to be sent in the notification
        user_ids (list[str]): list of users who will receive this notification when sent
        is_read (bool): true if notification has been read, false otherwise
        time (str): time (YYYY/MM/DD HH:MM) that notification was sent, or time created if not yet sent
    """
    def __init__(self, message: str, user_ids: list[str]):
        """
        Creates a new notification object. It is not saved to the database until it is sent.
        id and time are set automatically, and is_read is initially set to False for all users. 
        Time has format YYYY/MM/DD HH:MM.

        Parameters:
            message (str): the body text to be sent in the notification
            user_ids (list[str]): list of users who will receive this notification when sent
        
        Returns:
            Notification: the newly created notification object

        Raises:
            HTTPException (status_code = 400): if notification has no recipients
        """
        if len(user_ids) == 0:
            raise HTTPException(status_code=400, detail="Notification must have at least one recipient")
        self.id = self._get_next_id()
        self.message = message
        self.user_ids = user_ids
        self.is_read = {user_id: False for user_id in user_ids}
        self.time = datetime.now().strftime('%Y/%m/%d %H:%M')

    def _get_next_id(self) -> int:
        """
        Computes the next available identifier for a new notification object.

        Parameters: None

        Returns:
            int: the next available id
        """
        notifs = load_notifications()
        if len(notifs) == 0:
            return 1
        return max(notif["id"] for notif in notifs) + 1

    @classmethod
    def model_to_Notification(cls, notif_dict: Notification_Response):
        """
        Converts the current Notification_Response pydantic model to Notification class
        so that methods can be used.

        Parameters:
            notif_dict (Notification_Response): the notification data as a pydantic model
        
        Returns:
            Notification: a Notification object with the same data as the pydantic model
        """
        notif_data = notif_dict.model_dump()
        notif = cls(notif_data["message"], notif_data["user_ids"])
        notif.id = notif_data["id"]
        notif.is_read = notif_data["is_read"]
        notif.time = notif_data["time"]
        return notif

    def to_model(self) -> Notification_Response:
        """
        Converts the current Notification object to a Notification_Response schema for communication with frontend.

        Parameters: None

        Returns:
            Notification_Response: the current notification in the correct form according to the schema
        """
        return Notification_Response(
            id=self.id,
            message=self.message,
            user_ids=self.user_ids,
            is_read=self.is_read,
            time=self.time
        )

    def save(self) -> None:
        """
        Saves the current notification to the notification database.

        Parameters: None

        Returns: None
        """
        notifs = load_notifications()
        notifs.append(self.to_model().model_dump())
        save_notifications(notifs)
    
    def mark_as_read(self, user_id) -> Notification_Response:
        """
        Marks notification as read and saves to database.

        Parameters: None

        Returns:
            Notification_Response: the read notification in the correct form according to the schema

        Raises:
            HTTPException (status_code = 404): if this notifications id not found in notifications.json
            HTTPException (status_code = 404): if user_id is not in list of readers (which matches recipient list)
        """
        notifs = load_notifications()
        for notif in notifs:
            if notif["id"] == self.id:
                if user_id not in notif["is_read"]:
                    raise HTTPException(status_code=404, detail=f"User '{user_id}' cannot read notification '{self.id}'")
                notif["is_read"][user_id] = True
                save_notifications(notifs)
                return self.to_model()
        raise HTTPException(status_code=404, detail=f"Notification '{self.id}' not found")
    
    async def send_to_users(self) -> None:
        """
        Sends the current notification to the specified recipients in user_ids.
        The notification is saved to the database in the process with a timestamp
        so users can see it later if they are not logged in when it is sent.

        Parameters: None

        Returns: None

        Raises:
            HTTPException(status_code=400): if notification does not have any recipients
        """
        self.time = datetime.now().strftime('%Y/%m/%d %H:%M')
        self.save()
        for user_id in self.user_ids:
            await connection_manager.send_message(user_id, self.to_model())
