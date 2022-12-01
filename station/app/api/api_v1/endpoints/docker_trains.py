import json
from typing import List, Union
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from station.app.api import dependencies
from station.app.trains.docker import airflow
from station.app.schemas.docker_trains import DockerTrain, DockerTrainCreate, DockerTrainConfig, \
    DockerTrainConfigCreate, DockerTrainConfigUpdate, DockerTrainExecution, DockerTrainState, DockerTrainSavedExecution
from station.app.crud.crud_docker_trains import docker_trains
from station.app.crud.crud_train_configs import docker_train_config
from station.clients.harbor_client import harbor_client

router = APIRouter()


@router.post("/sync", response_model=List[DockerTrain])
def synchronize_database(db: Session = Depends(dependencies.get_db)):
    return docker_trains.synchronize_central(db)


@router.get("", response_model=List[DockerTrain])
def get_available_trains(limit: int = 0, db: Session = Depends(dependencies.get_db)):
    if limit != 0:
        db_trains = docker_trains.get_multi(db, limit=limit)
    else:
        db_trains = docker_trains.get_multi(db)
    return db_trains


@router.post("", response_model=DockerTrain)
def register_train(create_msg: DockerTrainCreate, db: Session = Depends(dependencies.get_db)):
    if docker_trains.get_by_train_id(db, train_id=create_msg.train_id):
        raise HTTPException(status_code=400, detail=f"Train with id '{create_msg.train_id}' already exists.")
    db_train = docker_trains.create(db, obj_in=create_msg)
    return db_train


@router.get("/{train_id}", response_model=DockerTrain)
def get_train_by_train_id(train_id: Union[int, str], db: Session = Depends(dependencies.get_db)):
    if isinstance(train_id, str):
        db_train = docker_trains.get_by_train_id(db, train_id)
    else:
        db_train = docker_trains.get(db, id=train_id)
    if not db_train:
        raise HTTPException(status_code=404, detail=f"Train with id '{train_id}' not found.")
    return db_train

@router.delete("/{train_id}", response_model=DockerTrain)
def get_train_by_train_id(train_id: str, db: Session = Depends(dependencies.get_db)):
    db_train = docker_trains.delete_by_train_id(db, train_id=train_id)
    return db_train


@router.post("/{train_id}/run", response_model=DockerTrainSavedExecution)
def run_docker_train(train_id: str, run_config: DockerTrainExecution = None,
                     db: Session = Depends(dependencies.get_db)):

    execution = airflow.run_train(db, train_id, run_config)
    return execution


@router.get("/{train_id}/config", response_model=DockerTrainConfig)
def get_config_for_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    train = docker_trains.get_by_train_id(db, train_id)
    if not train.config_id:
        raise HTTPException(status_code=404, detail=f"Train '{train_id}' does not have an assigned config.")
    config = docker_train_config.get(db, train.config_id)
    return config


@router.post("/{train_id}/config/{config_id}", response_model=DockerTrain)
def assign_config_to_docker_train(train_id: str, config_id: int, db: Session = Depends(dependencies.get_db)):
    train = docker_trains.get_by_train_id(db, train_id=train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train with id '{train_id}' not found.")

    config = docker_train_config.get(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Config with id '{config_id}' not found.")

    train = docker_train_config.assign_to_train(db, train_id, config.id)
    return train


@router.get("/{train_id}/state", response_model=DockerTrainState)
def get_state_for_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    state = docker_trains.read_train_state(db, train_id)
    return state


@router.put("/{train_id}/state", response_model=DockerTrainState)
def update_state_for_train(train_id: str, state: DockerTrainState, db: Session = Depends(dependencies.get_db)):
    state = docker_trains.update_train_state(db, train_id, state)
    return state


@router.get("/configs/all", response_model=List[DockerTrainConfig])
def get_all_docker_train_configs(db: Session = Depends(dependencies.get_db), skip: int = 0, limit: int = 100):
    db_configs = docker_train_config.get_multi(db, skip=skip, limit=limit)
    return db_configs


@router.post("/config", response_model=DockerTrainConfig)
def add_docker_train_configuration(config_in: DockerTrainConfigCreate, db: Session = Depends(dependencies.get_db)):
    print(config_in)
    if docker_train_config.get_by_name(db, name=config_in.name):
        raise HTTPException(status_code=400, detail="A config with the given name already exists.")
    config = docker_train_config.create(db, obj_in=config_in)
    return config


@router.put("/config/{config_id}", response_model=DockerTrainConfig)
def update_docker_train_configuration(update_config: DockerTrainConfigUpdate, config_id: int,
                                      db: Session = Depends(dependencies.get_db)):
    old_config = docker_train_config.get(db, config_id)
    if not old_config:
        raise HTTPException(status_code=404, detail=f"Config with id '{config_id}' not found.")
    config = docker_train_config.update(db, db_obj=old_config, obj_in=update_config)
    return config


@router.get("/config/{config_id}", response_model=DockerTrainConfig)
def get_docker_train_configuration(config_id: int, db: Session = Depends(dependencies.get_db)):
    config = docker_train_config.get(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Config with id '{config_id}' not found.")

    return config


@router.get("/executions/all", response_model=List[DockerTrainSavedExecution])
def get_all_docker_train_executions(skip: int = 0, limit: int = 100, db: Session = Depends(dependencies.get_db)):
    db_executions = docker_trains.get_executions(db, skip=skip, limit=limit)
    return db_executions


@router.get("/{train_id}/executions", response_model=List[DockerTrainSavedExecution])
def get_docker_train_executions(train_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(dependencies.get_db)):
    executions = docker_trains.get_train_executions(db, train_id,)
    return executions
