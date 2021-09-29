import tarfile
import time
import docker
import os
import io
from io import BytesIO
from docker.models.containers import Container
import asyncio
from station.clients.minio import MinioClient

class aachenClientLocalTrain:

    def __init__(self, context):
        self.docker_client = docker.from_env()
        self.minio_client = MinioClient(minio_server="127.0.0.1:9000", access_key="minio_admin",
                                        secret_key="minio_admin")
        self.train_state_dict =  context

    def build_image(self):

        docker_file = self.minio_client.get_file(self.train_state_dict["bucket"], self.train_state_dict["dockerfile"])


if __name__ == '__main__':
    context = {
      "dockerfile": "Dockerfile",
      "endpoint": "deutschebahn.py",
      "requirements": "requirements.txt",
      "dockerignore": ".dockerignore",
      "bucket": "aachentrain",
      "build_dir": "./temp/"
    }
    aachen_client_local_train = aachenClientLocalTrain(context)
    aachen_client_local_train.build_image()
