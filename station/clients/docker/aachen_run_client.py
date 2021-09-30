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
        files  = self.minio_client.get_file_names(self.train_state_dict["bucket"])
        for file in files:
            print(file.object_name)
        docker_file = self.minio_client.get_file(self.train_state_dict["bucket"], self.train_state_dict["dockerfile"])
        docker_file = BytesIO(docker_file)
        image, logs = self.docker_client.images.build(fileobj=docker_file)
        container = self.docker_client.containers.create(image.id)

        endpoint = self.minio_client.get_file(self.train_state_dict["bucket"], self.train_state_dict["endpoint"])
        print(image.id)

        tarfile_name = f'{self.train_state_dict["endpoint"]}.tar'
        with tarfile.TarFile(tarfile_name, 'w') as tar:
            data_file = tarfile.TarInfo(name=self.train_state_dict["endpoint"])
            data_file.size = len(endpoint)
            tar.addfile(data_file, io.BytesIO(endpoint))

        with open(tarfile_name, 'rb') as fd:
            respons = container.put_archive("/", fd)
            container.wait()
            print(respons)
        container.commit(repository=f'aachen_{self.train_state_dict["endpoint"]}_train', tag="latest")
        container.wait()

    def run_train(self):
        container = self.docker_client.containers.run("local_train", detach=True)
        exit_code = container.wait()["StatusCode"]
        print(f"{exit_code} run fin")
        f = open(f'results.tar', 'wb')
        results = container.get_archive('/')
        bits, stat = results
        for chunk in bits:
            f.write(chunk)
        f.close()

    def save_results(self):
        with open(f'results.tar', 'rb') as results_tar:
            asyncio.run(
                self.minio_client.store_files(bucket=self.train_state_dict["bucket"], name="results.tar", file=results_tar))


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
    #aachen_client_local_train.run_train()
    #aachen_client_local_train.save_results()
