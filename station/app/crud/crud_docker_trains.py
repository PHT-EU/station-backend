from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from fastapi import HTTPException

from .base import CRUDBase, CreateSchemaType, ModelType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig, DockerTrainState
from station.app.schemas.docker_trains import DockerTrainCreate, DockerTrainUpdate, DockerTrainConfigCreate, \
    DockerTrainConfigUpdate
from dateutil import parser
from station.app.crud.crud_train_configs import docker_train_config


# TODO improve handling of proposals

class CRUDDockerTrain(CRUDBase[DockerTrain, DockerTrainCreate, DockerTrainUpdate]):

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        if obj_in.config_id:
            try:
               config = docker_train_config.get(db, obj_in.config_id)
               config_id = obj_in.config_id
               if obj_in.config:
                   if config != obj_in.config:
                       raise HTTPException(status_code=400, detail="Saved config differs from specified one")
            except:
                raise HTTPException(status_code=404, detail="Config does not exist")
        elif obj_in.config:
            try:
                new_config = docker_train_config.create(db, obj_in=obj_in.config.dict())
                config_id = new_config.id
                db.add(new_config)
                db.commit()
            except:
                print("Config could not be created")
        db_train = super().create(db, obj_in=obj_in.dict(exclude={'config', 'config_id'}))
        try:
            db_train.config_id = config_id
        except:
            print("Train created without config definition")
        train_state = DockerTrainState(train_id=db_train.id)
        db.add(train_state)
        db.commit()

        return db_train

    def get_by_train_id(self, db: Session, train_id: str) -> DockerTrain:
        return db.query(DockerTrain).filter(DockerTrain.train_id == train_id).first()

    def get_trains_by_active_status(self, db: Session, active=True, limit: int = 0) -> List[DockerTrain]:
        if limit != 0:
            trains = db.query(DockerTrain).filter(DockerTrain.is_active == active).limit(limit).all()
        else:
            trains = db.query(DockerTrain).filter(DockerTrain.is_active == active).all()
        return trains

    def add_if_not_exists(self, db: Session, train_id: str, created_at: str = None):
        db_train = self.get_by_train_id(db, train_id)
        if not db_train:
            db_train = DockerTrain(train_id=train_id, created_at=parser.parse(created_at))
            db.add(db_train)
            train_state = DockerTrainState(train_id=db_train.id)
            db.add(train_state)
            db.commit()


docker_train = CRUDDockerTrain(DockerTrain)
