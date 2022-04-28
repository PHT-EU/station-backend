from station.clients.minio import MinioClient
from conductor_lib.src.torch import LightningTrainModel
from typing import Union
import os
from torch.utils.data import DataLoader

from station.worker.loader import BaseLoader


class ModelTrainer:

    def __init__(self, model_id: str = None, data_set_id: str = None, station_url: str = None):
        """
        Initialize a model trainer instance with a model and data set id

        :param model_id:
        :param data_set_id:
        :param station_url:
        """
        self.model_id = model_id
        self.station_url = station_url if station_url else os.getenv("STATION_API_URL")
        assert self.station_url
        self.model: LightningTrainModel = None
        # TODO fix minio
        self.data_set_id = data_set_id
        self.minio_client = MinioClient(minio_server="localhost:9000",
                                        secret_key="minio_admin", access_key="minio_admin")

    def train_model(self, train_args: dict = None):
        pass

    def prepare_torch_data_loader(self,
                                  data_set_id: str = None,
                                  path: Union[str, os.PathLike] = None,
                                  data_config: dict = None) -> DataLoader:
        """
        Create a pytorch data loader based on a specified data set id or path, applies the transforms specified
        in the lightning model to the created data set

        :param data_set_id: identifier for a data set registered at the station
        :param path: path to directory accessible to the trainer where the raw data for the data set is stored
        :param data_config: dictionary containing additional configuration parameters for the data set
        :return:
        """
        if path:
            # TODO Load data from file system
            raise NotImplementedError("Only Minio based data sets available")
        else:

            # TODO use station api to get the relevant information for a data set from the db
            if data_set_id:
                self.data_set_id = data_set_id
            # create a loader that will handle loading and preparing the data from Minio
            base_loader = BaseLoader(data_set=data_set_id,
                                     station_api=self.station_url,
                                     config=data_config,
                                     transform=self.model.make_transform())
            data_loader = base_loader.make_data_loader()
            return data_loader


if __name__ == '__main__':
    model_id = "af8c8b1e-3d89-4500-bc7d-7888e13381bd"

    trainer = ModelTrainer(model_id=model_id, station_url="http://localhost:8001")
    db_model = trainer.get_model_from_station(model_id=model_id)
    print(db_model)
