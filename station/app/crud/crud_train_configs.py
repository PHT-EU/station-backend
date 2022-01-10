from sqlalchemy.orm import Session
from typing import Union, Dict, Any
from datetime import datetime

from .base import CRUDBase, ModelType, UpdateSchemaType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig
from station.app.schemas.docker_trains import DockerTrainConfigCreate, DockerTrainConfigUpdate
from station.app.crud import docker_trains


class CRUDDockerTrainConfig(CRUDBase[DockerTrainConfig, DockerTrainConfigCreate, DockerTrainConfigUpdate]):

    def create(self, db: Session, *, obj_in: DockerTrainConfigCreate) -> DockerTrainConfig:
        db_config = DockerTrainConfig(
            name=obj_in.name,
            airflow_config=obj_in.airflow_config.dict() if obj_in.airflow_config else None,
            gpu_requirements=obj_in.gpu_requirements,
            cpu_requirements=obj_in.cpu_requirements,
            auto_execute=obj_in.auto_execute
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config

    def assign_to_train(self, db: Session, train_id: str, config_id: int) -> DockerTrain:
        train = docker_trains.get_by_train_id(db, train_id)
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
