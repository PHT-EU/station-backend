from typing import Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
import os
from typing import List, Optional

from station.app.api import dependencies
from station.app.schemas.dl_models import DLModelCreate, DLModel
from station.app.schemas.notifications import NotificationCreate, Notification
from station.app.schemas.station import Trains
from station.app.crud import docker_trains, notifications
from station.app.docker_trains.update import sync_db_with_registry

router = APIRouter()


@router.get("/config")
def get_station_config(db: Session = Depends(dependencies.get_db)):
    # TODO store station configuration either inside yaml/config file or in db and read it here
    pass


@router.put("/config")
def update_station_config():
    # TODO allow for updates and storage of configuration values for a station
    pass
