from sqlalchemy.orm import Session

from .base import CRUDBase
from typing import List, Any, Tuple

from station.app.models.train import Train, TrainState
from station.app.schemas.trains import TrainCreate, TrainUpdate


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


trains = CRUDTrain(Train)
