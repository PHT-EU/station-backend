from station.clients.docker.client import dockerClient
from fastapi import UploadFile
from station.clients.minio.client import minio_client
import aiofiles
from os import listdir


class TrainBuilderLocal:
    def __init__(self):
        self.docker_client = dockerClient
        # TODO do over env file
        self.path_to_resources = "./app/local_train_builder/local_trains_files/"
        self.bucket_name="localtrain"
        minio_client.add_bucket(self.bucket_name)

    def build_train(self, build_data: dict):
        self.docker_client.get_master_images(build_data["masterImage"])

        docker_file_obj = self._make_dockerfile(
            master_image=build_data["masterImage"],
            executable=build_data["entrypointExecutable"],
            entrypoint_file=build_data["entrypointPath"])

    async def store_endpoint(self, upload_file: UploadFile):
        """        async with aiofiles.open(self.path_to_resources + upload_file.filename, 'wb') as save_file:
            content = await upload_file.read()
            await save_file.write(content)
            """
        await minio_client.store_files(self.bucket_name, "endpoint.py", upload_file)

    async def store_train_file(self, upload_file: UploadFile):
        #file_name = upload_file.filename.split("/")[-1]
        #print(file_name)
        await minio_client.store_files(self.bucket_name, upload_file.filename, upload_file)

    async def delete_train_file(self, file_name):
        minio_client.delete_file(self.bucket_name,file_name)

    def read_file(self,file_name):
        # TODO make it so the file name can be other or ther can be multiple fiels
        # return open(self.path_to_resources + "endpoint.py")
        return minio_client.get_file(self.bucket_name, file_name)

    def get_all_uploaded_files(self):
        print(minio_client.get_file_names(self.bucket_name))
        return minio_client.get_file_names(self.bucket_name)


train_builder_local = TrainBuilderLocal()
