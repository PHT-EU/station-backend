from sqlalchemy.orm import Session
from datetime import datetime
import json
from typing import List, Any
import os

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig
from station.app.schemas.docker_trains import DockerTrainCreate


def create_train(db: Session, create_msg: DockerTrainCreate) -> DockerTrain:
    db_train = DockerTrain(train_id=create_msg.train_id,
                           proposal_id=create_msg.proposal_id,
                           config_id=create_msg.config_id)

    if create_msg.config_name:
        # TODO get config by name
        pass
    db.add(db_train)
    db.commit()
    db.refresh(db_train)
    return db_train


def read_train(db: Session, id: int) -> DockerTrain:
    return db.query(DockerTrain).get(id)


def read_trains(db: Session, limit: int, active: bool = None) -> List[DockerTrain]:
    if active:
        # Get only currently active trains
        if limit != 0:
            db_trains = db.query(DockerTrain).filter(DockerTrain.is_active == True).limit(limit).all()
        else:
            db_trains = db.query(DockerTrain).filter(DockerTrain.is_active == True).all()
    else:
        # get all trains
        if limit != 0:
            db_trains = db.query(DockerTrain).limit(limit).all()
        else:
            db_trains = db.query(DockerTrain).all()
    return db_trains


def read_train_by_train_id(db: Session, train_id: Any) -> DockerTrain:
    db_train = db.query(DockerTrain).filter(DockerTrain.train_id == train_id).first()
    return db_train


def update_train_with_execution(db: Session, train_id: Any, run_id: str) -> DockerTrain:
    db_train = read_train_by_train_id(db, train_id)
    db_train.updated_at = datetime.now()
    db_train.last_execution = run_id
    db_train.is_active = True
    db.commit()
    db.refresh(db_train)
    return db_train


def read_train_config(db: Session, id: int) -> DockerTrainConfig:
    return db.query(DockerTrainConfig).get(id)
