from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DBSchema(BaseModel):
    class Config:
        orm_mode = True

class NotificationBase(BaseModel):
    topic: Optional[str] = None
    message: Optional[str] = None
    target_user: Optional[str] = "all"
    title: Optional[str] = None
    is_read: Optional[bool] = None


class NotificationCreate(NotificationBase):
     pass


class NotificationUpdate(NotificationBase):
    pass


class Notification(NotificationBase, DBSchema):
    id: int
    message: str
    topic: Optional[str] = "trains"
    target_user: Optional[str] = "all"
    is_read: bool
    created_at: datetime


