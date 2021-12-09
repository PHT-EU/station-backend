from typing import Any, List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from station.app.api import dependencies
from station.app.schemas.trains import Train
from station.app.schemas.dl_models import DLModelCreate, DLModel
from station.app.crud import federated_trains, dl_models, datasets
from station.clients.conductor import ConductorRESTClient
from station.app.protocol.aggregation_protocol import AggregationProtocolClient

router = APIRouter()


@router.post("/federated/{train_name}", response_model=Train)
def add_new_train(train_name: str, db: Session = Depends(dependencies.get_db)) -> Any:
    # TODO fix proposal id
    if federated_trains.get_by_name(db=db, name=train_name):
        raise HTTPException(status_code=403, detail="Train already exists")

    protocol = AggregationProtocolClient(db)
    train = protocol.initialize_train(train_name)

    return train


@router.get("/federated/{train_id}", response_model=Train)
def get_train(train_id: Any, db: Session = Depends(dependencies.get_db)) -> Any:
    db_train = federated_trains.get(db, id=train_id)
    return db_train


@router.delete("/federated/{train_id}", response_model=Train)
def delete_train_with_id(train_id: Any, db: Session = Depends(dependencies.get_db)) -> Any:
    removed_train = federated_trains.remove(db, id=train_id)
    return removed_train


@router.get("/federated", response_model=List[Train])
def get_trains(db: Session = Depends(dependencies.get_db)):
    return federated_trains.get_multi(db)


@router.post("/federated/update")
def get_updates_from_conductor(db: Session = Depends(dependencies.get_db)):
    pass


@router.post("/federated/sync")
def synchronize_trains_with_conductor(db: Session = Depends(dependencies.get_db)):
    # Get the station assigned trains from conductor
    client = ConductorRESTClient()
    conductor_trains = client.get_available_trains()
    updated_trains, new_trains = federated_trains.sync_local_trains_with_conductor(db, conductor_trains)
    # TODO store which trains are updated/new somewhere to create notifications

    # Get the models for the new trains and store them
    for train in new_trains:
        train_model = client.get_model_for_train(train.train_id, db)
        db_model = dl_models.create_model_from_conductor(
            db,
            train_id=train.id,
            model_in=train_model
        )
        print(f"Created model {db_model.id} for train {train.id}")

    return updated_trains


@router.post("/trains/federated/{train_id}/model", response_model=DLModel)
def add_model_to_train(train_id: int, model_in: DLModelCreate, db: Session = Depends(dependencies.get_db)):
    db_train = federated_trains.get(db, id=train_id)
    if not db_train:
        raise HTTPException(400, detail="Train does not exist")
    db_model = dl_models.create_model_for_train(db, train_id=db_train.train_id, obj_in=model_in)
    return db_model


@router.get("/trains/federated/{train_id}/model", response_model=DLModel)
def get_train_model(train_id: Any, db: Session = Depends(dependencies.get_db)):
    db_train_model = dl_models.get_train_model(db, train_id)
    # TODO check byte string consistency
    return db_train_model


@router.post("/trains/federated/{train_id}/dataset/{dataset_id}", response_model=Train)
def assign_train_dataset(train_id: Any, dataset_id: Any, db: Session = Depends(dependencies.get_db)):
    db_train = federated_trains.get(db, id=train_id)
    if not db_train:
        raise HTTPException(400, detail="Train does not exist")
    db_dataset = datasets.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(400, detail="Dataset does not exist")

    db_train.dataset_id = db_dataset.id
    db.commit()
    db.refresh(db_train)

    return db_train


@router.post("/trains/federated/{train_id}/start")
def start_train(train_id: int, db: Session = Depends(dependencies.get_db)):
    # TODO check if train already exists locally if not request model from conductor and pass it to the worker
    pass
