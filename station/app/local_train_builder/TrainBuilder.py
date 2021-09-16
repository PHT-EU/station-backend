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
        minio_client.add_bucket("localtrain")

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
        await minio_client.store_files("localtrain", "endpoint.py", upload_file)

    def read_endpoint(self):
        # TODO make it so the file name can be other or ther can be multiple fiels
        # return open(self.path_to_resources + "endpoint.py")
        print(minio_client.list_buckets())
        print(minio_client.list_elements_in_bucket("localtrain"))
        return minio_client.get_file("localtrain", "endpoint.py")

    def get_all_uploaded_files(self):
        return listdir(self.path_to_resources)


train_builder_local = TrainBuilderLocal()
