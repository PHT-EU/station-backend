from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from station.app.api import dependencies
from station.clients.airflow import docker_trains as airflow_docker_train
from station.app.schemas.docker_trains import DockerTrain, DockerTrainCreate, DockerTrainConfig, \
    DockerTrainConfigCreate, DockerTrainConfigUpdate, DockerTrainExecution, DockerTrainState, DockerTrainSavedExecution
from station.app.crud.crud_docker_trains import docker_trains
from station.app.crud.crud_train_configs import docker_train_config
from station.clients.harbor_client import harbor_client

router = APIRouter()

@router.get("/sync")
def synchronize_database(station_id: int = None, db: Session = Depends(dependencies.get_db)):
    artifacts = harbor_client.get_artifacts_for_station(station_id=station_id)
    error = None
    try:
        error = artifacts['errors']
    except:
        for train in artifacts:
            id = train["name"].split("/")[1]
            created_at = train["creation_time"][:-1]
            updated_at = train["update_time"][:-1]
            if created_at == updated_at:
                updated_at = None
            new_train = docker_trains.add_if_not_exists(db, train_id=id, created_at=created_at, updated_at=updated_at)
        return {"station_id": station_id}
    if error:
        raise HTTPException(status_code=404,
                            detail=f"Station not found or no train registered at station {station_id}.")


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
def get_train_by_train_id(train_id: str, db: Session = Depends(dependencies.get_db)):
    db_train = docker_trains.get_by_train_id(db, train_id)
    if not db_train:
        raise HTTPException(status_code=404, detail=f"Train with id '{train_id}' not found.")
    return db_train


@router.post("/{train_id}/run")
def run_docker_train(train_id: str, run_config: DockerTrainExecution, db: Session = Depends(dependencies.get_db)):
    # todo check with tyra
    run_json = airflow_docker_train.run_train(db, train_id, run_config)
    return run_json


@router.get("/{train_id}/config", response_model=DockerTrainConfig)
def get_config_for_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    train = docker_trains.get_by_train_id(db, train_id)
    if not train.config:
        raise HTTPException(status_code=404, detail=f"Train '{train_id}' does not have an assigned config.")
    return train.config


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


@router.get("/{train_id}/executions", response_model=List[DockerTrainSavedExecution])
def get_docker_train_executions(train_id: str, db: Session = Depends(dependencies.get_db)):
    executions = docker_trains.get_train_executions(db, train_id)
    return executions
