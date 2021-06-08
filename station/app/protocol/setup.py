from dotenv import load_dotenv, find_dotenv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKeyWithSerialization as ECPK
from cryptography.hazmat.primitives.asymmetric import ec
from typing import Tuple
from sqlalchemy.orm import Session
import requests
import os
from fastapi import HTTPException

from station.app.crud.train import create_train, update_train_round_0
from station.app.models.train import Train
from station.app.protocol.vault import get_certified_ec_key_pair
from station.app.crud import trains


# TODO Check consistency in train ids
def initialize_train(db: Session, station_id: int, train_id: str, proposal_id: int):
    db_train = db.query(Train).get(train_id)
    db_train = trains.get_by_train_id(db, train_id)
    if db_train:
        raise HTTPException(400, detail="Train already exists")
    token = register_for_train(station_id=station_id, train_id=train_id)
    train = create_train(db, proposal_id=proposal_id, token=token)
    return train


# TODO get train config from server

def register_for_train(station_id: int, train_id: str, conductor_url: str = None):
    if not conductor_url:
        conductor_url = os.getenv("CONDUCTOR_URL")

    r = requests.post(conductor_url + f"/stations/{station_id}/{train_id}")
    r.raise_for_status()
    token = r.json()["token"]
    return token


def setup_protocol(db: Session, train_id: int, iteration: int) -> Tuple[ECPK, ECPK]:
    # get the key pairs
    load_dotenv(find_dotenv())
    # TODO uncomment this when vault is back
    # sk2, cert1 = get_certified_ec_key_pair("pht_federated")
    # sk2, cert2 = get_certified_ec_key_pair("pht_federated")

    # TODO evaluate key storage
    c_sk, c_pk, s_sk, s_pk = generate_ec_key_pair()

    signing_key = c_sk.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).hex()
    sharing_key = s_sk.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).hex()
    # update db state
    state = update_train_round_0(db, train_id=train_id, signing_key=signing_key,
                                 sharing_key=sharing_key, iteration=iteration)

    # return cert1.public_key(), cert2.public_key()
    return c_pk, s_pk


def generate_ec_key_pair():
    signing_key = ec.generate_private_key(ec.SECP384R1())
    sharing_key = ec.generate_private_key(ec.SECP384R1())
    return signing_key, signing_key.public_key(), sharing_key, sharing_key.public_key()


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    # initialize_train(1, 1, 1)
    # setup_protocol(1, 0)
    # print(generate_ec_key_pair())
    c_pk, s_sk = setup_protocol()
