import os

import pytest
from dotenv import load_dotenv, find_dotenv
import yaml

from station.clients.central.central_client import CentralApiClient

from station_ctl.util import get_template_env
from station_ctl.install import templates
from station_ctl.install.fs import create_pht_dirs
from station_ctl.constants import PHTDirectories
from station_ctl.install import docker


@pytest.fixture
def central_client():
    load_dotenv(find_dotenv())
    url = os.getenv("CENTRAL_API_URL")
    client_id = os.getenv("STATION_ROBOT_ID")
    client_secret = os.getenv("STATION_ROBOT_SECRET")
    return CentralApiClient(url, client_id, client_secret)


def test_ensure_directory_structure(tmp_path):
    p = tmp_path / "station"
    create_pht_dirs(p)
    for dir in PHTDirectories:
        assert p.joinpath(dir.value).exists()


def test_get_template_env():
    env = get_template_env()
    assert env

    template = env.get_template("init.sql.tmpl")
    assert template


def test_render_init_sql():
    sql = templates.render_init_sql("test_db_user")
    assert sql
    print(sql)
    lines = sql.splitlines()
    assert len(lines) == 4
    assert lines[-1].endswith("test_db_user;")
    assert lines[-2].endswith("test_db_user;")


def test_render_traefik_configs():
    traefik_config, router_config = templates.render_traefik_configs(
        http_port=80,
        https_port=443,
        domain="test.com",
        https_enabled=True,
        certs=[{"cert": "test", "key": "test"}],
    )
    assert traefik_config
    assert router_config

    print(traefik_config)
    print(router_config)

    traefik_dict = yaml.safe_load(traefik_config)
    router_dict = yaml.safe_load(router_config)
    print(traefik_dict)
    print(router_dict)

    assert traefik_dict["entryPoints"]["http"]["address"] == ":80"
    assert traefik_dict["entryPoints"]["https"]["address"] == ":443"

    assert router_dict["http"]["routers"]["traefik"]["tls"]["domains"][0]["main"] == "test.com"
    assert router_dict["tls"]["certificates"][0]["certFile"] == "test"
    assert router_dict["tls"]["certificates"][0]["keyFile"] == "test"


def test_setup_volumes():
    docker.setup_volumes()
