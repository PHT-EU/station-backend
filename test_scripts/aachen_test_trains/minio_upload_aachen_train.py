import asyncio
from station.clients.minio.client import MinioClient
import os
from pathlib import Path


class MinioUploadAachenTrain:
    def __init__(self):
        self.bucket_name = "aachentrain"
        self.minio_client = MinioClient(minio_server="0.0.0.0:9000", access_key="minio_admin", secret_key="minio_admin")
        self.minio_client.add_bucket(self.bucket_name)
        # self.train_folder = "./pht-architecture-master-Trains-deutschebahn/deutschebahn"
        self.train_folder = "./pht-architecture-master-Trains-mukopy/mukopy"
        self.files = []

    async def load_file(self):
        for filename in list(Path(self.train_folder).rglob("*")):
            print(filename)
            f = open(os.path.join(os.getcwd(), filename), 'r')
            await self.store_train_file(f.read(), filename)
            print(f.read())

    async def store_train_file(self, file, filename):
        await self.minio_client.store_files(self.bucket_name, filename.name, file)


def main():
    minio_upload_aachen_train = MinioUploadAachenTrain()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(minio_upload_aachen_train.load_file())


if __name__ == '__main__':
    main()
