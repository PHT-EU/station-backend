from typing import Any
import urllib.parse

import requests
import pendulum


class CentralApiClient:

    def __init__(self, api_url: str, robot_id: str, robot_secret: str):
        self.api_url = api_url
        self.robot_id = robot_id
        self.robot_secret = robot_secret
        self.token = None
        self.token_expiration = None
        self.setup()

    def setup(self):
        self._get_token()

    @property
    def headers(self) -> dict:
        token = self._get_token()

        return {"Authorization": f"Bearer {token}"}

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

    def _get_token(self) -> str:
        if not self.token or self.token_expiration < pendulum.now():
            r = requests.post(f"{self.api_url}/token", data={"id": self.robot_id, "secret": self.robot_secret})
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(r.text)
                raise e
            r = r.json()
            self.token = r["access_token"]
            self.token_expiration = pendulum.now().add(seconds=r["expires_in"])

        return self.token

    @staticmethod
    def _make_url_safe(url: str) -> str:
        return urllib.parse.quote(url, safe="=&?")
