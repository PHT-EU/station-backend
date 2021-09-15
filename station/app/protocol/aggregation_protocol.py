from typing import Any

import requests
from cryptography.hazmat.primitives import serialization
from sqlalchemy.orm import Session
import os
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKeyWithSerialization as ECPK
from cryptography.hazmat.primitives.asymmetric import ec

from .advertise_keys import advertise_keys
from .share_keys import share_keys
from station.app.crud import trains
from station.app.models.train import TrainState, Train


class AggregationProtocolClient:

    def __init__(self, db: Session):
        self.db = db

    def execute_protocol_for_train(self, train_id: Any) -> TrainState:
        db_train = trains.get(self.db, train_id)
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

    @staticmethod
    def _generate_ec_key_pair():
        signing_key = ec.generate_private_key(ec.SECP384R1())
        sharing_key = ec.generate_private_key(ec.SECP384R1())
        signing_key_hex = signing_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).hex()
        sharing_key_hex = sharing_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).hex()

        return signing_key, signing_key.public_key(), sharing_key, sharing_key.public_key(), signing_key_hex, sharing_key_hex

    def setup_protocol(self, train_id: Any):
        db_train = trains.get(self.db, train_id=train_id)
        assert db_train
        db_train.is_active = True

        state = db_train.state
        c_sk, c_pk, s_sk, s_pk, c_sk_hex, s_sk_hex = self._generate_ec_key_pair()
        self._update_db_after_setup(state, c_sk_hex, s_sk_hex)

    def _update_db_after_setup(self, state: TrainState, signing_key: str, sharing_key: str):
        state

    @staticmethod
    def advertise_keys(db: Session, train_id: Any) -> TrainState:
        station_id = os.getenv("STATION_ID")
        conductor_url = os.getenv("CONDUCTOR_URL")
        train_state = advertise_keys(db, train_id, station_id, conductor_url)
        return train_state

    @staticmethod
    def share_keys(db: Session, train_id: Any) -> TrainState:
        response = share_keys(db, train_id)
        state = trains.get(db=db, id=train_id).state
        return state

    @staticmethod
    def upload_masked_input(db: Session, train_id: Any):
        pass

    @staticmethod
    def upload_unmasking_shares(db: Session, train_id: Any):
        pass


class ProtocolError(Exception):
    pass
