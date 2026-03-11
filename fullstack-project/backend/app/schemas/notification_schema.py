"""
This module defines the schema which notifications sent to users will follow
"""

from pydantic import BaseModel

class Notification_Response(BaseModel):
    id: int
    user_ids: list[str]
    message: str
    is_read: bool
    time: str # YYYY/MM/DD HH:MM