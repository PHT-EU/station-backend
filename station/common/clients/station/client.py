import os

from station.app.schemas.datasets import DataSet
from station.app.schemas.local_trains import LocalTrain
from station.app.schemas.trains import Train
from station.common.clients.base import BaseClient
from station.common.clients.resource_client import ResourceClient
from station.common.clients.station.local_trains import LocalTrainClient


class StationAPIClient(BaseClient):
    local_trains: LocalTrainClient
    datasets: ResourceClient
    trains: ResourceClient

    def __init__(
        self,
        base_url: str,
        auth_url: str = None,
        username: str = None,
        password: str = None,
    ):
        super().__init__(
            base_url=base_url, auth_url=auth_url, username=username, password=password
        )

        self.local_trains = LocalTrainClient(base_url, "local-trains", LocalTrain, self)
        self.datasets = ResourceClient(base_url, "datasets", DataSet, client=self)
        self.trains = ResourceClient(base_url, "trains/docker", Train, client=self)

    @classmethod
    def from_env(cls):
        base_url = os.getenv("STATION_API_URL")
        username = os.getenv("STATION_USER")
        password = os.getenv("STATION_PASSWORD")
        auth_url = os.getenv("AUTH_URL")

        return cls(
            base_url=base_url, username=username, password=password, auth_url=auth_url
        )
