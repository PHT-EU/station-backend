from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from station.app.api import dependencies
from station.clients.airflow import docker_trains
from station.app.schemas.docker_trains import DockerTrain, DockerTrainCreate, DockerTrainRun
from station.app.crud.docker_trains import create_train, read_train_by_train_id, read_trains


router = APIRouter()


@router.get("/docker/trains/", response_model=List[DockerTrain])
def get_available_trains(active: bool = None, limit: int = 0, db: Session = Depends(dependencies.get_db)):
    db_trains = read_trains(db, active=active, limit=limit)
    return db_trains


@router.post("/docker/trains/", response_model=DockerTrain)
def register_train(create_msg: DockerTrainCreate, db: Session = Depends(dependencies.get_db)):
    db_train = create_train(db, create_msg)
    return db_train


@router.get("/docker/trains/{train_id}", response_model=DockerTrain)
def get_train_by_train_id(train_id: str, db: Session = Depends(dependencies.get_db)):
    db_train = read_train_by_train_id(db, train_id)
    return db_train


@router.post("/docker/trains/{train_id}/run")
def run_docker_train(train_id: str, run_config: DockerTrainRun, db: Session = Depends(dependencies.get_db)):
    # TODO get config and execute station_airflow dag
    run_id = docker_trains.run_train(db, train_id, run_config)
    return run_id


@router.get("/docker/trains/{train_id}/run")
def get_latest_train_execution_result(train_id: str, db: Session = Depends(dependencies.get_db)):
    # TODO get execution details from db or airflow
    pass


@router.get("/docker/configs")
def get_all_docker_train_configs(db: Session = Depends(dependencies.get_db)):
    pass

@router.post("/docker/config")
def add_docker_train_configuration(db: Session = Depends(dependencies.get_db)):
    pass


@router.put("/docker/config/{config_id}")
def update_docker_train_configuration(config_id: int, db: Session = Depends(dependencies.get_db)):
    pass


@router.get("/docker/config/{config_id}")
def get_docker_train_configuration(train_id: int, db: Session = Depends(dependencies.get_db)):
    pass
