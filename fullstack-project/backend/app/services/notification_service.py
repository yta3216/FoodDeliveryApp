"""
This module defines notification class and its methods.
"""

from datetime import datetime
from typing import Any
from fastapi import HTTPException

from app.repositories.notification_repo import load_notifications, save_notifications

# Generic notification class
class Notification():
 
    # create notification.
    def __init__(self, message: str):
        notifs = load_notifications()
        self.id = self.get_next_id_from_list(notifs)
        self.message = message
        self.is_read = True
        self.time = datetime.now().strftime('%Y/%m/%d %H:%M') # YYYY/MM/DD HH:MM
    
    # convert to dictionary, store type
    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "id": self.id,
            "message": self.message,
            "is_read": self.is_read,
            "time": self.time
        }

    # pass in the loaded notifications so we don't load them twice
    @staticmethod
    def get_next_id_from_list(notifs: list[dict[str, Any]]) -> int:
        if len(notifs) == 0:
            return 1
        return max(notif["id"] for notif in notifs) + 1
    
    def read_notification(self) -> None:
        notifs = load_notifications()
        for notif in notifs:
            if notif["id"] == self.id:
                notif["is_read"] = True
                save_notifications(notifs)
                return None
        raise HTTPException(status_code=404, detail=f"Notification '{self.id}' not found")

# Class for order notifications
class OrderNotification(Notification):
    user_ids: list[str]

    # create notification
    def __init__(self, message: str, user_ids: list[str]):
        super().__init__(message)
        self.user_ids = user_ids
    
    # convert to dictionary for saving
    def to_dict(self) -> dict[str, Any]:
        notif_dict = super().to_dict()
        notif_dict["user_ids"] = self.user_ids
        return notif_dict
