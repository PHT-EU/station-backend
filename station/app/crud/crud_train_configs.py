from sqlalchemy.orm import Session
from typing import List, Union, Dict, Any
from datetime import datetime

from .base import CRUDBase, CreateSchemaType, ModelType, UpdateSchemaType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig
from station.app.schemas.docker_trains import DockerTrainConfigCreate, DockerTrainConfigUpdate, DockerTrainConfigBase
from dateutil import parser
from station.app.crud.crud_docker_trains import docker_train


class CRUDDockerTrainConfig(CRUDBase[DockerTrainConfig, DockerTrainConfigCreate, DockerTrainConfigUpdate]):

    def get_by_train_id(self, db: Session, train_id: str) -> DockerTrainConfig:
        train = db.query(DockerTrain).filter(DockerTrain.train_id == train_id).first()

        config = train.config
        return config

    def assign_to_train(self, db: Session, train_id: str, config_id: int) -> DockerTrain:
        train = docker_train.get_by_train_id(db, train_id)
        train.config_id = config_id
        train.updated_at = datetime.now()
        db.commit()
        db.refresh(train)
        return train

    def get_by_name(self, db: Session, name: str) -> DockerTrainConfig:
        config = db.query(DockerTrainConfig).filter(
            DockerTrainConfig.name == name
        ).first()
        return config

    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj = super().update(db, db_obj=db_obj, obj_in=obj_in)
        obj.updated_at = datetime.now()
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


docker_train_config = CRUDDockerTrainConfig(DockerTrainConfig)
