from sqlalchemy.orm import Session
from typing import List, Union, Dict, Any, Optional
from datetime import datetime

from .base import CRUDBase, CreateSchemaType, ModelType, UpdateSchemaType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig
from station.app.schemas.docker_trains import DockerTrainConfigCreate, DockerTrainConfigUpdate, DockerTrainConfigBase
from dateutil import parser
from station.app.crud.crud_docker_trains import docker_train


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

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        db_configs = db.query(DockerTrainConfig).offset(skip).limit(limit).all()
        return db_configs

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
