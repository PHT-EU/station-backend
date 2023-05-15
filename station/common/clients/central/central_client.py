from typing import Any

import requests

from station.common.clients.base import BaseClient
from station.common.clients.central.schemas import RegistryCredentials


class CentralApiClient(BaseClient):
    def __init__(self, base_url: str, robot_id: str, robot_secret: str):
        super().__init__(
            base_url=base_url,
            robot_id=robot_id,
            robot_secret=robot_secret,
            auth_url=f"{base_url}/auth",
        )
        self.base_url = base_url

        self.api_url = base_url + "/api"

    def get_trains(self, station_id: Any) -> dict:
        url = self.api_url + "/train-stations?"
        filters = f"filter[station_id]={station_id}&include=train"
        safe_filters = self._make_url_safe(filters)
        url = url + safe_filters
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_registry_credentials(self, station_id: Any) -> RegistryCredentials:
        # get registry and external name
        url = self.api_url + "/stations?"
        filters = (
            "fields=+secure_id,+registry_project_account_name,"
            "+registry_project_account_token&"
            f"filter[id]={station_id}"
        )
        safe_filters = self._make_url_safe(filters)
        url = url + safe_filters
        r = requests.get(url, headers=self.headers)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(r.content)
            raise e
        # create credentials object
        station_registry_data = r.json()["data"][0]
        # extract station associated data from initial response
        project = station_registry_data["external_name"]
        registry_id = station_registry_data["registry_id"]
        registry_project_id = station_registry_data["registry_project_id"]

        address = self._get_registry_url(registry_id)
        user, password = self._get_registry_project_credentials(registry_project_id)

        credentials = RegistryCredentials(
            address=address,
            user=user,
            password=password,
            project=project,
        )
        return credentials

    def _get_registry_url(self, registry_id: Any) -> str:
        url = self.api_url + f"/registries/{registry_id}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()["host"]

    def _get_registry_project_credentials(self, registry_project_id: str) -> tuple:
        url = self.api_url + f"/registry-projects/{registry_project_id}?"
        filters = "fields=+account_id,+account_name,+account_secret"
        safe_filters = self._make_url_safe(filters)
        url = url + safe_filters
        r = requests.get(url, headers=self.headers)
        try:
            r.raise_for_status()
        except Exception as e:
            print(r.content)
            raise e
        return r.json()["account_name"], r.json()["account_secret"]

    def update_public_key(self, station_id: Any, public_key: str) -> dict:
        url = self.api_url + f"/stations/{station_id}"
        payload = {"public_key": public_key}
        r = requests.post(url, headers=self.headers, json=payload)
        r.raise_for_status()
        return r.json()
