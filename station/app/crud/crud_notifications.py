from sqlalchemy.orm import Session
from typing import List

from .base import CRUDBase

from station.app.models.notification import Notification
from station.app.schemas.notifications import NotificationCreate, NotificationUpdate
from dateutil import parser


class CRUDNotifications(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):

    def read_notifications_for_user(self, db: Session, user: str) -> List[Notification]:
        return db.query(Notification).filter(Notification.target_user == user).all()


notifications = CRUDNotifications(Notification)
