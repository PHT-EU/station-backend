from station.app.config import settings
from station.clients.docker.client import dockerClient
from fastapi import UploadFile
from station.clients.minio.client import MinioClient
from minio.error import MinioException


class LocalTrainMinIO:
    def __init__(self):
        self.minio_client = MinioClient()
        self.docker_client = dockerClient
        # TODO do over env file

        self.bucket_name = "localtrain"
        self.minio_client.add_bucket(self.bucket_name)

    async def store_endpoint(self, upload_file: UploadFile, train_id: str):
        await self.minio_client.store_files(self.bucket_name, f"{train_id}/endpoint.py", upload_file)

    async def store_train_file(self, upload_file: UploadFile, train_id: str):
        print(f"{train_id}/{upload_file.filename}")
        await self.minio_client.store_files(self.bucket_name, f"{train_id}/{upload_file.filename}", upload_file)

    async def delete_train_file(self, file_name):
        self.minio_client.delete_file(self.bucket_name, file_name)

    def read_file(self, file_name):
        # TODO make it so the file name can be other or ther can be multiple fiels
        # return open(self.path_to_resources + "endpoint.py")
        try:
            file = self.minio_client.get_file(self.bucket_name, file_name)
        except MinioException as e:
            print(e)
            return None
        return file

    def get_results(self, train_id):
        file = self.minio_client.get_file(self.bucket_name, f"{train_id}/results.tar")
        return file

    def get_all_uploaded_files(self):
        print(self.minio_client.get_file_names(self.bucket_name))
        return self.minio_client.get_file_names(self.bucket_name)

    def get_all_uploaded_files_train(self, train_id: str):
        """
        Returns all files stord in for the selected given train
        @param train_id: uid for of the train
        @return: json with file information
        """
        files = self._get_all_files_recursively(f"{train_id}/")

        return files

    def _get_all_files_recursively(self, subfolder):
        """
        returns all files in a folder if ther are subfolders it returns the files in the subfolder
        @param subfolder:
        @return:
        """
        files = self.minio_client.get_file_names(self.bucket_name, subfolder)
        out_files = []
        for file in files:
            if file._object_name[-1] == "/":
                out_files.extend(self._get_all_files_recursively(file._object_name))
            else:
                out_files.append(file)

        return out_files


train_data = LocalTrainMinIO()
