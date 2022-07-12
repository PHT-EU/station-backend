import random
import string
from typing import Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization



def password_generator() -> str:
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])


def generate_private_key(name: str, password: str = None) -> Tuple[str, rsa.RSAPrivateKey, rsa.RSAPublicKey]:

    private_key = rsa.generate_private_key(65537, key_size=2048, backend=default_backend())
    # encrypt key with password when given
    if password:
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
    else:
        encryption_algorithm = serialization.NoEncryption()

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm
    )

    # name the private key file as pem
    if name.split(".")[-1] != "pem":
        name += ".pem"

    with open(name, 'wb') as f:
        f.write(pem)

    # generate public key and store it under the same name as .pub
    pub_name = name.split(".")[0] + ".pub"

    with open(pub_name, 'wb') as f:
        f.write(private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    return name, private_key, private_key.public_key()


def generate_fernet_key() -> str:
    key = Fernet.generate_key()
    return key.decode()
