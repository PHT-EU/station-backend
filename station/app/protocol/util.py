from typing import Union

from sqlalchemy.orm import Session
from .advertise_keys import advertise_keys
from .share_keys import share_keys
from station.app.crud import trains

ROUND_FUNCTIONS = {
    0: advertise_keys,
    1: share_keys
}


def execute_protocol(db: Session, train_id: Union[int, str]):
    train = trains.get_by_train_id(db, str(train_id))
    state = train.state

    protocol_round = state.round

    state = ROUND_FUNCTIONS[protocol_round](db, train_id)

    return state
