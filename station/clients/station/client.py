import time

import requests
import requests.auth
import pendulum

from station.app.schemas.local_trains import LocalTrain
from station.app.schemas.trains import Train
from station.app.schemas.datasets import DataSet
from station.clients.base import BaseClient
from station.clients.resource_client import ResourceClient


class StationAPIClient(BaseClient):
    local_trains: ResourceClient
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
            base_url=base_url,
            auth_url=auth_url,
            username=username,
            password=password
        )

        self.local_trains = ResourceClient(base_url, "local-trains", LocalTrain, client=self)
        self.datasets = ResourceClient(base_url, "datasets", DataSet, client=self)
        self.trains = ResourceClient(base_url, "trains/docker", Train, client=self)
