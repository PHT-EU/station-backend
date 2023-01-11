from io import BytesIO

import requests

from station.app.schemas.local_trains import LocalTrain, LocalTrainCreate, LocalTrainUpdate
from station.clients.resource_client import ResourceClient


class LocalTrainClient(ResourceClient[LocalTrain, LocalTrainCreate, LocalTrainUpdate]):

    def download_train_archive(self, train_id: str) -> BytesIO:
        url = f"{self.base_url}/{self.resource_name}/{train_id}/archive"
        with requests.get(url, headers=self._client.headers, stream=True) as r:
            r.raise_for_status()
            file_obj = BytesIO()
            for chunk in r.iter_content():
                file_obj.write(chunk)
            file_obj.seek(0)
        return file_obj

    def post_failure_notification(
            self,
            train_id: str,
            message: str,

    ) -> None:
        url = f"{self.base_url}/notifications"
        payload = {
            "message": message,
            "topic": "local-trains",
            "title": f"Local Train {train_id} failed"
        }
        with requests.post(url, headers=self._client.headers, json=payload) as r:
            r.raise_for_status()

    def update_train_status(self, train_id: str, status: str):
        url = f"{self.base_url}/{self.resource_name}/{train_id}"
        payload = {
            "status": status
        }
        with requests.put(url, headers=self._client.headers, json=payload) as r:
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(e)
                print(r.text)
                raise e
