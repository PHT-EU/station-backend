import os

import pytest
from dotenv import find_dotenv, load_dotenv

from station.app.schemas.local_trains import LocalTrainCreate
from station.common.clients.station import StationAPIClient


@pytest.fixture
def station_client():
    load_dotenv(find_dotenv())
    base_url = os.getenv("STATION_API_URL", "http://localhost:8000/api")
    auth_url = os.getenv("STATION_AUTH_URL", "http://localhost:3010/token")
    username = os.getenv("STATION_USER")
    password = os.getenv("STATION_PASSWORD")
    return StationAPIClient(
        base_url=base_url, auth_url=auth_url, username=username, password=password
    )


"""
Test local train client

"""


def test_local_train_create(station_client):
    local_train = station_client.local_trains.create(
        LocalTrainCreate(
            name="test-create",
            command="python3 -m station.app.main",
            custom_image="station:latest",
        )
    )
    assert local_train.name == "test-create"
    assert local_train.command == "python3 -m station.app.main"


def test_get_local_train(station_client):
    local_train = station_client.local_trains.get("test-create")
    assert local_train.name == "test-create"
    assert local_train.command == "python3 -m station.app.main"


def test_list_local_trains(station_client):
    local_trains = station_client.local_trains.get_multi()
    print(local_trains)
    assert len(local_trains) > 0


def test_get_local_train_archive(station_client):
    archive = station_client.local_trains.download_train_archive(
        "5b2682dd-b4b1-46af-b2ed-d6aba8a309bb"
    )
    print(archive.getmembers())
    assert archive
