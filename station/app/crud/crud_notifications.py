from sqlalchemy.orm import Session
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from .base import CRUDBase

from station.app.models.notification import Notification
from station.app.schemas.notifications import NotificationCreate, NotificationUpdate



class CRUDNotifications(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):

    def read_notifications_for_user(self, db: Session, user: str) -> List[Notification]:
        return db.query(Notification).filter(Notification.target_user == user).all()

    def create_notification(self, db: Session, *, obj_in: NotificationCreate) -> NotificationCreate:
        db_notification = self.get_notification_by_id(db, obj_in.id)

        if not db_notification:
            db_notification = Notification(
                id=obj_in.id,
                topic=obj_in.topic,
                message=obj_in.message
            )
            db.add(db_notification)
            db.commit()
            db.refresh(db_notification)
            return db_notification

    def get_notification_by_id(self, db: Session, notification_id: int) -> Notification:
        db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
        return db_notification


notifications = CRUDNotifications(Notification)
