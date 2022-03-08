from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DBSchema(BaseModel):
    class Config:
        orm_mode = True

class NotificationBase(BaseModel):
    topic: str
    message: str
    target_user: Optional[str] = "all"


class NotificationCreate(NotificationBase):
     pass


class NotificationUpdate(NotificationBase):
    is_read: bool


class Notification(DBSchema):
    id: int
    message: str

'''class Notification(NotificationBase):
    id: int
    created_at: datetime
    is_read: bool

    class Config:
        orm_mode = True'''

