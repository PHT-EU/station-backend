import requests
import os
from dotenv import load_dotenv, find_dotenv
from typing import List, Tuple
from sqlalchemy.orm import Session

from station.app.schemas.protocol import BroadCastKeysSchema, StationKeys
from station.app.protocol.primitives.secret_sharing import share_secret_pycroptodome, share_secret_key
from station.app.crud.train import (
    update_train_state_with_key_broadcast,
    update_rng_seed,
    get_train_sharing_key,
    get_train_signing_key
)
from station.app.protocol.messages.share_keys import ShareKeysMessage
from station.app.crud import federated_trains


def share_keys(db: Session, train_id: int, conductor_url: str = None):
    if not conductor_url:
        conductor_url = os.getenv("CONDUCTOR_URL")

    assert conductor_url
    # Get the keys from the server
    broadcast = get_broad_casted_keys(train_id=train_id, conductor_url=conductor_url)
    # TODO get threshold from train config and pass to secret sharing
    validate_keys(broadcast.keys)
    # store the received keys
    state = federated_trains.update_train_with_key_broadcast(db, train_id=train_id, key_broadcast=broadcast)

    n_participants = len(broadcast.keys)

    # Create seed/shares and update db state
    seed, seed_shares = create_random_seed_and_shares(n_participants)
    state = update_rng_seed(db, str(train_id), seed)

    sharing_key = get_train_sharing_key(db, train_id)
    signing_key = get_train_signing_key(db, train_id)

    key_shares = create_key_shares(sharing_key, n_participants)

    msg = ShareKeysMessage(db, signing_key, broadcast.keys, seed_shares, key_shares, state.iteration)

    res = send_shared_keys_to_server(train_id, msg, conductor_url)

    return res


def send_shared_keys_to_server(train_id: int, msg: ShareKeysMessage, conductor_url: str = None):
    r = requests.post(conductor_url + f"/api/trains/{train_id}/shareKeys", json=msg.serialize(format="dict"))
    print(r.json())
    r.raise_for_status()

    return r.json()


def get_broad_casted_keys(train_id: int, conductor_url: str = None) -> BroadCastKeysSchema:
    """
    Get keys from the server if the train is ready for key distribution other wise raise an error

    :param train_id:
    :param conductor_url:
    :return:
    """
    if not conductor_url:
        conductor_url = os.getenv("CONDUCTOR_URL")
    r = requests.get(conductor_url + f"/api/trains/{train_id}/broadcastKeys")
    print(r.json())
    r.raise_for_status()
    broadcast = BroadCastKeysSchema(**r.json())
    return broadcast


def validate_keys(keys: List[StationKeys], threshold: int = 3):
    # check the size of the received keys
    if threshold:
        assert len(keys) >= threshold

    def _all_unique(x):
        seen = list()
        return not any(i in seen or seen.append(i) for i in x)

    signing_keys = [sk.signing_key for sk in keys]
    sharing_keys = [sk.sharing_key for sk in keys]
    # Check that all public keys are unique
    assert _all_unique(signing_keys)
    assert _all_unique(sharing_keys)
    # TODO add key signature validation


def create_random_seed_and_shares(n: int, threshold: int = 3) -> Tuple[int, List[Tuple[int, bytes]]]:
    seed = os.urandom(6)
    shares = share_secret_pycroptodome(seed, threshold, n)

    return int.from_bytes(seed, byteorder="big"), shares


def create_key_shares(sharing_key: str, n: int, t: int = 3):
    key_shares = share_secret_key(bytes.fromhex(sharing_key), t, n)
    # print(key_shares)
    return key_shares


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    share_keys(station_id=1, train_id=1, iteration=0)
