from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from station.app.api import dependencies
from station.app.crud.crud_notifications import notifications
from station.app.schemas.notifications import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
)

router = APIRouter()


@router.post("", response_model=Notification, status_code=201)
def add_notification(
    create_msg: NotificationCreate, db: Session = Depends(dependencies.get_db)
):
    db_notification = notifications.create(db=db, obj_in=create_msg)
    return db_notification


@router.put("/{notification_id}", response_model=Notification)
def update_notification(
    notification_id: int,
    update_msg: NotificationUpdate,
    db: Session = Depends(dependencies.get_db),
):
    db_notification = notifications.get(db, id=notification_id)
    db_notification = notifications.update(
        db=db, db_obj=db_notification, obj_in=update_msg
    )
    return db_notification


@router.delete("/{notification_id}", status_code=202, response_model=Notification)
def delete_notification(
    notification_id: int, db: Session = Depends(dependencies.get_db)
):
    deleted_notification = notifications.remove(db=db, id=notification_id)
    return deleted_notification


@router.get("/{notification_id}", response_model=Notification)
def get_notification(notification_id: int, db: Session = Depends(dependencies.get_db)):
    db_notification = notifications.get(db=db, id=notification_id)
    return db_notification


@router.get("", response_model=List[Notification])
def get_notifications(
    limit: int = 100, skip: int = 0, db: Session = Depends(dependencies.get_db)
):
    db_notifications = notifications.get_multi(db=db, skip=skip, limit=limit)
    return db_notifications
