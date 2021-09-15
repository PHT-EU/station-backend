from typing import Union

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKeyWithSerialization as ECPubKey
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization as ECPrivateKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


class ProtocolKeys:
    signing_key: ECPrivateKey
    sharing_key: ECPrivateKey

    def __init__(self, signing_key: Union[ECPrivateKey, str] = None, sharing_key: Union[ECPrivateKey, str] = None):
        # generate a new private key if none is given
        if not signing_key:
            self.signing_key = ec.generate_private_key(ec.SECP384R1())

        else:
            # load private key from hex string
            if isinstance(signing_key, str):
                self.signing_key = self._load_private_key_from_hex(signing_key)

            # assign the key instance directly
            elif isinstance(signing_key, ECPrivateKey):
                self.signing_key = signing_key

            else:
                raise ValueError("Invalid key format")

        if not sharing_key:
            self.sharing_key = ec.generate_private_key(ec.SECP384R1())
        else:
            if isinstance(sharing_key, str):
                self.sharing_key = self._load_private_key_from_hex(sharing_key)

            else:
                self.sharing_key = sharing_key

    @property
    def hex_signing_key(self) -> str:
        return self._serialize_private_key_to_hex(self.signing_key)

    @property
    def hex_sharing_key(self) -> str:
        return self._serialize_private_key_to_hex(self.sharing_key)

    @property
    def signing_key_public(self) -> ECPubKey:
        return self.signing_key.public_key()

    @property
    def sharing_key_public(self) -> ECPubKey:
        return self.sharing_key.public_key()

    @property
    def hex_signing_key_public(self) -> str:
        return self._serialize_public_key_to_hex(self.signing_key_public)

    @property
    def hex_sharing_key_public(self) -> str:
        return self._serialize_public_key_to_hex(self.sharing_key_public)

    @staticmethod
    def _load_private_key_from_hex(key: str):
        private_key = serialization.load_pem_private_key(bytes.fromhex(key), password=None)
        return private_key

    @staticmethod
    def _serialize_private_key_to_hex(key: ECPrivateKey) -> str:
        return key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).hex()

    @staticmethod
    def _serialize_public_key_to_hex(key: ECPubKey) -> str:
        return key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1
        ).hex()
