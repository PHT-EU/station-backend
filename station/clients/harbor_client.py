import requests
import os
from typing import Union, List
from pprint import pprint

from dotenv import load_dotenv, find_dotenv


class HarborClient:

    def __init__(self, harbor_api_url: str = None, username: str = None, password: str = None):
        # Setup and verify connection parameters either based on arguments or .env vars

        self.url = harbor_api_url if harbor_api_url else os.getenv("HARBOR_URL")
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
        #TODO chache no replys
        return r.json()

    def get_master_images(self):
        """
        returns names of master images form harbor
        """
        endpoint = f"/projects/master/repositories"
        r = requests.get(self.url + endpoint, auth=(self.username, self.password))
        return [repositori["name"] for repositori in r.json()]

    def health_check(self):
        """
        requests the central service
        @return: dict: status of central harbor instance
        """
        url = self.url + "health"
        try:
            r = requests.get(url=url, auth=(self.username, self.password))
            if r and r.status_code == 200:
                return r.json()
            else:
                return {"status": None}
        except requests.exceptions.ConnectionError as e:
            print(e)
        return {"status": None}




harbor_client = HarborClient()

if __name__ == '__main__':
    load_dotenv(find_dotenv())
    hc = HarborClient()
    res = hc.get_artifacts_for_station(3)
    print(res)
