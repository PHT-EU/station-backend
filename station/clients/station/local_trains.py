from io import BytesIO
import tarfile

import requests

from station.clients.resource_client import ResourceClient
from station.app.schemas.local_trains import LocalTrain, LocalTrainCreate, LocalTrainUpdate


class LocalTrainClient(ResourceClient[LocalTrain, LocalTrainCreate, LocalTrainUpdate]):

    def download_train_archive(self, train_id: str) -> tarfile.TarFile:
        url = f"{self.base_url}/{self.resource_name}/{train_id}/archive"
        with requests.get(url, headers=self._client.headers, stream=True) as r:
            r.raise_for_status()
            file_obj = BytesIO()
            for chunk in r.iter_content():
                file_obj.write(chunk)
            file_obj.seek(0)
        return tarfile.open(fileobj=file_obj)

