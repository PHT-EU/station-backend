import datetime
from typing import Any, List

import requests
from sqlalchemy.orm import Session
import os

from .advertise_keys import advertise_keys
from .messages.share_keys import ShareKeysMessage
from .primitives.keys import ProtocolKeys
from .primitives.secret_sharing import create_random_seed_and_shares
from .share_keys import share_keys
from station.app.crud import federated_trains
from station.app.models.train import TrainState, Train
from ..schemas.protocol import BroadCastKeysSchema, StationKeys


class AggregationProtocolClient:

    def __init__(self, db: Session, conductor_url: str = None, station_id: Any = None):
        self.db = db
        self.conductor_url = conductor_url if conductor_url else os.getenv("CONDUCTOR_URL")
        self.station_id = station_id if station_id else os.getenv("STATION_ID")

        if not self.conductor_url:
            raise EnvironmentError("Conductor url not specified.")

        if not self.station_id:
            raise EnvironmentError("Station ID not specified.")

    def execute_protocol_for_train(self, train_id: int) -> TrainState:
        db_train = federated_trains.get(self.db, train_id)
        if not db_train:
            raise ProtocolError(f"Train {train_id} does not exist in the database")
        protocol_round = db_train.state.round

        if protocol_round == 0:
            self.setup_protocol(train_id)
            state = self.advertise_keys(train_id)
        elif protocol_round == 1:
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

    def advertise_keys(self, train_id: Any) -> TrainState:
        train_state = advertise_keys(self.db, train_id, self.station_id, self.conductor_url)
        return train_state

    def share_keys(self, train_id: Any) -> dict:
        broadcast = self._get_key_broadcast(train_id)
        state = federated_trains.update_train_with_key_broadcast(self.db, train_id, broadcast)

        share_keys_message = self._make_share_keys_message(state, broadcast)
        response = self._upload_key_shares(train_id=train_id, msg=share_keys_message)
        return response

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

    def _register_for_train(self, station_id: Any, train_id: str):
        r = requests.post(self.conductor_url + f"/api/trains/{train_id}/register",
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

    @staticmethod
    def upload_masked_input(db: Session, train_id: Any):
        pass

    @staticmethod
    def upload_unmasking_shares(db: Session, train_id: Any):
        pass

    def _get_key_broadcast(self, train_id: int):
        r = requests.get(self.conductor_url + f"/api/trains/{train_id}/broadcastKeys")
        r.raise_for_status()
        broadcast = BroadCastKeysSchema(**r.json())

        # Check that all keys are unique
        self._validate_key_broadcast(broadcast.keys)

        return broadcast

    def _make_share_keys_message(self, state: TrainState, broadcast_message: BroadCastKeysSchema):
        n_participants = len(broadcast_message.keys)
        seed, seed_shares = create_random_seed_and_shares(n_participants)

        # update train state with seed
        state.seed = seed
        self.db.commit()
        self.db.refresh(state)

        keys = ProtocolKeys(state.signing_key, state.sharing_key)

        # create key shares from sharing key
        # todo add threshold value from config
        key_shares = keys.create_key_shares(n=n_participants)

        msg = ShareKeysMessage(self.db, state.signing_key, broadcast_message.keys, seed_shares, key_shares,
                               state.iteration)

        return msg

    def _upload_key_shares(self, train_id: Any, msg: ShareKeysMessage):
        r = requests.post(self.conductor_url + f"/api/trains/{train_id}/shareKeys", json=msg.serialize(format="dict"))
        r.raise_for_status()

        return r.json()

    @staticmethod
    def _validate_key_broadcast(keys: List[StationKeys], threshold: int = 3):
        if threshold:
            assert len(keys) >= threshold

        def _all_unique(x):
            seen = list()
            return not any(i in seen or seen.append(i) for i in x)

        signing_keys = [sk.signing_key for sk in keys]
        sharing_keys = [sk.sharing_key for sk in keys]
        # Check that all public keys are unique
        if not _all_unique(signing_keys):
            raise ProtocolError("Duplicate signing keys.")
        if not _all_unique(sharing_keys):
            raise ProtocolError("Duplicate sharing keys.")


class ProtocolError(Exception):
    pass
