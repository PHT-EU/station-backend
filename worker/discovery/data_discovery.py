from typing import Dict, Union, List

from station.app.models.data import DataSet
from station.clients.minio import MinioClient


def perform_discovery(ds: DataSet):
    """

    :param ds:
    :return:
    """
    if ds.storage_type == "minio":
        class_dist = _minio_discovery(ds)
        return class_dist
    elif ds.storage_type == "file":
        pass
    else:
        raise NotImplementedError(f"Unsupported storage type: {ds.storage_type}")


def _minio_discovery(ds: DataSet) -> List[Dict[str, Union[int, str]]]:
    print("Performing minio discovery")
    minio_client = MinioClient()

    local_classes = minio_client.get_classes_by_folders(ds.access_path)
    class_distribution = minio_client.get_class_distributions(ds.access_path, local_classes)

    return class_distribution
