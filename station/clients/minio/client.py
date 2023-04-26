import tarfile
import time
from io import BufferedReader, BytesIO, TextIOWrapper
from typing import Dict, List, Union
from zipfile import ZipFile

import pendulum
import starlette
from fastapi import File, UploadFile
from loguru import logger
from minio import Minio
from minio.error import S3Error
from pydantic import SecretStr

from station.app.schemas.datasets import MinioFile
from station.app.schemas.station_status import HealthStatus
from station.ctl.constants import DataDirectories


class MinioClient:
    def __init__(
        self, minio_server: str = None, access_key: str = None, secret_key: str = None
    ):
        """
        Initialize a minio client either with the values passed to the constructor or based on environment variables

        :param minio_server: endpoint of the minio server
        :param access_key: minio access key or username
        :param secret_key: minio password
        """
        # Initialize class fields based on constructor values or environment variables

        # if settings.config.minio.port:
        #     minio_url = f"{settings.config.minio.host}:{settings.config.minio.port}"
        # else:
        #     minio_url = settings.config.minio.host
        # minio_user = settings.config.minio.access_key
        # minio_pass = settings.config.minio.secret_key

        self.minio_server = minio_server
        self.access_key = access_key
        self.secret_key = secret_key

        if isinstance(self.secret_key, SecretStr):
            self.secret_key = self.secret_key.get_secret_value()

        assert self.minio_server
        assert self.access_key
        assert self.secret_key

        # Initialize minio client
        self.client = Minio(
            self.minio_server,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False,
        )

    async def store_model_file(self, id: str, model_file: Union[File, UploadFile]):
        model_data = await model_file.read()
        file = BytesIO(model_data)
        res = self.client.put_object(
            DataDirectories.MODELS.value,
            object_name=id,
            data=file,
            length=len(file.getbuffer()),
        )
        return res

    def get_model_file(self, model_id: str) -> bytes:
        try:
            response = self.client.get_object(
                bucket_name=DataDirectories.MODELS.value, object_name=model_id
            )
            data = response.read()
        finally:
            response.close()
            response.release_conn()

        return data

    async def store_files(self, bucket: str, name: str, file: Union[File, UploadFile]):
        """
        store files into minio
        """
        print(name)
        print(type(file))
        if isinstance(file, BufferedReader):
            model_data = file.read()
        elif isinstance(file, str):
            model_data = file.encode("utf-8")
        elif isinstance(file, TextIOWrapper):
            model_data = file.read().encode("utf-8")
        elif isinstance(file, BytesIO):
            res = self.client.put_object(
                bucket, object_name=name, data=file, length=len(file.getbuffer())
            )
            return res
        elif isinstance(file, starlette.datastructures.UploadFile):
            model_data = await file.read()
        else:
            raise TypeError(f"files with type {type(file)} are not supported")

        file = BytesIO(model_data)
        res = self.client.put_object(
            bucket, object_name=name, data=file, length=len(file.getbuffer())
        )
        return res

    async def save_dataset_files(
        self, dataset_id: str, files: List[Union[File, UploadFile]]
    ):
        """
        store files into minio
        """
        resp = []

        for file in files:
            data = await file.read()

            data_file = BytesIO(data)
            res = self.client.put_object(
                bucket_name=DataDirectories.DATASETS.value,
                object_name=f"{dataset_id}/{file.filename}",
                data=data_file,
                length=len(data),
                content_type="text/plain",
            )
            resp.append(res)
            data_file.seek(0)

        return resp

    async def save_local_train_files(
        self, train_id: str, files: List[Union[File, UploadFile]]
    ) -> List[MinioFile]:
        """
        store files of local train in minio
        """
        resp = []

        for file in files:
            data = await file.read()
            data_file = BytesIO(data)
            res = self.client.put_object(
                bucket_name=DataDirectories.LOCAL_TRAINS.value,
                object_name=f"{train_id}/{file.filename}",
                data=data_file,
                length=len(data),
            )

            resp.append(
                MinioFile(
                    file_name=file.filename,
                    file_size=len(data),
                    full_path=f"{res.bucket_name}/{res.object_name}",
                    updated_at=pendulum.now(),
                )
            )
        return resp

    def get_local_train_archive(self, train_id: str):
        print(DataDirectories.LOCAL_TRAINS.value)
        items = self.get_minio_dir_items(
            bucket=DataDirectories.LOCAL_TRAINS.value, directory=train_id
        )

        archive = self.make_download_archive(
            DataDirectories.LOCAL_TRAINS.value, items=items
        )

        return archive

    def get_file(self, bucket: str, name: str) -> bytes:
        response = self.client.get_object(bucket_name=bucket, object_name=name)
        data = response.read()
        response.close()
        response.release_conn()

        return data

    def delete_file(self, bucket: str, name: str):
        self.client.remove_object(bucket_name=bucket, object_name=name)

    def delete_folder(self, bucket: str, directory: str):
        delete_objects = self.client.list_objects(
            bucket_name=bucket, prefix=directory, recursive=True
        )
        for obj in delete_objects:
            self.client.remove_object(bucket_name=bucket, object_name=obj.object_name)

    def get_file_names(self, bucket: str, prefix: str = "") -> List[str]:
        response = self.client.list_objects(bucket, prefix=prefix)
        data = list(response)
        return data

    def add_bucket(self, bucket_name: str):
        found = self.client.bucket_exists(bucket_name)
        if not found:
            self.client.make_bucket(bucket_name)

    def list_data_sets(self):
        data_sets = self.client.list_objects("datasets")
        return [ds.object_name for ds in list(data_sets)]

    def list_buckets(self):
        buckets = self.client.list_buckets()
        return buckets

    def list_elements_in_bucket(self, bucket):
        elements = self.client.list_objects(bucket)
        return [ds.object_name for ds in list(elements)]

    def load_data_set(self):
        pass

    def get_minio_dir_items(
        self, bucket: Union[str, DataDirectories], directory: str
    ) -> List[MinioFile]:
        """
        Get all objects in the data set specified by data_set_id and return them as a generator
        Args:
            bucket:
            directory:

        Returns:

        """
        if isinstance(bucket, DataDirectories):
            bucket = bucket.value
        items = self.client.list_objects(bucket, prefix=directory, recursive=True)
        try:
            dir_files = []
            for item in items:
                print(item)
                dir_files.append(
                    MinioFile(
                        file_name=item.object_name.split("/")[-1],
                        full_path=item.object_name,
                        size=item.size,
                        updated_at=item.last_modified,
                    )
                )
            return dir_files
        except Exception as e:
            print(e)
            return []

    def make_dataset_archive(
        self, data_set_id: str, items: List[MinioFile] = None, archive_type: str = "tar"
    ) -> BytesIO:
        """
        Create an archive of the data set specified by data_set_id and return it as a BytesIO object
        Args:
            data_set_id: id of the dataset
            items: list of items to include in the archive
            archive_type: tar or zip

        Returns:

        """
        if items is None:
            items = self.get_minio_dir_items("datasets", data_set_id)

        archive = self.make_download_archive(
            "datasets", items, archive_type=archive_type
        )

        return archive

    def make_download_archive(
        self, bucket: str, items: List[MinioFile], archive_type: str = "tar"
    ) -> BytesIO:
        archive = BytesIO()

        if archive_type == "tar":
            with tarfile.TarFile(fileobj=archive, mode="w") as tar:
                for file in items:
                    data = self.get_file(bucket, file.full_path)
                    info = tarfile.TarInfo(name=file.full_path)
                    info.size = len(data)
                    info.mtime = time.time()
                    tar.addfile(info, BytesIO(data))

            archive.seek(0)
            return archive
        elif archive_type == "zip":
            with ZipFile(archive, "w") as zip:
                for item in items:
                    data = self.get_file(bucket, item.full_path)
                    zip.writestr(item.full_path, data)
            archive.seek(0)
            return archive

        raise ValueError(f"Unknown archive type {archive_type}")

    def get_classes_by_folders(self, data_set_id: str) -> List[str]:
        """
        Gets the subdirectories of a dataset directory in minio. The folder names correspond the classes defined for
        the dataset

        :param data_set_id: identifier of the data set in the datasets bucket
        :return: List of directory (class) names found in the specified directory
        """

        folders = self.client.list_objects(
            "datasets", prefix=data_set_id, recursive=False
        )
        classes = []
        for folder in folders:
            classes.append(folder.object_name.split("/")[-2])
        return classes

    def get_class_distributions(
        self, data_set_id: str, classes: List[str]
    ) -> List[Dict[str, Union[int, str]]]:
        class_distribution = []

        for cls in classes:
            prefix = data_set_id + cls + "/"
            class_items = len(list(self.client.list_objects("datasets", prefix=prefix)))
            class_object = {"class_name": cls, "n_items": class_items}
            class_distribution.append(class_object)

        return class_distribution

    def health_check(self) -> HealthStatus:
        """
        Get health of minio
        """
        try:
            self.client.list_buckets()

            return HealthStatus.healthy
        except Exception as e:
            logger.error(f"Error while checking minio health: {e}")
            return HealthStatus.error

    def setup_buckets(self):
        for d in DataDirectories:
            try:
                self.client.make_bucket(d.value)
            except S3Error as se:
                if se.code == "BucketAlreadyOwnedByYou":
                    pass
                else:
                    raise se
            except Exception as e:
                raise e
