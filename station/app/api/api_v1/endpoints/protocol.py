import logging
from typing import Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, Body, Depends, HTTPException
import os

from station.app.api import dependencies
from station.app.protocol import execute_protocol
from station.app.schemas.trains import Train, TrainState
from station.app.schemas.protocol import BroadCastKeysSchema
from station.app.crud.train import read_train, update_train_state_with_key_broadcast
from station.app.protocol import share_keys, masked_input_collection, AggregationProtocolClient

router = APIRouter()


@router.post("/trains/{train_id}/protocol")
def perform_protocol(train_id: int, db: Session = Depends(dependencies.get_db)) -> Any:
    """
    Convenience endpoint for executing the next protocol round based on the db state

    """
    logging.info(f"Executing Protocol for Train: {train_id}")
    train = read_train(db, train_id)

    if not train:
        raise HTTPException(status_code=403, detail="Train does not exist")

    protocol = AggregationProtocolClient(db)

    protocol.execute_protocol_for_train(train_id=str(train_id))


    # response = execute_protocol(db, str(train_id))
    # print(response)


@router.get("/trains/{train_id}/protocol")
def get_protocol_state(train_id: int, db: Session = Depends(dependencies.get_db)) -> Any:
    """
    Show the current state of the aggregation for the selected train

    """
    pass


@router.get("/trains/{train_id}/keyBroadcasts", response_model=BroadCastKeysSchema)
def get_key_broadcast_from_conductor(train_id: int, db: Session = Depends(dependencies.get_db)) -> Any:
    broadcast = share_keys.get_broad_casted_keys(train_id)
    state = update_train_state_with_key_broadcast(db, train_id, broadcast)
    return broadcast


@router.post("/trains/{train_id}/maskedInputCollection")
def get_cyphers_from_conductor(train_id: int, db: Session = Depends(dependencies.get_db)) -> Any:
    cyphers = masked_input_collection.compute_masked_input_vector(db, train_id)




