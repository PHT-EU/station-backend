from builtins import str

from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from dateutil import parser

from .base import CRUDBase, ModelType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig, DockerTrainState
from station.app.schemas.docker_trains import DockerTrainCreate, DockerTrainUpdate, DockerTrainConfigCreate
from station.app.schemas.docker_trains import DockerTrainState as DockerTrainStateSchema


# TODO improve handling of proposals

class CRUDDockerTrain(CRUDBase[DockerTrain, DockerTrainCreate, DockerTrainUpdate]):

    def create(self, db: Session, *, obj_in: DockerTrainCreate) -> ModelType:

        if isinstance(obj_in.config, int):
            db_config = db.query(DockerTrainConfig).filter(DockerTrainConfig.id == obj_in.config).first()
            if not db_config:
                raise HTTPException(status_code=404, detail=f"Config {obj_in.config} not found")
            config_id = db_config.id

        elif isinstance(obj_in.config, DockerTrainConfigCreate):
            print("CASE DOCKERTRAIN CREATE")
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
        print("DOCKER TRAIN OBJECT CREATED")
        db.add(db_train)
        db.commit()
        db.refresh(db_train)
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

    # todo maybe remove for new solution by tyra
    def add_if_not_exists(self, db: Session, train_id: str, created_at: str = None):
        db_train = self.get_by_train_id(db, train_id)
        if not db_train:
            db_train = DockerTrain(train_id=train_id, created_at=parser.parse(created_at))
            db.add(db_train)
            train_state = DockerTrainState(train_id=db_train.id)
            db.add(train_state)
            db.commit()

    def read_train_state(self, db: Session, train_id: str) -> DockerTrainState:
        db_train = self.get_by_train_id(db, train_id)
        if not db_train:
            raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
        state = db_train.state
        return state

    def update_train_state(self, db: Session, train_id: str, state_in: DockerTrainStateSchema) -> DockerTrainState:
        db_state = self.read_train_state(db, train_id)
        if not db_state:
            raise HTTPException(status_code=404, detail=f"Train State for train: {train_id} not found")
        db_state.num_executions = state_in.num_executions
        db_state.last_execution = state_in.last_execution
        db_state.status = state_in.status

        db.commit()
        db.refresh(db_state)

        return db_state


docker_trains = CRUDDockerTrain(DockerTrain)
