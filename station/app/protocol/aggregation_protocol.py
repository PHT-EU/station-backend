import datetime
from typing import Any

import requests
from sqlalchemy.orm import Session
import os

from .advertise_keys import advertise_keys
from .primitives.keys import ProtocolKeys
from .share_keys import share_keys
from station.app.crud import federated_trains
from station.app.models.train import TrainState, Train


class AggregationProtocolClient:

    def __init__(self, db: Session):
        self.db = db

    def execute_protocol_for_train(self, train_id: int) -> TrainState:
        db_train = federated_trains.get(self.db, train_id)
        if not db_train:
            raise ProtocolError(f"Train {train_id} does not exist in the database")
        round = db_train.state.round
        iteration = db_train.state.iteration

        if round == 0:
            self.setup_protocol(train_id)
            state = self.advertise_keys(train_id)
        elif round == 1:
            state = self.share_keys(train_id)

        self.db.refresh(db_train)
        return db_train.state

    def initialize_train(self, name: Any, station_id: Any = None) -> Train:
        # register train at conductor
        if not station_id:
            station_id = os.getenv("STATION_ID")

        if not station_id:
            raise EnvironmentError("Station ID not defined")

        token = self._register_for_train(station_id, name)
        train = self._initialize_db_train(name, token)

        return train

    def setup_protocol(self, train_id: Any):
        db_train = federated_trains.get(self.db, id=train_id)
        assert db_train
        db_train.is_active = True

        state = db_train.state
        keys = ProtocolKeys()
        self._update_db_after_setup(state, keys.hex_signing_key, keys.hex_sharing_key)

    def _initialize_db_train(self, name, token: str, proposal_id: Any = None) -> Train:
        db_train = Train(proposal_id=proposal_id, token=token, name=name)
        self.db.add(db_train)
        self.db.commit()
        self.db.refresh(db_train)

        # Initialize train state
        db_train_state = TrainState(train_id=db_train.id)
        self.db.add(db_train_state)
        self.db.commit()

        return db_train

    @staticmethod
    def _register_for_train(station_id: Any, train_id: str, conductor_url: str = None):
        if not conductor_url:
            conductor_url = os.getenv("CONDUCTOR_URL")

        if not conductor_url:
            raise EnvironmentError("Conductor Url not defined.")
        r = requests.post(conductor_url + f"/api/trains/{train_id}/register",
                          params={"station_id": os.getenv("STATION_ID", station_id)})
        r.raise_for_status()
        token = r.json()["token"]
        return token

    def _update_db_after_setup(self, state: TrainState, signing_key: str, sharing_key: str):
        # set train to active
        state.signing_key = signing_key
        state.sharing_key = sharing_key

        state.updated_at = datetime.datetime.now()
        self.db.commit()

    def advertise_keys(self, train_id: Any) -> TrainState:
        station_id = os.getenv("STATION_ID")
        conductor_url = os.getenv("CONDUCTOR_URL")
        train_state = advertise_keys(self.db, train_id, station_id, conductor_url)
        return train_state

    @staticmethod
    def share_keys(db: Session, train_id: Any) -> TrainState:
        response = share_keys(db, train_id)
        state = federated_trains.get(db=db, id=train_id).state
        return state

    @staticmethod
    def upload_masked_input(db: Session, train_id: Any):
        pass

    @staticmethod
    def upload_unmasking_shares(db: Session, train_id: Any):
        pass


class ProtocolError(Exception):
    pass
