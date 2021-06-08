from io import BytesIO

from minio import Minio
import os
from fastapi import File, UploadFile
from typing import List, Union, Dict
from dotenv import load_dotenv, find_dotenv
from uuid import uuid4
import pickle
import dill


class MinioClient:

    def __init__(self, minio_server: str = None, access_key: str = None, secret_key: str = None):
        """
        Initialize a minio client either with the values passed to the constructor or based on environment variables

        :param minio_server: endpoint of the minio server
        :param access_key: minio access key or username
        :param secret_key: minio password
        """
        # Initialize class fields based on constructor values or environment variables
        self.minio_server = minio_server if minio_server else os.getenv("MINIO_URL")
        self.access_key = access_key if access_key else os.getenv("MINIO_USER")
        self.secret_key = secret_key if secret_key else os.getenv("MINIO_PW")

        assert self.minio_server
        assert self.access_key
        assert self.secret_key


        # Initialize minio client
        self.client = Minio(
            self.minio_server,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False
        )

        self._init_server()

    async def store_model_file(self, id: str, model_file: Union[File, UploadFile]):
        model_data = await model_file.read()
        file = BytesIO(model_data)
        res = self.client.put_object("models", object_name=id, data=file, length=len(file.getbuffer()))
        return res

    def get_model_file(self, model_id: str) -> bytes:
        try:
            response = self.client.get_object(bucket_name="models", object_name=model_id)
            data = response.read()
        finally:
            response.close()
            response.release_conn()

        return data

    def _init_server(self):
        """
        Checks if the required buckets are present on the minio server and creates them if necessary

        :return:
        """
        # Create a Minio Bucket for station models
        found = self.client.bucket_exists("models")
        if not found:
            print("Creating minio bucket for models")
            self.client.make_bucket("models")
        # Create bucket for data sets
        found = self.client.bucket_exists("datasets")
        if not found:
            print("Creating minio bucket for data sets")
            self.client.make_bucket("datasets")

    def list_data_sets(self):
        data_sets = self.client.list_objects("datasets")
        return [ds.object_name for ds in list(data_sets)]

    def list_buckets(self):
        buckets = self.client.list_buckets()

        return buckets

    def load_data_set(self):
        pass

    def get_data_set_items(self, data_set_id: str):
        """
        Get all objects in the data set specified by data_set_id and return them as a generator

        :param data_set_id:
        :return:
        """
        items = self.client.list_objects("datasets", prefix=data_set_id, recursive=True)
        return items

    def get_classes_by_folders(self, data_set_id: str) -> List[str]:
        """
        Gets the subdirectories of a dataset directory in minio. The folder names correspond the classes defined for
        the dataset

        :param data_set_id: identifier of the data set in the datasets bucket
        :return: List of directory (class) names found in the specified directory
        """

        folders = self.client.list_objects("datasets", prefix=data_set_id, recursive=False)
        classes = []
        for folder in folders:
            classes.append(folder.object_name.split("/")[-2])
        return classes

    def get_class_distributions(self, data_set_id: str, classes: List[str]) -> List[Dict[str, Union[int, str]]]:

        class_distribution = []

        for cls in classes:
            prefix = data_set_id + cls + "/"
            class_items = len(list(self.client.list_objects("datasets", prefix=prefix)))
            class_object = {
                "class_name": cls,
                "n_items": class_items
            }
            class_distribution.append(class_object)

        return class_distribution


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    minio_client = MinioClient()
