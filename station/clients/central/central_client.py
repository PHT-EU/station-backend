from typing import Any

import requests

from station.clients.base import BaseClient


class CentralApiClient(BaseClient):

    def __init__(self, api_url: str, robot_id: str, robot_secret: str):

        super().__init__(
            base_url=api_url,
            robot_id=robot_id,
            robot_secret=robot_secret,
            auth_url=f"{api_url}/token"
        )

        self.api_url = api_url

    def get_trains(self, station_id: Any) -> dict:
        url = self.api_url + "/train-stations?"
        filters = f"filter[station_id]={station_id}&include=train"
        safe_filters = self._make_url_safe(filters)
        url = url + safe_filters
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_registry_credentials(self, station_id: Any) -> dict:
        url = self.api_url + f"/stations/{station_id}?"
        filters = "fields[station]=+secure_id,+registry_project_account_name,+registry_project_account_token,+public_key"
        safe_filters = self._make_url_safe(filters)
        url = url + safe_filters
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def update_public_key(self, station_id: Any, public_key: str) -> dict:
        url = self.api_url + f"/stations/{station_id}"
        payload = {
            "public_key": public_key
        }
        r = requests.post(url, headers=self.headers, json=payload)
        r.raise_for_status()
        return r.json()
