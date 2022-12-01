from builtins import str

from sqlalchemy.orm import Session
from typing import List, Tuple, Union
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from dateutil import parser
from datetime import datetime

from .base import CRUDBase, ModelType

from station.app.models.docker_trains import DockerTrain, DockerTrainConfig, DockerTrainState, DockerTrainExecution
from station.app.schemas.docker_trains import DockerTrainCreate, DockerTrainUpdate, DockerTrainConfigCreate
from station.app.schemas.docker_trains import DockerTrainState as DockerTrainStateSchema
from station.app.config import settings

# TODO improve handling of proposals
from ...clients.central.central_client import CentralApiClient


class CRUDDockerTrain(CRUDBase[DockerTrain, DockerTrainCreate, DockerTrainUpdate]):

    def create(self, db: Session, *, obj_in: DockerTrainCreate) -> ModelType:

        if isinstance(obj_in.config, int):
            db_config = db.query(DockerTrainConfig).filter(DockerTrainConfig.id == obj_in.config).first()
            if not db_config:
                raise HTTPException(status_code=404, detail=f"Config {obj_in.config} not found")
            config_id = db_config.id

        elif isinstance(obj_in.config, DockerTrainConfigCreate):
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

    def delete_by_train_id(self, db: Session, train_id: str) -> DockerTrain:
        db_train = self.get_by_train_id(db, train_id)
        if not db_train:
            raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
        db.delete(db_train)
        db.commit()
        return db_train

    def add_if_not_exists(self, db: Session, train_id: str, created_at: str = datetime.now(), updated_at: str = None):
        db_train = self.get_by_train_id(db, train_id)
        if not db_train:
            if updated_at:
                db_train = DockerTrain(train_id=train_id, created_at=parser.parse(created_at),
                                       updated_at=parser.parse(updated_at))
            else:
                db_train = DockerTrain(train_id=train_id, created_at=parser.parse(created_at))
            db.add(db_train)
            db.commit()
            db.refresh(db_train)
            train_state = DockerTrainState(train_id=db_train.id)
            db.add(train_state)
            db.commit()
            return db_train

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

    def get_train_executions(self, db: Session, train_id: str) -> DockerTrainExecution:
        db_train = self.get_by_train_id(db, train_id)
        if not db_train:
            raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
        executions = db_train.executions
        return executions

    def get_executions(self, db: Session, skip: int = 0, limit: int = 100) -> List[DockerTrainExecution]:
        return db.query(DockerTrainExecution).order_by(DockerTrainExecution.start.desc()).offset(skip).limit(limit).all()

    def synchronize_central(self, db: Session) -> List[DockerTrain]:
        client = CentralApiClient(
            api_url=settings.config.central_ui.api_url,
            robot_id=settings.config.central_ui.robot_id,
            robot_secret=settings.config.central_ui.robot_secret
        )
        central_trains = client.get_trains(settings.config.station_id)
        train_objects = []
        for train in central_trains["data"]:
            if train["approval_status"] == "approved":
                db_train = self._parse_central_api_train(db, train_dict=train)
                if db_train:
                    train_objects.append(db_train)
        if train_objects:
            trains, train_states = zip(*train_objects)
        else:
            return []
        return trains

    def _parse_central_api_train(self,
                                 db: Session,
                                 train_dict: dict) -> Union[None, Tuple[DockerTrain, DockerTrainState]]:
        db_train = self.get_by_train_id(db, train_dict["train_id"])
        if db_train:
            # todo update existing train
            return None
        else:
            db_train = self._db_train_from_central_api(train_dict)
            db.add(db_train)
            db.commit()
            db.refresh(db_train)

            db_state = self._train_state_from_central(db_train.id, train_dict)
            db.add(db_state)
            db.commit()
            db.refresh(db_state)

            return db_train, db_state

    def _db_train_from_central_api(self, train_dict: dict) -> DockerTrain:

        image_name = self._make_train_image_name(train_dict)
        proposal_link = self._make_train_proposal_link(train_dict)
        db_train = DockerTrain(
            train_id=train_dict["train_id"],
            created_at=parser.parse(train_dict["created_at"]),
            updated_at=parser.parse(train_dict["updated_at"]),
            proposal=proposal_link,
            type=train_dict["train"]["type"],
            name=train_dict["train"]["name"],
            num_participants=train_dict["train"]["stations"],
            image_name=image_name,

        )
        return db_train

    @staticmethod
    def _make_train_image_name(train_dict: dict) -> str:

        tag = train_dict["artifact_tag"]
        if not tag:
            tag = "latest"
        image_name = '{}/{}/{}:{}'.format(
            settings.config.registry.address,
            settings.config.registry.project,
            train_dict["train_id"],
            tag
        )
        return image_name

    @staticmethod
    def _train_state_from_central(train_id: int, train_dict: dict) -> DockerTrainState:
        state = DockerTrainState(
            train_id=train_id,
            central_status=train_dict["run_status"],
        )
        return state

    @staticmethod
    def _make_train_proposal_link(train_dict: dict):
        proposal_id = train_dict["train"]["proposal_id"]

        central_path = settings.config.central_ui.api_url
        if central_path.endswith("/api"):
            central_path = central_path[:-4]
        proposal_link = f"{central_path}/proposals/{proposal_id}"
        return proposal_link


docker_trains = CRUDDockerTrain(DockerTrain)
