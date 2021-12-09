from typing import Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from station.app.api import dependencies
from station.app.crud import federated_trains
from station.app.schemas.protocol import BroadCastKeysSchema
from station.app.crud.train import update_train_state_with_key_broadcast
from station.app.protocol import share_keys, masked_input_collection, AggregationProtocolClient

router = APIRouter()


@router.post("/trains/{train}/protocol")
def perform_protocol(train: Any, db: Session = Depends(dependencies.get_db)) -> Any:
    """
    Endpoint for performing the appropriate step in the protocol for the train with the given id
    """
    db_train = federated_trains.get(db=db, id=train)

    # TODO check train id logic
    if not db_train:

        db_train = federated_trains.get_by_name(db, name=train)
        if not db_train:
            raise HTTPException(status_code=403, detail="Train does not exist")

    protocol = AggregationProtocolClient(db)

    state = protocol.execute_protocol_for_train(db_train.id)

    return state


@router.get("/trains/{train_id}/keyBroadcasts", response_model=BroadCastKeysSchema)
def get_key_broadcast_from_conductor(train_id: int, db: Session = Depends(dependencies.get_db)) -> Any:
    broadcast = share_keys.get_broad_casted_keys(train_id)
    update_train_state_with_key_broadcast(db, train_id, broadcast)
    return broadcast


@router.post("/trains/{train_id}/maskedInputCollection")
def get_cyphers_from_conductor(train_id: int, db: Session = Depends(dependencies.get_db)) -> Any:
    cyphers = masked_input_collection.compute_masked_input_vector(db, train_id)
    return cyphers
