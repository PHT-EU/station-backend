from typing import Any
from sqlalchemy.orm import Session
import os

from .setup import setup_protocol
from .advertise_keys import advertise_keys
from .share_keys import share_keys
from station.app.crud import trains
from station.app.models.train import TrainState


class AggregationProtocol:

    def execute_protocol(self, db: Session, train_id: Any):
        db_train = trains.get_by_train_id(db, train_id)
        if not db_train:
            raise ValueError(f"Train {train_id} does not exist in the database")

        round = db_train.state.round

        if round == 0:
            state = self.advertise_keys(db, train_id)
        elif round == 1:
            state = self.share_keys(db, train_id)




    @staticmethod
    def setup_protocol(db: Session, train_id: Any):
        db_train = trains.get_by_train_id(db, train_id=train_id)
        assert db_train
        iteration = db_train.state.iteration
        signing_pk, sharing_pk = setup_protocol(db, train_id, iteration)
        # TODO is this necessary?

    @staticmethod
    def advertise_keys(db: Session, train_id: Any) -> TrainState:
        station_id = os.getenv("STATION_ID")
        conductor_url = os.getenv("CONDUCTOR_URL")
        train_state = advertise_keys(db, train_id, station_id, conductor_url)
        return train_state

    @staticmethod
    def share_keys(db: Session, train_id: Any):
        response = share_keys(db, train_id)
        return response

    @staticmethod
    def upload_masked_input(db: Session, train_id: Any):
        pass

    @staticmethod
    def upload_unmasking_shares(db: Session, train_id: Any):
        pass
