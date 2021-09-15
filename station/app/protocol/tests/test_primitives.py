import pytest

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKeyWithSerialization as ECPubKey
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization as ECPrivateKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from station.app.protocol.primitives.keys import ProtocolKeys


def test_protocol_keys_generate():
    keys = ProtocolKeys()

    assert isinstance(keys.signing_key, ECPrivateKey)
    assert isinstance(keys.signing_key, ECPrivateKey)


def test_protocol_keys_initialization():
    key = ec.generate_private_key(ec.SECP384R1())

    key_hex = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).hex()

    keys_hex = ProtocolKeys(key_hex, key_hex)

    keys_instance = ProtocolKeys(key, key)

    with pytest.raises(ValueError):
        keys = ProtocolKeys(1, 0.5)




def test_protocol_keys_serialization_and_loading():
    key = ec.generate_private_key(ec.SECP384R1())

    key_hex = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).hex()

    keys = ProtocolKeys(signing_key=key_hex, sharing_key=key_hex)

    assert keys.hex_sharing_key == key_hex
    assert keys.hex_signing_key == key_hex

    keys2 = ProtocolKeys(key, key)

    assert keys2.hex_sharing_key == key_hex
    assert keys2.hex_signing_key == key_hex
