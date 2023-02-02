import os
from typing import Union

import pytorch_lightning as pl
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms import Compose, ToTensor

from station.clients.minio import MinioClient
from station.worker.loader.dataset import MinioFolderDS


class BaseLoader:
    def __init__(
        self,
        data_set: Union[Dataset, str] = None,
        station_api: str = None,
        config: dict = None,
        transform: Compose = None,
    ):

        self.station_api = station_api if station_api else os.getenv("STATION_API_URL")
        self.data_set = data_set
        self.transform = transform
        self.config = config
        # TODO fix minio
        self.minio_client = MinioClient()

    def make_data_loader(self) -> DataLoader:
        """
        Create a pytorch data loder based on this instance's fields, either takes a data set directly passed
        to the constructor or loads the data set from Minio if the given data set is specified as a string identifier

        :return: pytorch Dataloader to be used in model training
        """
        if isinstance(self.data_set, str):
            # Get data from db
            self.data_set = self.get_data_set()
        if self.config:
            return DataLoader(self.data_set, **self.config)
        return DataLoader(self.data_set)

    def make_lightning_data_module(self) -> pl.LightningDataModule:
        pass

    def get_data_set(self):
        # TODO enable different data set types
        dataset = MinioFolderDS(
            client=self.minio_client,
            data_set_id=self.data_set,
            transform=self.transform,
        )
        return dataset


if __name__ == "__main__":

    transform = Compose([ToTensor()])

    loader = BaseLoader(
        data_set="cifar/batch_1",
        transform=transform,
        config={"batch_size": 6, "num_workers": 0},
    ).make_data_loader()
    for i, batch in enumerate(loader):
        print(batch.size())
        if i > 3:
            break
