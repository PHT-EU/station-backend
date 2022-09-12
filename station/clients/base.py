import urllib.parse

import pendulum
import requests


class BaseClient:
    def __init__(self,
                 base_url: str,
                 auth_url: str = None,
                 username: str = None,
                 password: str = None,
                 robot_id: str = None,
                 robot_secret: str = None,
                 headers: dict = None,
                 ):
        self.base_url = base_url
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.robot_id = robot_id
        self.robot_secret = robot_secret
        self.token = None
        self.refresh_token = None
        self.token_expiration = None
        self._headers = headers

        if not self.auth_url:
            self.auth_url = f"{self.base_url}/auth/token"

        self.setup()

    @property
    def headers(self) -> dict:
        token = self._get_token()
        if self._headers:
            return {**self._headers, "Authorization": f"Bearer {token}"}

        return {"Authorization": f"Bearer {token}"}

    def setup(self):
        self._get_token()

    def _get_token(self) -> str:
        if not self.token or self.token_expiration < pendulum.now():
            if self.username and self.password:
                r = requests.post(self.auth_url, data={"username": self.username, "password": self.password})
            elif self.robot_id and self.robot_secret:

                r = requests.post(self.auth_url, data={"id": self.robot_id, "secret": self.robot_secret})
            else:
                raise Exception("No credentials provided")

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
