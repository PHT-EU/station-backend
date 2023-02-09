import os
from typing import Any, Dict

import requests
from sqlalchemy.orm import Session


class ConductorRESTClient:
    def __init__(self, conductor_url: str = None, station_id: int = None):
        self.conductor_url = (
            conductor_url if conductor_url else os.getenv("CONDUCTOR_URL")
        )
        self.station_id = station_id if station_id else os.getenv("STATION_ID")

        assert self.conductor_url
        assert self.station_id

    def get_model_for_train(self, train_id: Any, db: Session):
        """
        Obtain the model definition for the train given by the id from the conductor

        :param train_id:
        :param db:
        :return:
        """

        url = self.conductor_url + f"/api/trains/{train_id}/model"
        r = requests.get(url=url)
        return r.json()

    def upload_model_parameters(self, train_id: Any):
        pass

    def get_aggregated_model(self, train_id: Any):
        pass

    def get_available_trains(self):
        url = self.conductor_url + f"/api/stations/{self.station_id}/trains"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def post_discovery_results(self, train_id: Any, discovery_results: Dict):
        url = self.conductor_url + f"/api/trains/{train_id}/discovery"
        r = requests.post(url, json=discovery_results)
        print(r.request.body)
        r.raise_for_status()
        return r.json()
