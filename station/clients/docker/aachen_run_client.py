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
        self.build_dir=  "./temp/"
        self.results =  "./result/"
        self.repo = f'aachen_{self.train_state_dict["endpoint"].lower()}_train'

    def build_image(self):

        requirements_file = self.minio_client.get_file(self.train_state_dict["bucket"],
                                                       self.train_state_dict["requirements"])
        requirements_file = BytesIO(requirements_file)
        with open(self.build_dir+self.train_state_dict["requirements"], 'wb') as f:
            f.write(requirements_file.getbuffer())

        dockerignore_file = self.minio_client.get_file(self.train_state_dict["bucket"],
                                                       self.train_state_dict["dockerignore"])
        dockerignore_file = BytesIO(dockerignore_file)
        with open(self.build_dir+self.train_state_dict["dockerignore"], 'wb') as f:
            f.write(dockerignore_file.getbuffer())

        docker_file = self.minio_client.get_file(self.train_state_dict["bucket"], self.train_state_dict["dockerfile"])
        docker_file = BytesIO(docker_file)
        with open(self.build_dir+self.train_state_dict["dockerfile"], 'wb') as f:
            f.write(docker_file.getbuffer())

        image, logs = self.docker_client.images.build(path=self.build_dir, labels=self.train_state_dict["label"])
        container = self.docker_client.containers.create(image.id)

        endpoint = self.minio_client.get_file(self.train_state_dict["bucket"], self.train_state_dict["endpoint"])

        tarfile_name = f'{self.train_state_dict["endpoint"]}.tar'
        with tarfile.TarFile(tarfile_name, 'w') as tar:
            data_file = tarfile.TarInfo(name=self.train_state_dict["endpoint"])
            data_file.size = len(endpoint)
            tar.addfile(data_file, io.BytesIO(endpoint))

        with open(tarfile_name, 'rb') as fd:
            respons = container.put_archive("/", fd)
            container.wait()
            print(respons)
        container.commit(repository=self.repo, tag="latest")
        container.wait()

    def run_train(self):
        container = self.docker_client.containers.run(self.repo,labels= self.train_state_dict["label"], detach=True)
        exit_code = container.wait()["StatusCode"]
        print(self.train_state_dict["label"])
        print(f"{exit_code} run fin")
        f = open(f'results.tar', 'wb')
        results = container.get_archive('./')
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
      "endpoint": "mukoWithPython.py",
      "requirements": "requirements.txt",
      "dockerignore": ".dockerignore",
      "bucket": "aachentrain",
      "build_dir": "./temp/",
      "label": {"FHIR_SERVER" :"137.226.232.119" , "FHIR_PORT" :"8080"}
    }
    aachen_client_local_train = aachenClientLocalTrain(context)
    aachen_client_local_train.build_image()
    aachen_client_local_train.run_train()
    aachen_client_local_train.save_results()
