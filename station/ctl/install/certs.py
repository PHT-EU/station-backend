import datetime
from pathlib import Path

import click
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def copy_certificates(ctx):
    """
    Copy certificates from the paths specified in the config to the installation directory
    Args:
        ctx: cli context

    Returns:

    """
    click.echo("Copying certificates to installation directory")
    certs = ctx.obj['https']['certs'][0]
    key_path = certs['key']
    cert_path = certs['cert']
    with open(key_path, "rb") as f:
        key = f.read()
    with open(cert_path, "rb") as f:
        cert = f.read()

    dest_path = Path(ctx.obj["install_dir"]) / "certs"
    with open(dest_path / "key.pem", "wb") as f:
        f.write(key)
    with open(dest_path / "cert.pem", "wb") as f:
        f.write(cert)

def generate_certificates(domain: str, key_path: str, cert_path: str, key_password: str = None):
    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    # Write our key to disk for safe keeping
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(
                key_password.encode()) if key_password else serialization.NoEncryption(),
        ))

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"DE"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Baden-Wuerttemberg"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Tuebingen"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"PHT"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"{}".format(domain)),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Our certificate will be valid for 1 year
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"station.local")]),
        critical=False,
        # Sign our certificate with our private key
    ).sign(key, hashes.SHA256())
    # Write our certificate out to disk.
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
