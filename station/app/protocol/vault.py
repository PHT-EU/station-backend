"""
Utility functions for interacting with vault
"""

import requests
import os
from dotenv import load_dotenv, find_dotenv
from pprint import pprint
from cryptography import x509
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import ec
from typing import Tuple


def vault_headers(token: str = None) -> dict:
    if not token:
        token = os.getenv("VAULT_TOKEN")
    return {"X-Vault-Token": token}


def get_certified_ec_key_pair(role_name: str, url: str = None, token: str = None,
                              engine: str = "pki") -> Tuple[ec.EllipticCurvePrivateKeyWithSerialization, x509.Certificate]:
    if url:
        endpoint = url + f"/{role_name}"
    else:
        api_address = os.getenv("VAULT_API")
        endpoint = f"{api_address}/{engine}/issue/{role_name}"

    r = requests.post(endpoint, headers=vault_headers(token))
    r.raise_for_status()

    data = r.json()["data"]
    certificate = x509.load_pem_x509_certificate(data["certificate"].encode("utf-8"))
    private_key = load_pem_private_key(data=data["private_key"].encode("utf-8"), password=None)
    return private_key, certificate


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    print(get_certified_ec_key_pair("pht_federated", engine="pki"))
