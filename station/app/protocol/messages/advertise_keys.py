from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from typing import Union, Optional
from .base import Message
import json
from ..vault import get_certified_ec_key_pair
from dotenv import load_dotenv, find_dotenv


class AdvertiseKeysMessage(Message):
    station_id: int
    train_id: int
    signing_key: EllipticCurvePublicKey
    sharing_key: EllipticCurvePublicKey
    key_signature: Optional[bytes]
    iteration: int

    def __init__(self, station_id: int, train_id: int, signing_key: Union[str, EllipticCurvePublicKey] = None,
                 sharing_key: Union[str, EllipticCurvePublicKey] = None, key_signature: Union[str, bytes] = None,
                 iteration: int = 0):
        self.station_id = station_id
        self.train_id = train_id

        # Initialize with values passed to the constructor
        if signing_key and sharing_key:
            self.signing_key = self._load_public_key(signing_key)
            self.sharing_key = self._load_public_key(sharing_key)
            if isinstance(key_signature, str):
                self.key_signature = self._from_hex(key_signature)
            else:
                self.key_signature = key_signature

        # Create a new message by obtaining keys from vault
        else:
            self._make_message()

        self.iteration = iteration

    def serialize(self, format: str = None):

        # Create dictionary and serialize values
        json_dict = {
            "train_id": self.train_id,
            "station_id": self.station_id,
            "signing_key": self._pk_to_hex(self.signing_key),
            "sharing_key": self._pk_to_hex(self.sharing_key),
            "key_signature": self._to_hex(self.key_signature) if self.key_signature else None,
            "iteration": self.iteration
        }
        if format == "json":
            return json.dumps(json_dict, indent=2)

        return json_dict

    def _make_message(self, sign_keys=False):
        sk1, cert1 = get_certified_ec_key_pair("pht_federated")
        sk2, cert2 = get_certified_ec_key_pair("pht_federated")
        # TODO store private keys
        self.signing_key = cert1.public_key()
        self.sharing_key = cert2.public_key()
        self.key_signature = None
        if sign_keys:
            # TODO sign keys with TTP key
            pass








if __name__ == '__main__':
    load_dotenv(find_dotenv())
    sk1, cert1 = get_certified_ec_key_pair("pht_federated")
    sk2, cert2 = get_certified_ec_key_pair("pht_federated")

    msg = AdvertiseKeysMessage(
        station_id=1,
        train_id=1
    )
    print(msg.serialize())








