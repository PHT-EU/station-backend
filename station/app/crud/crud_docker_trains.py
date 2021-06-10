from sqlalchemy.orm import Session
from typing import List

from .base import CRUDBase, CreateSchemaType, ModelType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig, DockerTrainState
from station.app.schemas.docker_trains import DockerTrainCreate, DockerTrainUpdate, DockerTrainConfigCreate, \
    DockerTrainConfigUpdate
from dateutil import parser


# TODO improve handling of proposals

class CRUDDockerTrain(CRUDBase[DockerTrain, DockerTrainCreate, DockerTrainUpdate]):

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        db_train = super().create(db, obj_in=obj_in)
        train_state = DockerTrainState(train_id=db_train.id)
        db.add(train_state)
        db.commit()

        return db_train

    def get_by_train_id(self, db: Session, train_id: str) -> DockerTrain:
        return db.query(DockerTrain).filter(DockerTrain.train_id == train_id).first()

    def get_trains_by_active_status(self, db: Session, active=True) -> List[DockerTrain]:
        return db.query(DockerTrain).filter(DockerTrain.is_active == active).all()

    def add_if_not_exists(self, db: Session, train_id: str, created_at: str = None):
        db_train = self.get_by_train_id(db, train_id)
        if not db_train:
            db_train = DockerTrain(train_id=train_id, created_at=parser.parse(created_at))
            db.add(db_train)
            train_state = DockerTrainState(train_id=db_train.id)
            db.add(train_state)
            db.commit()


docker_train = CRUDDockerTrain(DockerTrain)
