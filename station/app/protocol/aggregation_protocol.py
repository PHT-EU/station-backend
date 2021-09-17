import datetime
from typing import Any, List

import requests
from sqlalchemy.orm import Session
import os

from .advertise_keys import advertise_keys
from .messages import AdvertiseKeysMessage
from .messages.share_keys import ShareKeysMessage
from .primitives.keys import ProtocolKeys
from .primitives.secret_sharing import create_random_seed_and_shares
from .share_keys import share_keys
from station.app.crud import federated_trains
from station.app.models.train import TrainState, Train
from ..models.protocol import Cypher
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
        """
        Executes the protocol for a train with the given id based on the state stored in the database

        Args:
            train_id:

        Returns:

        """

        db_train = federated_trains.get(self.db, train_id)
        if not db_train:
            raise ProtocolError(f"Train {train_id} does not exist in the database")
        protocol_round = db_train.state.round
        print(f"Executing round {protocol_round} of the protocol for train {train_id}")
        if protocol_round == 0:

            self.setup_protocol(train_id)
            state = self.advertise_keys(train_id)
        elif protocol_round == 1:
            state = self.share_keys(train_id)

        elif protocol_round == 2:
            state = self.submit_masked_input(train_id)

        self.db.refresh(db_train)
        return db_train.state

    def initialize_train(self, name: Any, station_id: Any = None) -> Train:
        """
        Attempts to join a train specified by the name at the conductor, if the registration is successful a new
        train will be created in the database

        Args:
            name: train name to query the conductor with
            station_id: optional station id parameter will be loaded from env vars

        Returns:

        """
        # register train at conductor
        if not station_id:
            station_id = os.getenv("STATION_ID")

        if not station_id:
            raise EnvironmentError("Station ID not defined")

        token = self._register_for_train(station_id, name)
        train = self._initialize_db_train(name, token)

        return train

    def setup_protocol(self, train_id: Any):
        """
        Sets up a new round of the protocol by generating a new set of EC keys and storing the private keys in the db

        Args:
            train_id: train_id to create keys for

        Returns:

        """

        db_train = federated_trains.get(self.db, id=train_id)
        assert db_train
        db_train.is_active = True

        state = db_train.state
        keys = ProtocolKeys()
        self._update_db_after_setup(state, keys.hex_signing_key, keys.hex_sharing_key)

    def advertise_keys(self, train_id: Any) -> TrainState:
        """
        Perform the initial communication round of the aggregation protocol, where the station creates a new set
        of keys and advertises these keys to the aggregation server.

        Args:
            train_id: train id to advertise keys for

        Returns:
            state of the train after advertising the keys to the conductor
        """

        train = federated_trains.get(self.db, train_id)

        # initialize keys from db
        keys = ProtocolKeys(signing_key=train.state.signing_key, sharing_key=train.state.sharing_key)

        # Create a key advertisement message containing the public keys of the previously generated private keys
        msg = AdvertiseKeysMessage(
            station_id=self.station_id,
            train_id=train_id,
            iteration=train.state.iteration,
            signing_key=keys.signing_key_public,
            sharing_key=keys.sharing_key_public
        )

        # send the message to the server
        response = requests.post(self.conductor_url + f"/api/trains/{train_id}/advertiseKeys", json=msg.serialize())
        response.raise_for_status()

        # update state
        train.state.round = 1
        train.state.updated_at = datetime.datetime.now()

        self.db.commit()
        self.db.refresh(train.state)
        return train.state

    def share_keys(self, train_id: Any) -> dict:
        """
        Perform the second communication round of the aggregation protocol, where shares of the private sharing key
        are created with shamir's secret sharing and signed with the public keys received in the key broadcast from
        the conductor node

        Args:
            train_id: train id whose keys to share

        Returns:
            conductor response to the share keys message
        """
        broadcast = self._get_key_broadcast(train_id)
        state = federated_trains.update_train_with_key_broadcast(self.db, train_id, broadcast)

        share_keys_message = self._make_share_keys_message(state, broadcast)
        response = self._upload_key_shares(train_id=train_id, msg=share_keys_message)

        state.round = 2
        self.db.commit()

        return response

    def submit_masked_input(self, train_id):
        participants = self.get_cyphers(train_id)

    def get_cyphers(self, train_id):

        db_train = federated_trains.get(self.db, train_id)
        state = db_train.state

        data = {
            "station_id": os.getenv("STATION_ID"),
            "iteration": state.iteration
        }

        r = requests.post(self.conductor_url + f"/api/trains/{train_id}/cyphers", json=data)
        print(r.text)
        r.raise_for_status()
        other_participants = self._process_cyphers(r.json(), db_train.id, state.iteration)
        print("other participants", other_participants)
        return other_participants

    def _process_cyphers(self, cyphers: list, train_id: int, iteration: int):
        # Parse the cyphers from the message and store them in database with train_id and iteration
        participants_round_2 = []
        for cypher_msg in cyphers:
            if cypher_msg["sender"] != int(os.getenv("STATION_ID")):
                db_cypher = Cypher(
                    train_id=train_id,
                    iteration=iteration,
                    station_id=cypher_msg["sender"],
                    cypher=cypher_msg["cypher"]
                )
                self.db.add(db_cypher)
                participants_round_2.append(cypher_msg["sender"])
        self.db.commit()
        return participants_round_2


    def _load_input_data(self, train_id):
        pass


    def _initialize_db_train(self, name, token: str, proposal_id: Any = None) -> Train:
        """
        Create a new train object in the database, as well as the associated empty default state.

        Args:
            name: name of the train
            token: token received from registering for the train at the conductor node
            proposal_id: id of the proposal the train is associated with

        Returns:
            Train object submitted to the database
        """
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
        """
        Register this station at for the given train

        Args:
            station_id: station id
            train_id: identifier of the train to register for

        Returns:
            token for accessing the train in the future
        """
        r = requests.post(self.conductor_url + f"/api/trains/{train_id}/register",
                          params={"station_id": os.getenv("STATION_ID", station_id)})
        r.raise_for_status()
        token = r.json()["token"]
        return token

    def _update_db_after_setup(self, state: TrainState, signing_key: str, sharing_key: str):
        """
        Update the state in the database after initializing the keys for this iteration

        Args:
            state: train state from the database
            signing_key: hex representation of the private signing key
            sharing_key: hex representation of the private sharing key

        Returns:

        """
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

    def _get_key_broadcast(self, train_id: int) -> BroadCastKeysSchema:
        """
        Query the key broadcast for the given train from the conductor and validate the received keys

        Args:
            train_id: identifier of the train

        Returns:
            key broadcast message from the conductor

        """

        r = requests.get(self.conductor_url + f"/api/trains/{train_id}/broadcastKeys")
        r.raise_for_status()
        broadcast = BroadCastKeysSchema(**r.json())

        # Check that all keys are unique
        self._validate_key_broadcast(broadcast.keys)

        return broadcast

    def _make_share_keys_message(self, state: TrainState, broadcast_message: BroadCastKeysSchema) -> ShareKeysMessage:
        """
        Create a message containing key shares based on a key broadcast received from the conductor

        Args:
            state: database state of the train
            broadcast_message: key broadcast received from the conductor

        Returns:
            Share keys message to be send to the condcutor

        """
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
        """
        Send a share keys message to the conductor and return the response

        Args:
            train_id: train identifier
            msg: share keys message to be send to the conductor

        Returns:
            the conductors response to the share keys message (state of the train at the conductor)

        """
        r = requests.post(self.conductor_url + f"/api/trains/{train_id}/shareKeys", json=msg.serialize(format="dict"))
        r.raise_for_status()

        return r.json()

    @staticmethod
    def _validate_key_broadcast(keys: List[StationKeys], threshold: int = 3):
        """
        Validate the keys received in a key broadcast from the conductor by asserting that they are all unique and
        at least t keys are available

        Args:
            keys: list of key pairs received from the conductor
            threshold: minimum number of keys required

        Returns:

        """

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
