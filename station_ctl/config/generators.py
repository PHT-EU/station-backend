import random
import string

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def _password_generator() -> str:
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])


def _generate_private_key(path: str, password: str = None) -> str:
    private_key = rsa.generate_private_key(65537, key_size=2048)

    # encrypt key with password when given
    encryption_algorithm = serialization.BestAvailableEncryption(
        password.encode()) if password else serialization.NoEncryption()

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm
    )

    with open(path, 'wb') as f:
        f.write(pem)

    return pem.decode()


def _generate_fernet_key() -> str:
    key = Fernet.generate_key()
    return key.decode()
