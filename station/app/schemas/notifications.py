from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DBSchema(BaseModel):
    class Config:
        orm_mode = True

class NotificationBase(BaseModel):
    target_user: Optional[str] = "all"
    topic: str
    message: str


class NotificationCreate(BaseModel):
    id: int
    topic: Optional[str] = "trains"
    message: str


class NotificationUpdate(NotificationBase):
    is_read: bool


class Notification(DBSchema):
    id: int
    target_user: Optional[str] = "all"
    topic: Optional[str] = "trains"
    message: str
    is_read: Optional[bool] = False
    created_at: Optional[datetime] = datetime.now()
