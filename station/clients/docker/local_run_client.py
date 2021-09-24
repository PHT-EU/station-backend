import tarfile

import docker
import os
import io
from io import BytesIO
from docker.models.containers import Container

from station.clients.minio import MinioClient

class DockerClientLocalTrain:

    def __init__(self, context):
        self.docker_client = docker.from_env()
        self.minio_client = MinioClient(minio_server="minio:9000")
        repository, tag, env, volumes, build_dir = [context['dag_run'].conf.get(_, None) for _ in
                                                    ['repository', 'tag', 'env', 'volumes', 'build_dir']]

        img = repository + ":" + tag
        self.bucket_name = "localtrain"
        if  not os.path.isdir(build_dir):
            os.mkdir(build_dir)
        self.train_state_dict = {
            "repository": repository,
            "tag": tag,
            "img": img,
            "env": env,
            "volumes": volumes,
            "build_dir": build_dir,
        }
        self.image = None

    def pull_master_image(self):
        harbor_address = os.getenv("HARBOR_API_URL")
        print(harbor_address)
        self.docker_client.login(username=os.getenv("HARBOR_USER"), password=os.getenv("HARBOR_PW"),
                                 registry=harbor_address)
        self.docker_client.images.pull(repository=self.get_repository(), tag=self.get_tag())
        print("DAG run")
        images = self.docker_client.images.list()
        print(images)

    def build_train(self):
        docker_file = self._make_build_file()
        self.image, logs = self.docker_client.images.build(fileobj=docker_file)
        container = self.docker_client.containers.create(self.image.id)
        self._add_run_files(container)


    def run(self):
        self.docker_client.containers.run(image=self.image)


    def save_results(self):
        pass

    def _add_run_files(self,container):
        #TODO make selectet by configuraion.
        tar = self._minIO_bytes_to_tar( self.minio_client.get_file(self.bucket_name, "endpoint.py"), "endpoint.py")
        tar.
        container.put_archive("/opt/pht_train",  tar)
        container.wait()


    def _make_build_file(self):
        docker_file = f'''
                    FROM {self.train_state_dict["img"]}
                    RUN mkdir /opt/pht_results
                    RUN mkdir /opt/pht_train
                    RUN chmod -R +x /opt/pht_train
                    CMD ["python", "/opt/pht_train/endpoint.py"]
                    '''
        file_obj = BytesIO(docker_file.encode("utf-8"))

        return file_obj

    def _minIO_bytes_to_tar(self,bytes , name):
        data = io.BytesIO(bytes)
        return tarfile.open(name=name , fileobj=data, mode="w")

    def get_repository(self):
        return self.train_state_dict["repository"]

    def get_tag(self):
        return self.train_state_dict["tag"]
