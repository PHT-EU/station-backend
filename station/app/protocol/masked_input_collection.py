import os
import requests
from sqlalchemy.orm import Session
from typing import List
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey, EllipticCurvePublicKey

from station.app.crud.train import read_train_state
from station.app.schemas import protocol
from station.app.models.protocol import Cypher
from station.app.crud.train import get_train_signing_key
from station.app.protocol.primitives import key_agreement
from station.app.crud.protocol import get_signing_key_from_key_broadcast


def compute_masked_input_vector(db: Session, train_id: int, conductor_url: str = None):
    """
    Performs round 2 of the aggregation protocol for a specified train

    :param db:
    :param train_id:
    :param conductor_url:
    :return:
    """
    state = read_train_state(db, train_id)
    # get the cyphers from the server, store them and return the participants in round 2
    participants = get_cyphers(db, train_id, state.iteration, conductor_url)
    signing_private_key = _load_local_signing_private_key(db, train_id)
    for particpant in participants:
        signing_public_key = _load_signing_public_key(db, train_id, particpant, state.iteration)


def _load_local_signing_private_key(db: Session, train_id: int) -> EllipticCurvePrivateKey:
    """
    Gets this iterations locally stored private from the DB and load it into a private key object


    :param db:
    :param train_id:
    :return:  Private key to be used for performing the key exchange algorithm
    """

    signing_key_str = get_train_signing_key(db, train_id)
    private_key = key_agreement.load_private_key(signing_key_str)
    return private_key


def _load_signing_public_key(db: Session, train_id: int, station_id: int, iteration: int) -> EllipticCurvePublicKey:
    db_sharing_key = get_signing_key_from_key_broadcast(db, train_id, station_id, iteration)
    public_key = key_agreement.load_public_key(db_sharing_key)
    return public_key


def get_cyphers(db: Session, train_id: int, iteration: int, conductor_url: str = None) -> List[int]:
    """
    Get the cyphers from the conductor and process them according to the local train state and config

    :param db:
    :param train_id:
    :param iteration:
    :param conductor_url:
    :return: List U_2 of ids of participants in the second round of the protocol
    """

    if not conductor_url:
        conductor_url = os.getenv("CONDUCTOR_URL")

    data = {
        "station_id": os.getenv("STATION_ID"),
        "iteration": iteration
    }
    r = requests.post(conductor_url + f"/api/trains/{train_id}/cyphers", json=data)
    # TODO validate the length of the users based on train config
    print(len(r.json()))
    participants = _process_cyphers(db, train_id, iteration, r.json())
    return participants


def _process_cyphers(db: Session, train_id: int, iteration: int, cyphers: list) -> List[int]:
    """
    Process the cyphers received from the conductor and store foreign cyphers in the database

    :param db:
    :param train_id:
    :param iteration:
    :param cyphers: List of cyphers
    :return: List of participating station ids defining the list of participants for round 2
    """

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
            db.add(db_cypher)
            participants_round_2.append(cypher_msg["sender"])
    db.commit()

    return participants_round_2
