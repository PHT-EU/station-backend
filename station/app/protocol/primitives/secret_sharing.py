import subprocess
import os
from typing import List, Tuple
from Crypto.Protocol.SecretSharing import Shamir
import math

"""
Share and combine secrets with the Shamir Secret Sharing Scheme.

uses the ssss tool http://point-at-infinity.org/ssss/
"""


def create_random_seed_and_shares(n: int, threshold: int = 3) -> Tuple[int, List[Tuple[int, bytes]]]:
    seed = os.urandom(6)
    shares = share_secret_pycroptodome(seed, threshold, n)

    return int.from_bytes(seed, byteorder="big"), shares


# TODO implement this for larger secrets more efficiently

def share_secret(secret: bytes, t: int, n: int, s: int = 1024) -> List[bytes]:
    args = ["ssss-split", "-t", str(t), "-n", str(n), "-s", str(s)]
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.communicate(secret)

    # secrets = [s.decode("utf-8").split("-") for s in output[0].splitlines()[1:]]
    secrets = output[0].splitlines()[1:]
    process.terminate()
    return secrets


def combine_secret(shares: List[bytes], t: int) -> str:
    """
    Takes a list of shares as bytes and combines them into the original secret using ssss combine


    :param shares:
    :param t:
    :return: hex string containing the reconstructed secret
    """
    args = ["ssss-combine", "-t", str(t), "-x"]
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    ssss_input = b"\n".join(shares)
    output = process.communicate(ssss_input)
    secret = output[1].decode("utf-8").split(" ")[2].rstrip()
    process.terminate()
    return secret


# Only 16 byte secrets

def share_secret_pycroptodome(secret: bytes, t: int, n: int) -> List[Tuple[int, bytes]]:
    if len(secret) < 16:
        padded_secret = secret + b"\0" * (16 - len(secret))
        shares = Shamir.split(t, n, padded_secret)
        return shares
    shares = Shamir.split(t, n, secret)
    return shares


def combine_secret_pycroptodome(shares: List[Tuple[int, bytes]]) -> bytes:
    secret = Shamir.combine(shares)
    return secret


def recover_seed(seed_shares):
    secret = combine_secret_pycroptodome(seed_shares)
    return secret[:6]


def share_secret_key(secret_key_bytes: bytes, t: int, n: int) -> List[List[Tuple[int, bytes]]]:
    blocks = math.floor(len(secret_key_bytes) / 16.0)
    block_shares = []
    for i in range(blocks):
        key_block = secret_key_bytes[i * 16: (i + 1) * 16]
        block = share_secret_pycroptodome(key_block, t, n)
        block_shares.append(block)
    # Add the incomplete block
    remainder = secret_key_bytes[blocks * 16:]
    pad_size = 16 - len(remainder)
    remainder += b"\0" * pad_size
    block_shares.append(share_secret_pycroptodome(remainder, t, n))

    return block_shares


def recover_secret_key(shares: List[List[Tuple[int, bytes]]]) -> str:
    recovered = ""
    for block in shares:
        recovered += combine_secret_pycroptodome(block).hex()

    # remove padding (last 14 bytes/28 hex chars in current implementation)
    # TODO improve this hack
    recovered = recovered[:-28]

    return recovered


if __name__ == '__main__':
    data = os.urandom(306)
    print(data.hex())
    key_shares = share_secret_key(data, 3, 5)
    recovered_key = recover_secret_key(key_shares)

    print(data == bytes.fromhex(recovered_key))

    seed_data = os.urandom(6)
    seed_hex = seed_data.hex()
    secrets = share_secret_pycroptodome(seed_data, 3, 3)
    recovered_seed = recover_seed(secrets)
    print(seed_hex)
    print(recovered_seed.hex())

    # print(data.hex())
    # shares = share_secret(data, 3, 5)
    # print(shares)
    # combined = combine_secret(shares[:3], 3)
    # print(combined)
    # print(combined == data.hex())
