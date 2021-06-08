import requests
import os
from typing import Union, List
from pprint import pprint

from dotenv import load_dotenv, find_dotenv


class HarborClient:

    def __init__(self, harbor_api_url: str = None, username: str = None, password: str = None):
        # Setup and verify connection parameters either based on arguments or .env vars

        self.url = harbor_api_url if harbor_api_url else os.getenv("HARBOR_API_URL")
        assert self.url

        self.username = username if username else os.getenv("HARBOR_USER")
        assert self.username

        self.password = password if password else os.getenv("HARBOR_PW")
        assert self.password

    def get_artifacts_for_station(self, station_id: Union[str, int] = None) -> List[dict]:

        if not station_id:
            station_id = int(os.getenv("STATION_ID"))
        assert station_id

        endpoint = f"/projects/station_{station_id}/repositories"
        r = requests.get(self.url + endpoint, auth=(self.username, self.password))
        return r.json()


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    hc = HarborClient()
    res = hc.get_artifacts_for_station(1)
