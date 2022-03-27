import os

import pytest
from dotenv import load_dotenv, find_dotenv

from station.clients.central.central_client import CentralApiClient

from station_ctl.install import templates
from station_ctl.install.fs import ensure_directory_structure
from station_ctl.constants import PHTDirectories


@pytest.fixture
def central_client():
    load_dotenv(find_dotenv())
    url = os.getenv("CENTRAL_API_URL")
    client_id = os.getenv("STATION_ROBOT_ID")
    client_secret = os.getenv("STATION_ROBOT_SECRET")
    return CentralApiClient(url, client_id, client_secret)


def test_ensure_directory_structure(tmp_path):
    p = tmp_path / "station"
    ensure_directory_structure(p)
    for dir in PHTDirectories:
        assert p.joinpath(dir.value).exists()


def test_get_template_env():
    env = templates._get_template_env()
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
