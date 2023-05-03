import copy
import os
import pathlib
from unittest import mock

import pytest
from pydantic import ValidationError

from station.common.config.station_config import StationConfig
from station.ctl.config.command import render_config

TEST_DIR = pathlib.Path(__file__).parent

CONFIG_DICT = {
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
            "cert": str(TEST_DIR / "cert.pem"),
            "key": str(TEST_DIR / "key.pem"),
        },
    },
    "traefik": {"dashboard": True, "dashboard_port": 8081},
    "registry": {
        "address": "dev-harbor.personalhealthtrain.de",
        "user": "test-user",
        "password": "test-password",
        "project": "test-project",
    },
    "db": {"host": "127.0.0.1", "admin_user": "admin", "admin_password": "start123"},
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
        "admin_password": "start123",
    },
}


def test_config_from_dict():
    config = StationConfig(**CONFIG_DICT)
    config.display()


def test_construct():
    modified_config_dict = copy.deepcopy(CONFIG_DICT)
    modified_config_dict["https"]["certificate"]["key"] = "test-id"
    config = StationConfig.construct(**modified_config_dict)

    config.display()

    assert config.https.certificate.key == "test-id"

    with pytest.raises(ValidationError):
        config = StationConfig(modified_config_dict)


def test_from_file(tmp_path):
    # create temp path
    config_file = tmp_path / "test_station_config.yml"

    # render config file and write to path
    render_config(CONFIG_DICT, path=str(config_file))

    # print config file
    print(config_file.read_text())

    config = StationConfig.from_file(str(config_file))
    config.display()


def test_env_vars():
    # mock env vars

    # test top level env var
    with mock.patch.dict(os.environ, {"STATION_ID": "env-test"}):
        print(os.getenv("STATION_ID"))
        config = StationConfig(**CONFIG_DICT)
        assert config.id == "env-test"

    # test nested env var
    with mock.patch.dict(os.environ, {"STATION_MINIO_HOST": "env-test"}):
        config = StationConfig(**CONFIG_DICT)
        assert config.minio.host == "env-test"
