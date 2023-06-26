import datetime
import os
import random
import string
from typing import Any

from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pydantic import BaseModel


class GeneratorResult(BaseModel):
    """Base class for generator results"""

    loc: tuple
    value: Any


def password_generator() -> str:
    return "".join(
        [random.choice(string.ascii_letters + string.digits) for _ in range(32)]
    )


def generate_private_key(
    name: str, path: str = None, password: str = None
) -> list[GeneratorResult]:
    private_key = rsa.generate_private_key(
        65537, key_size=2048, backend=default_backend()
    )
    # encrypt key with password when given
    if password:
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
    else:
        encryption_algorithm = serialization.NoEncryption()

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm,
    )

    # name the private key file as pem
    if name.split(".")[-1] != "pem":
        name += ".pem"

    # if a path is given append the name of the private key to this path
    if path:
        private_key_path = os.path.join(path, name)
        with open(private_key_path, "wb") as f:
            f.write(pem)

    # generate public key and store it under the same name as .pub
    pub_name = name.split(".")[0] + ".pub"
    if path:
        pub_key_path = os.path.join(path, pub_name)
    else:
        pub_key_path = os.getcwd().join(pub_name)
    with open(pub_key_path, "wb") as f:
        f.write(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    results = [GeneratorResult(loc=("central", "private_key"), value=private_key_path)]

    if password:
        results.append(
            GeneratorResult(loc=("central", "private_key_password"), value=password)
        )

    return results


def generate_fernet_key() -> GeneratorResult:
    key = Fernet.generate_key()

    result = GeneratorResult(loc=("api", "fernet_key"), value=key.decode())
    return result


def generate_self_signed_cert(
    domain_name: str, path: str = None
) -> list[GeneratorResult]:
    # Generate a new private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Create a new self-signed certificate
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domain_name)])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(domain_name)]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Write our certificate out to disk.
    if not path:
        path = os.getcwd()
    else:
        # make the path absolute
        path = os.path.abspath(path)

    cert_path = os.path.join(path, "cert.pem")
    key_path = os.path.join(path, "key.pem")

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )

    results = [
        GeneratorResult(loc=("https", "certificate", "cert"), value=cert_path),
        GeneratorResult(loc=("https", "certificate", "cert"), value=key_path),
    ]

    # Return the results containing the certificate and private key path
    return results
