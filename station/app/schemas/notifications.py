from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class NotificationBase(BaseModel):
    target_user: Optional[str] = "all"
    topic: str
    message: str


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(NotificationBase):
    is_read: bool


class Notification(NotificationBase):
    id: int
    created_at: datetime
    is_read: bool

    class Config:
        orm_mode = True
