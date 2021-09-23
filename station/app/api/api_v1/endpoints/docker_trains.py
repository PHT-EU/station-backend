from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from station.app.api import dependencies
from station.clients.airflow import docker_trains
from station.app.schemas.docker_trains import DockerTrain, DockerTrainCreate, DockerTrainConfig, DockerTrainConfigCreate, DockerTrainConfigUpdate, DockerTrainExecution
from station.app.crud.docker_trains import create_train, read_train_by_train_id, read_trains, read_train_config
from station.app.crud.crud_docker_trains import docker_train
from station.app.crud.crud_train_configs import docker_train_config

router = APIRouter()


@router.get("/trains/docker", response_model=List[DockerTrain])
def get_available_trains(active: bool = None, limit: int = 0, db: Session = Depends(dependencies.get_db)):
    db_trains = docker_train.get_trains_by_active_status(db, active, limit)
    return db_trains


@router.post("/trains/docker", response_model=DockerTrain)
def register_train(create_msg: DockerTrainCreate, db: Session = Depends(dependencies.get_db)):
    db_train = docker_train.create(db, obj_in=create_msg)
    return db_train


@router.get("/trains/docker/{train_id}", response_model=DockerTrain)
def get_train_by_train_id(train_id: str, db: Session = Depends(dependencies.get_db)):
    db_train = docker_train.get_by_train_id(db, train_id)
    return db_train


@router.post("/trains/docker/{train_id}/run")
def run_docker_train(train_id: str, run_config: DockerTrainExecution, db: Session = Depends(dependencies.get_db)):
    run_id = docker_trains.run_train(db, train_id, run_config)
    return run_id


@router.get("/trains/docker/{train_id}/run")
def get_latest_train_execution_result(train_id: str, db: Session = Depends(dependencies.get_db)):
    # TODO get execution details from db or airflow
    pass


@router.get("/trains/docker/{train_id}/config", response_model=DockerTrainConfig)
def get_config_for_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    train_config = docker_train_config.get_by_train_id(db, train_id)
    return train_config


@router.post("/trains/docker/{train_id}/config/{config_id}", response_model=DockerTrain)
def assign_config_to_docker_train(train_id: str, config_id: int, db: Session = Depends(dependencies.get_db)):
    train = docker_train_config.assign_to_train(db, train_id, config_id)
    return train


@router.get("/trains/docker/{train_id}/state")
def get_state_for_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    pass


@router.get("/trains/docker/configs", response_model=List[DockerTrainConfig])
def get_all_docker_train_configs(db: Session = Depends(dependencies.get_db), limit: int = 100, skip: int = 0):
    config_all = docker_train_config.get_multi(db, limit=limit, skip=skip)
    return config_all


@router.post("/trains/docker/config", response_model=DockerTrainConfig)
def add_docker_train_configuration(config_in: DockerTrainConfigCreate, db: Session = Depends(dependencies.get_db)):
    config = docker_train_config.create(db, obj_in=config_in)
    return config


@router.put("/trains/docker/config/{config_id}", response_model=DockerTrainConfig)
def update_docker_train_configuration(update_config: DockerTrainConfigUpdate, config_id: int, db: Session = Depends(dependencies.get_db)):
    old_config = docker_train_config.get(db, config_id)
    config = docker_train_config.update(db, db_obj=old_config, obj_in=update_config)
    return config


@router.get("/trains/docker/config/{config_id}", response_model=DockerTrainConfig)
def get_docker_train_configuration(config_id: int, db: Session = Depends(dependencies.get_db)):
    config = docker_train_config.get(db, config_id)
    return config
