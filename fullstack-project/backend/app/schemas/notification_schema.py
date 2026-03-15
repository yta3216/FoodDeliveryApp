"""
This module defines the schema which notifications sent to users will follow.
"""

from pydantic import BaseModel

class Notification_Response(BaseModel):
    """
    **Defines the attributions of a notification sent to users.**

    Attributes:
    *   **id** (int): the identifier of the notification object
    *   **user_ids** (list[str]): the identifiers of the users who should receive this notification
    *   **message** (str): the message of the notification
    *   **is_read** (bool): true if message has been read, false if not
    *   **time** (str): time that notification was sent, or time it was created if not sent yet (YYYY/MM/DD HH:MM)
    """
    id: int
    user_ids: list[str]
    message: str
    is_read: bool
    time: str