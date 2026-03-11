"""
This module defines notification class and its methods.
"""

from datetime import datetime
from fastapi import HTTPException

from app.repositories.notification_repo import load_notifications, save_notifications
from app.realtime.connection_manager import ConnectionManager
from app.schemas.notification_schema import Notification_Response

connection_manager = ConnectionManager()

# Generic notification class. Not defined as BaseModel because the creation is strictly internal.
class Notification():
 
    # create notification. save method must be used as well for it to be saved.
    def __init__(self, message: str, user_ids: list[str]):
        self.id = self._get_next_id()
        self.message = message
        self.user_ids = user_ids
        self.is_read = False
        self.time = datetime.now().strftime('%Y/%m/%d %H:%M') # YYYY/MM/DD HH:MM
    
    # get next notif id.
    def _get_next_id(self) -> int:
        notifs = load_notifications()
        if len(notifs) == 0:
            return 1
        return max(notif["id"] for notif in notifs) + 1

    # convert to the respective fastapi schema
    def to_model(self) -> Notification_Response:
        return Notification_Response(
            id=self.id,
            message=self.message,
            user_ids=self.user_ids,
            is_read=self.is_read,
            time=self.time
        )

    # save the new notification
    def save(self) -> None:
        notifs = load_notifications()
        notifs.append(self.to_model().model_dump())
        save_notifications(notifs)
    
    # mark notification as read
    def read_notification(self) -> None:
        notifs = load_notifications()
        for notif in notifs:
            if notif["id"] == self.id:
                notif["is_read"] = True
                save_notifications(notifs)
                return None
        raise HTTPException(status_code=404, detail=f"Notification '{self.id}' not found")
    
    # send the notification to the list of users. this causes the notification to be saved.
    async def send_to_users(self, user_ids: list[str]) -> None:
        self.save()
        for user_id in user_ids:
            await connection_manager.send_message(user_id, self.to_model())
