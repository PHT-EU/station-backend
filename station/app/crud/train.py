from sqlalchemy.orm import Session
from datetime import datetime
import json
from typing import List
import os

from station.app.models.train import Train, TrainState
from station.app.models.protocol import BroadCastKeys
from station.app.schemas.protocol import BroadCastKeysSchema

from station.app.crud import federated_trains


def read_train(db: Session, train_id: int) -> Train:
    db_train = db.query(Train).get(train_id)
    return db_train


def create_train(db: Session, proposal_id: int, token: str):
    db_train = Train(proposal_id=proposal_id, token=token)
    db.add(db_train)
    db.commit()
    db.refresh(db_train)

    # Initialize train state
    db_train_state = TrainState(train_id=db_train.id)
    db.add(db_train_state)
    db.commit()
    return db_train


def read_train_state(db: Session, train_id: int) -> TrainState:
    db_train_state = db.query(TrainState).filter(TrainState.train_id == train_id).first()
    return db_train_state


def update_rng_seed(db: Session, train_id: str, seed: int):
    db_train = federated_trains.get(db, train_id)
    db_train_state: TrainState = db.query(TrainState).filter(TrainState.train_id == db_train.id).first()
    db_train_state.seed = seed
    db.commit()
    db.refresh(db_train_state)
    return db_train_state


# TODO move to protocol/refactor
def update_train_state_with_key_broadcast(db: Session, train_id: str, broadcast: BroadCastKeysSchema) -> TrainState:
    db_train = federated_trains.get_by_train_id(db, train_id)
    db_train_state: TrainState = db.query(TrainState).filter(TrainState.train_id == train_id).first()

    for key_pair in broadcast.keys:
        if key_pair.station_id != int(os.getenv("STATION_ID")):
            db_broadcast = BroadCastKeys(
                train_id=db_train.id,
                iteration=db_train_state.iteration,
                **key_pair.dict()
            )
            db.add(db_broadcast)
    db_train_state.key_broadcast = broadcast.json()
    db.commit()
    db.refresh(db_train_state)
    return db_train_state


def update_train_round_0(db: Session, train_id: str, signing_key: str, sharing_key: str, iteration: int):
    # set train to active
    db_train: Train = federated_trains.get(db, train_id)
    db_train.is_active = True
    # Update train state
    db_train_state: TrainState = db.query(TrainState).filter(TrainState.train_id == db_train.id).first()

    db_train_state.signing_key = signing_key
    db_train_state.sharing_key = sharing_key
    db_train_state.updated_at = datetime.now()
    db_train_state.iteration = iteration

    db.commit()
    db.refresh(db_train_state)

    return db_train_state


def get_train_sharing_key(db: Session, train_id: int):
    db_train_state: TrainState = db.query(TrainState).filter(TrainState.train_id == train_id).first()
    return db_train_state.sharing_key


def get_train_signing_key(db: Session, train_id: int):
    db_train_state: TrainState = db.query(TrainState).filter(TrainState.train_id == train_id).first()
    return db_train_state.signing_key
