from abc import ABC
from typing import Iterator, Generator, List
import torch
from torch.utils.data import Dataset, IterableDataset, DataLoader
from torch.utils.data.dataset import T_co
from minio import datatypes
from PIL import Image
from torchvision.transforms import Compose, ToTensor, CenterCrop
import numpy as np
from conductor_lib.src.torch import LightningTrainModel

from station.clients.minio import MinioClient


class BaseDataSet(Dataset, ABC):
    id: str


class MinioFolderDataSet(IterableDataset):

    def __init__(self, minio_client: MinioClient, id: str = None, transform: Compose = None):
        super(MinioFolderDataSet, self).__init__()
        self.id = id
        self.client = minio_client
        self.transform = transform

    def __iter__(self) -> Iterator[T_co]:
        worker_info = torch.utils.data.get_worker_info()

        if worker_info is None:
            return self._make_generator()

        else:
            print(worker_info.num_workers)
            # TODO
            raise NotImplementedError("Implement sliced generators for multiworker loading")

    def _make_generator(self, id: str = None):
        if id:
            self.id = id
        minio_items = self._get_minio_items()

        tensor_generator = self._make_image_generator(minio_items)
        return tensor_generator

    def _get_minio_items(self) -> Generator[datatypes.Object, None, None]:
        items = self.client.get_data_set_items(self.id)
        return items

    def _make_image_generator(self,
                              minio_items: Generator[datatypes.Object, None, None]
                              ) -> Generator[torch.Tensor, None, None]:
        for i, object in enumerate(minio_items):
            minio_object = self.client.client.get_object("data-sets", object.object_name)
            np_img = np.array(Image.open(minio_object))

            print(object.object_name)

            if self.transform:
                yield self.transform(np_img)
            else:
                yield np_img


class MinioFolderDS(Dataset):

    # TODO generalized target creation

    def __init__(self, client: MinioClient, data_set_id: str = None, transform: Compose = None,
                 target_classes: List[str] = None):
        super().__init__()
        self.data_set_id = data_set_id
        self.minio_client = client
        self.transform = transform
        self.items = None

        self.get_minio_items()

        if target_classes:
            self.classes = np.asarray(target_classes)
        else:
            self.classes = self.get_classes_from_folders()

    def __getitem__(self, index) -> T_co:
        minio_object = self.minio_client.client.get_object("datasets", self.items[index])
        np_img = np.array(Image.open(minio_object))
        np_img = np.transpose(np_img.astype(float), (2, 1, 0))
        label = self.get_label(self.items[index])
        if self.transform:
            return self.transform(np_img), label
        return torch.Tensor(np_img), label

    def __len__(self):
        return len(list(self.items))

    def get_label(self, item_name: str):
        folder = item_name[len(self.data_set_id):].split("/")[0]
        label = self.classes == folder
        return torch.tensor(label, dtype=torch.long)

    def get_minio_items(self):
        minio_items = self.minio_client.get_data_set_items(self.data_set_id)
        item_list = []
        for item in minio_items:
            item_list.append(item.object_name)

        self.items = item_list

    def save(self):

        # TODO Save the full data set to disk somewhere to enable fast loading
        pass

    def get_classes_from_folders(self):
        classes = self.minio_client.get_classes_by_folders(self.data_set_id)
        print(classes)
        return np.asarray(classes)

if __name__ == '__main__':
    minio_client = MinioClient(minio_server="localhost:9000",
                               secret_key="minio_admin", access_key="minio_admin")

    transform = Compose([ToTensor(), CenterCrop(size=24)])
    minio_ds = MinioFolderDS(client=minio_client, data_set_id="cifar/batch_2", transform=transform)
    minio_ds.get_minio_items()
    print(len(minio_ds))

    dl = DataLoader(minio_ds, batch_size=6, num_workers=0, shuffle=True)

    for i, batch in enumerate(dl):
        x, y = batch
        print(y)
        if i > 3:
            break
