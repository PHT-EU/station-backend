from typing import Any, List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Body, Depends, HTTPException
import os

from station.app.api import dependencies
from station.app.protocol.setup import initialize_train
from station.app.protocol import execute_protocol
from station.app.schemas.trains import Train
from station.app.schemas.dl_models import DLModelCreate, DLModel
from station.app.crud.train import read_train
from station.app.crud import trains, torch_models, dl_models, datasets
from station.clients.conductor import ConductorRESTClient

router = APIRouter()


@router.post("/trains/{train_id}", response_model=Train)
def add_new_train(train_id: str, db: Session = Depends(dependencies.get_db)) -> Any:
    station_id = int(os.getenv("STATION_ID"))
    # TODO fix proposal id
    train = initialize_train(db, station_id=station_id, train_id=train_id, proposal_id=1)
    return train


@router.get("/trains/{train_id}", response_model=Train)
def get_train(train_id: Any, db: Session = Depends(dependencies.get_db)) -> Any:
    db_train = trains.get_by_train_id(db, train_id)
    return db_train


@router.get("/trains", response_model=List[Train])
def get_trains(db: Session = Depends(dependencies.get_db)):
    return trains.get_multi(db)


@router.post("/trains/sync/")
def synchronize_trains_with_conductor(db: Session = Depends(dependencies.get_db)):
    # Get the station assigned trains from conductor
    client = ConductorRESTClient()
    conductor_trains = client.get_available_trains()
    updated_trains, new_trains = trains.sync_local_trains_with_conductor(db, conductor_trains)
    # TODO store which trains are updated/new somewhere to create notifications

    # Get the models for the new trains and store them
    for train in new_trains:
        train_model = client.get_model_for_train(train.train_id, db)
        print(train_model)
        db_model = dl_models.create_model_from_conductor(
            db,
            train_id=train.id,
            model_in=train_model
        )
        print(db_model.id)

    return updated_trains


@router.post("/trains/{train_id}/model", response_model=DLModel)
def add_model_to_train(train_id: int, model_in: DLModelCreate, db: Session = Depends(dependencies.get_db)):
    db_train = trains.get(db, id=train_id)
    if not db_train:
        raise HTTPException(400, detail="Train does not exist")
    db_model = dl_models.create_model_for_train(db, train_id=db_train.train_id, obj_in=model_in)
    return db_model


@router.get("/trains/{train_id}/model", response_model=DLModel)
def get_train_model(train_id: Any, db: Session = Depends(dependencies.get_db)):
    db_train_model = dl_models.get_train_model(db, train_id)
    # TODO check byte string consistency
    return db_train_model


@router.post("/trains/{train_id}/dataset/{dataset_id}", response_model=Train)
def assign_train_dataset(train_id: Any, dataset_id: Any, db: Session = Depends(dependencies.get_db)):
    db_train = trains.get(db, id=train_id)
    if not db_train:
        raise HTTPException(400, detail="Train does not exist")
    db_dataset = datasets.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(400, detail="Dataset does not exist")

    db_train.dataset_id = db_dataset.id
    db.commit()
    db.refresh(db_train)

    return db_train


@router.post("/trains/{train_id}/start")
def start_train(train_id: int, db: Session = Depends(dependencies.get_db)):
    # TODO check if train already exists locally if not request model from conductor and pass it to the worker
    pass
