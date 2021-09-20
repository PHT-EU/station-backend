import os
import requests
from dotenv import load_dotenv, find_dotenv
from sqlalchemy.orm import Session

from station.app.protocol.messages import AdvertiseKeysMessage
from station.app.protocol.setup import setup_protocol
from station.app.crud.train import read_train_state
from station.app.models.train import TrainState


def advertise_keys(db: Session, train_id: int,
                   station_id: int = None, conductor_url: str = None) -> TrainState:
    # TODO get train token from db
    if not station_id:
        station_id = os.getenv("STATION_ID")

    assert station_id
    # Get train state
    state = read_train_state(db, train_id)

    signing_key, sharing_key = setup_protocol(db, train_id, state.iteration)
    msg = AdvertiseKeysMessage(
        station_id=station_id,
        train_id=train_id,
        iteration=state.iteration,
        signing_key=signing_key,
        sharing_key=sharing_key
    )

    if not conductor_url:
        conductor_url = os.getenv("CONDUCTOR_URL")

    assert conductor_url

    # Send message to the conductor
    response = requests.post(conductor_url + f"/api/trains/{train_id}/advertiseKeys", json=msg.serialize())
    print(response.json())
    response.raise_for_status()

    # update train state
    state.round = 1

    db.commit()
    db.refresh(state)

    return state


if __name__ == '__main__':
    load_dotenv(find_dotenv(raise_error_if_not_found=True))
    state = advertise_keys(station_id=3, train_id=1)
    print(state)
