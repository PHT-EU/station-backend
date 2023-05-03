import copy
import re

import pytest
from rich.console import Console

from station.common.constants import CERTS_REGEX
from station.ctl.config import validate_config
from station.ctl.config.validate import validate_config_object


@pytest.fixture
def config_dict():
    config = {
        "id": "d7b7bd69-c828-45f3-b0bc-0d5ca10a8cd5",
        "version": "latest",
        "environment": "development",
        "admin_password": "GucVuG6MgVyy58v8Xjg3o4jTnAyNrP1k",
        "data_dir": "./station_data",
        "central": {
            "api_url": "https://dev.personalhealthtrain.de/api",
            "robot_id": "0b34acb9-9b26-4780-80d1-705772464cf2",
            "robot_secret": "start123",
            "private_key": "./private.pem",
            "private_key_password": "",
        },
        "http": {"port": "80"},
        "https": {
            "port": "443",
            "domain": "station.localhost",
            "certificate": {
                "cert": "./certs/cert.pem",
                "key": "./certs/cert.pem",
            },
        },
        "traefik": {"dashboard": True, "dashboard_port": 8081},
        "registry": {
            "address": "dev-harbor.personalhealthtrain.de",
            "user": "test-user",
            "password": "test-password",
            "project": "test-project",
        },
        "db": {"host": "127.0.0.1", "admin_user": "admin", "admin_password": "admin"},
        "api": {"fernet_key": "Z_kebTcA7p2VV9xga-ES2wCMjvfaRNzQktjsxo5vPMM="},
        "airflow": {
            "host": "127.0.0.1",
            "admin_user": "admin",
            "admin_password": "start123",
        },
        "auth": {
            "admin_user": "admin",
            "host": "127.0.0.1",
            "port": 3001,
            "robot_id": "5f77fe3f-a48c-46be-ba67-df6b1058ebcb",
            "robot_secret": "v1ziczynshyotuzudc8ymumjtijli9yoo1mygyrv2ucqdm77lae6d5pni6xh5vp4",
        },
        "minio": {
            "host": "127.0.0.1",
            "port": 9000,
            "admin_user": "minio_admin",
            "admin_password": "minio_admin",
        },
        "redis": {
            "host": "127.0.0.1",
        },
    }
    return config


def test_validate_config_object(config_dict):
    test_dict = copy.deepcopy(config_dict)

    del test_dict["id"]
    del test_dict["airflow"]["host"]
    del test_dict["https"]["certificate"]["key"]
    test_dict["admin_password"] = "password"
    validate_config_object(test_dict)


def test_validate_config(config_dict):
    results, table = validate_config(config_dict)
    console = Console()
    print()
    console.print(table)


def test_match_cert_index():
    field_0 = "https.certs[0]"
    field_1 = "https.certs[12]"
    field_2 = "htps.certs[0]"
    field_3 = "https.certs[a]"

    assert re.match(CERTS_REGEX, field_0)
    assert re.match(CERTS_REGEX, field_0).group(1) == "0"
    assert re.match(CERTS_REGEX, field_1)
    assert re.match(CERTS_REGEX, field_2) is None
    assert re.match(CERTS_REGEX, field_3) is None
