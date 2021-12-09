from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives import serialization
from typing import Union


class Message:

    def serialize(self, format: str = "json"):
        pass

    @staticmethod
    def _load_public_key(key: Union[str, EllipticCurvePublicKey, bytes]):
        if isinstance(key, EllipticCurvePublicKey):
            return key
        elif isinstance(key, str):
            key = load_pem_public_key(bytes.fromhex(key))
            return key
        elif isinstance(key, bytes):
            key = load_pem_public_key(key)
            return key
        else:
            raise ValueError(f"Unsupported key format for key:\n{key}")

    @staticmethod
    def _pk_to_hex(pk: EllipticCurvePublicKey) -> str:

        pk_hex = pk.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).hex()
        print(pk_hex)
        return pk_hex

    @staticmethod
    def _to_hex(val: bytes) -> str:
        return val.hex()

    @staticmethod
    def _from_hex(val: str) -> bytes:
        return bytes.fromhex(val)
