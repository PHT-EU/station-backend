from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from dateutil import parser

from .base import CRUDBase, ModelType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig, DockerTrainState
from station.app.schemas.docker_trains import DockerTrainCreate, DockerTrainUpdate



# TODO improve handling of proposals

class CRUDDockerTrain(CRUDBase[DockerTrain, DockerTrainCreate, DockerTrainUpdate]):

    def create(self, db: Session, *, obj_in: DockerTrainCreate) -> ModelType:

        if obj_in.config_name:
            db_config: DockerTrainConfig = db.query(DockerTrainConfig).filter(
                DockerTrainConfig.name == obj_in.config_name
            ).first()

            config_id = db_config.id

        elif obj_in.config_id:
            config_id = obj_in.config_id

        elif obj_in.config:
            db_config: DockerTrainConfig = db.query(DockerTrainConfig).filter(
                DockerTrainConfig.name == obj_in.config.name
            ).first()
            if db_config:
                raise HTTPException(status_code=400, detail="A config with the given name already exists.")
            else:
                new_config = DockerTrainConfig(**jsonable_encoder(obj_in.config))
                db.add(new_config)
                db.commit()
                db.refresh(new_config)
                config_id = new_config.id

        else:
            config_id = None

        db_train = DockerTrain(
            train_id=obj_in.train_id,
            config_id=config_id
        )
        db.add(db_train)
        train_state = DockerTrainState(train_id=db_train.id)
        db.add(train_state)
        db.commit()

        db.refresh(db_train)
        return db_train

    def get_by_train_id(self, db: Session, train_id: str) -> DockerTrain:
        train = db.query(DockerTrain).filter(DockerTrain.train_id == train_id).first()
        return train

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
