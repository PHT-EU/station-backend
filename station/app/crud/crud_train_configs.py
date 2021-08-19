from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .base import CRUDBase, CreateSchemaType, ModelType, UpdateSchemaType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig
from station.app.schemas.docker_trains import DockerTrainConfigCreate, DockerTrainConfigUpdate, DockerTrainConfigBase
from dateutil import parser

class CRUDDockerTrainConfig(CRUDBase[DockerTrainConfigBase, DockerTrainConfigCreate, DockerTrainConfigUpdate]):

    def get_by_train_id(self, db: Session, train_id: str) -> DockerTrainConfig:
        train = db.query(DockerTrain).filter(DockerTrain.train_id == train_id).first()
        config_id = train.config_id
        config = db.query(DockerTrainConfig).filter(DockerTrainConfig.id == config_id).first()
        return config

    def assign_to_train(self, db: Session, train_id: str, config_id: int) -> DockerTrain:
        train = db.query(DockerTrain).filter(DockerTrain.train_id == train_id).first()
        train.config_id = config_id
        return train

    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj = super().update(db, db_obj=db_obj, obj_in=obj_in)
        setattr(obj, updated_at, datetime.now())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


docker_train_config = CRUDDockerTrainConfig(DockerTrainConfigBase)
