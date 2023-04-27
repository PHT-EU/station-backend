import os

import pytest

from station.common.clients.central import CentralApiClient


@pytest.fixture
def central_robot_credentials():
    api_url = os.getenv("CENTRAL_API_URL")
    robot_id = os.getenv("STATION_ROBOT_ID")
    robot_secret = os.getenv("STATION_ROBOT_SECRET")

    return {
        "api_url": api_url,
        "robot_id": robot_id,
        "robot_secret": robot_secret,
    }


def test_get_registry_credentials(central_robot_credentials):
    station_id = os.getenv("STATION_ID")

    client = CentralApiClient(**central_robot_credentials)

    registry_credentials = client.get_registry_credentials(station_id)
    print(registry_credentials)
    assert registry_credentials
    assert registry_credentials.address
    assert registry_credentials.user
    assert registry_credentials.password
    assert registry_credentials.project
