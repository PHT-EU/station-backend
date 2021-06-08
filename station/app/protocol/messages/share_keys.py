import os
from typing import List, Tuple
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from datetime import datetime
import json
from cryptography.fernet import Fernet
import base64

from .base import Message
from station.app.schemas.protocol import StationKeys
from station.app.protocol.primitives.key_agreement import derive_shared_key


class ShareKeysMessage(Message):

    def __init__(self, db: Session, signing_key: str, broadcast_keys: List[StationKeys],
                 seed_shares: List[Tuple[int, bytes]], key_shares, iteration: int):
        self.broadcast_keys = broadcast_keys
        self.seed_shares = seed_shares
        self.key_shares = key_shares
        self.db = db
        self.private_key = load_pem_private_key(
            bytes.fromhex(signing_key),
            None
        )
        self.station_id = os.getenv("STATION_ID")
        self.iteration = iteration

    def serialize(self, format: str = "json"):
        msg = {}
        cypher_texts = self._create_cyphers()
        msg["cyphers"] = cypher_texts
        msg["created_at"] = datetime.now().isoformat()
        msg["station_id"] = self.station_id
        msg["iteration"] = self.iteration

        return json.dumps(msg)

    def _create_cyphers(self):
        cyphers = []
        for i, key_pair in enumerate(self.broadcast_keys):
            derivation_pk = load_pem_public_key(bytes.fromhex(key_pair.signing_key))
            # ECDSH key derivation with station id as additional data
            shared_aes_key = derive_shared_key(self.private_key, derivation_pk, self.station_id.encode())
            if not self.station_id == key_pair.station_id:
                cypher_msg = {
                    "station_id": key_pair.station_id,
                    "cypher": self._make_cypher(shared_aes_key, i)

                }
                cyphers.append(cypher_msg)

        return cyphers

    def _make_cypher(self, key: bytes, index: int):
        cypher_dict = {"seed_share": [self.seed_shares[index][0], self.seed_shares[index][1].hex()],
                       "key_shares": self._get_key_shares(index),
                       }
        json_string = json.dumps(cypher_dict)

        fernet = Fernet(base64.b64encode(key))
        cypher = fernet.encrypt(json_string.encode("utf-8"))

        return cypher.hex()

    def _get_key_shares(self, index: int):
        shares = []
        for key_share in self.key_shares:
            shares.append([key_share[index][0], key_share[index][1].hex()])
        return shares
