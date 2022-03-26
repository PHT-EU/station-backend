import os

import pytest
from dotenv import load_dotenv, find_dotenv

from station.clients.central.central_client import CentralApiClient


@pytest.fixture
def central_client():
    load_dotenv(find_dotenv())
    url = os.getenv("CENTRAL_API_URL")
    client_id = os.getenv("STATION_ROBOT_ID")
    client_secret = os.getenv("STATION_ROBOT_SECRET")
    return CentralApiClient(url, client_id, client_secret)