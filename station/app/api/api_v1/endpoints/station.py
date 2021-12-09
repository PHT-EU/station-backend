from typing import Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
import os
from typing import List, Optional

from station.app.api import dependencies
from station.app.schemas.dl_models import DLModelCreate, DLModel
from station.app.schemas.notifications import NotificationCreate, Notification
from station.app.schemas.station import Trains
from station.app.crud import docker_train, federated_trains, dl_models, notifications
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


@router.get("/station/trains", response_model=Trains)
def get_available_trains(active: Optional[bool] = None,
                         refresh: Optional[bool] = None,
                         db: Session = Depends(dependencies.get_db)):
    if refresh:
        # TODO query the conductor for trains
        sync_db_with_registry(db, station_id=os.getenv("STATION_ID"))

    if active:
        db_docker_trains = docker_train.get_trains_by_active_status(db, active)
        db_trains = federated_trains.get_trains_by_active_status(db, active)
    else:
        db_docker_trains = docker_train.get_multi(db)
        db_trains = federated_trains.get_multi(db)

    response = Trains(
        docker_trains=db_docker_trains,
        federated_trains=db_trains
    )

    return response


"""
Routes for using models at a station
"""


# TODO maybe split this into a different file

# @router.post("/station/models", response_model=dl_models.DLModel)
# def add_local_model(model_in: dl_models.TorchModelCreate, db: Session = Depends(dependencies.get_db)):
#     db_model = torch_models.create(db, obj_in=model_in)
#     return db_model


@router.get("/station/models", response_model=List[DLModel])
def get_station_models(db: Session = Depends(dependencies.get_db)):
    return dl_models.get_multi(db)


@router.get("/station/models/{model_id}", response_model=DLModel)
def get_model_from_station(model_id: str, db: Session = Depends(dependencies.get_db)):
    db_model = dl_models.get_model_by_model_id(db, model_id)

    if not db_model:
        raise HTTPException(status_code=400, detail=f"Model with the given id: {model_id} does not exist.")
    return db_model


@router.post("/station/models/{model_id}", response_model=DLModel)
async def add_station_model(model_id: Any, model_in: DLModelCreate, db: Session = Depends(dependencies.get_db)):
    # TODO create model and change dl models orm
    db_model = dl_models.get_model_by_model_id(db, model_id)
    if db_model:
        raise HTTPException(status_code=400, detail=f"Model with id: {model_id} already exists")

    # TODO create model in db with minio path
    db_model = dl_models.create_dl_model_with_id(db, model_id=model_id, obj_in=model_in)
    # minio_client = MinioClient()
    # res = await minio_client.store_model_file(model_id, model)
    # print(res.object_name)

    return db_model


# @router.post("/station/models/files")
# def upload_model_files_to_minio(model_id: str = Form(...),
#                                 net: UploadFile = File(...),
#                                 optimizer: UploadFile = File((...)),
#                                 loss_function: UploadFile = File((...)),
#                                 data_loader: UploadFile = File((...)),
#                                 db: Session = Depends(dependencies.get_db)):
#     print(net)
#     print(model_id)
#     # TODO add files to minio -> test the client, change to accept tar archive
#     return model_id


@router.post("/station/models/{model_id}/run")
def train_model_at_station(db: Session = Depends(dependencies.get_db)):
    # TODO
    pass


@router.get("/station/models/{model_id}/run")
def get_status_of_model_training(db: Session = Depends(dependencies.get_db)):
    # TODO
    pass


@router.post("/station/notification", response_model=Notification)
def post_notification(notification_in: NotificationCreate, db: Session = Depends(dependencies.get_db)):
    db_notification = notifications.create(db=db, obj_in=notification_in)
    return db_notification


@router.get("/station/notifications", response_model=List[Notification])
def get_all_notifications(db: Session = Depends(dependencies.get_db)):
    db_notifications = notifications.get_multi(db, skip=None, limit=None)
    return db_notifications
