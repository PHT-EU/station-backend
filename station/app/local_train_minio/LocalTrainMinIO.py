from station.clients.docker.client import dockerClient
from fastapi import UploadFile
from station.clients.minio.client import MinioClient
from  minio.error import MinioException
import aiofiles
from os import listdir


class LocalTrainMinIO:
    def __init__(self):
        self.minio_client = MinioClient()
        self.docker_client = dockerClient
        # TODO do over env file

        self.bucket_name="localtrain"
        self.minio_client.add_bucket(self.bucket_name)

    async def store_endpoint(self, upload_file: UploadFile, train_id: str):
        await self.minio_client.store_files(self.bucket_name, f"{train_id}/endpoint.py", upload_file)

    async def store_train_file(self, upload_file: UploadFile, train_id: str):
        print(f"{train_id}/{upload_file.filename}")
        await self.minio_client.store_files(self.bucket_name, f"{train_id}/{upload_file.filename}", upload_file)

    async def delete_train_file(self, file_name):
        self.minio_client.delete_file(self.bucket_name,file_name)

    def read_file(self,file_name):
        # TODO make it so the file name can be other or ther can be multiple fiels
        # return open(self.path_to_resources + "endpoint.py")
        try:
            file = self.minio_client.get_file(self.bucket_name, file_name)
        except MinioException as e:
            print(e)
            return None
        return file

    def get_results(self,train_id):
        file = self.minio_client.get_file(self.bucket_name, f"{train_id}/results.tar")
        return file

    def get_all_uploaded_files(self):
        print(self.minio_client.get_file_names(self.bucket_name))
        return self.minio_client.get_file_names(self.bucket_name)

    def get_all_uploaded_files_train(self, train_id: str):
        return self.minio_client.get_file_names(self.bucket_name, f"{train_id}/")


train_data = LocalTrainMinIO()
