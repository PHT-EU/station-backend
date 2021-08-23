from sqlalchemy.orm import Session
import os

from .base import CRUDBase
from typing import List, Any, Tuple

from station.app.models.train import Train, TrainState
from station.app.schemas.trains import TrainCreate, TrainUpdate
from station.app.schemas.protocol import BroadCastKeysSchema
from station.app.models.protocol import BroadCastKeys


class CRUDTrain(CRUDBase[Train, TrainCreate, TrainUpdate]):
    def get_by_train_id(self, db: Session, train_id: str) -> Train:
        return db.query(Train).filter(Train.train_id == train_id).first()

    def get_trains_by_active_status(self, db: Session, active=True):
        return db.query(Train).filter(Train.is_active == active).all()

    def sync_local_trains_with_conductor(self, db: Session, conductor_trains: List[dict]) -> \
            Tuple[List[Train], List[Train]]:

        updated_trains = []
        new_trains = []
        for conductor_train in conductor_trains:
            if self.get_by_train_id(db, str(conductor_train["id"])):
                # TODO check for available updates and process them
                print("Found existing train")
            else:
                # create a new train
                db_train = self._create_train_from_conductor(db, conductor_train)
                print(f"Creating new train")
                new_trains.append(db_train)

        return updated_trains, new_trains

    def _create_train_from_conductor(self, db: Session, conductor_train: dict) -> Train:

        db_train = self.model(
            train_id=conductor_train["id"],
            proposal_id=conductor_train["proposal_id"]
        )
        db.add(db_train)
        db.commit()
        db.refresh(db_train)
        db_train_state = TrainState(train_id=db_train.id)
        db.add(db_train_state)
        db.commit()
        db.refresh(db_train_state)

        return db_train

    def update_train_with_key_broadcast(self, db: Session, train_id: int,
                                        key_broadcast: BroadCastKeysSchema) -> TrainState:
        db_train = self.get(db, id=train_id)
        assert db_train
        db_train_state: TrainState = db.query(TrainState).filter(TrainState.train_id == train_id).first()
        for key_pair in key_broadcast.keys:
            if key_pair.station_id != int(os.getenv("STATION_ID")):
                db_broadcast = BroadCastKeys(
                    train_id=db_train.id,
                    iteration=db_train_state.iteration,
                    **key_pair.dict()
                )
                db.add(db_broadcast)
        db_train_state.key_broadcast = key_broadcast.json()
        db_train_state.round = 2
        db.commit()
        db.refresh(db_train_state)

        return db_train_state


trains = CRUDTrain(Train)
