from sqlalchemy.orm import Session
from typing import List

from .base import CRUDBase, CreateSchemaType, ModelType

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

docker_trainConfig = CRUDDockerTrainConfig(DockerTrainConfigBase)
