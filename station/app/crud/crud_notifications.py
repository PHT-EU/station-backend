from typing import List

from sqlalchemy.orm import Session

from station.app.models.notification import Notification
from station.app.schemas.notifications import NotificationCreate, NotificationUpdate

from .base import CRUDBase


class CRUDNotifications(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):

    def read_notifications_for_user(self, db: Session, user: str) -> List[Notification]:
        return db.query(Notification).filter(Notification.target_user == user).all()



notifications = CRUDNotifications(Notification)
