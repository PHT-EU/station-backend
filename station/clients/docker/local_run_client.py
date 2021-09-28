import tarfile
import time
import docker
import os
import io
from io import BytesIO
from docker.models.containers import Container
import asyncio
from station.clients.minio import MinioClient


class DockerClientLocalTrain:

    def __init__(self, context):
        self.docker_client = docker.from_env()
        # for use in airflow
        # self.minio_client = MinioClient(minio_server="minio:9000")
        self.minio_client = MinioClient(minio_server="127.0.0.1:9000", access_key="minio_admin",
                                        secret_key="minio_admin")
        # repository, tag, env, volumes, build_dir = [context['dag_run'].conf.get(_, None) for _ in
        #                                            ['repository', 'tag', 'env', 'volumes', 'build_dir']]
        ## local
        repository = context["repository"]
        tag = context["tag"]
        env = None
        volumes = None
        build_dir = context["build_dir"]

        ##local
        img = repository + ":" + tag
        self.bucket_name = "localtrain"
        if not os.path.isdir(build_dir):
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
        print(self.image.id)
        self._add_run_files(container)
        container.commit(repository="local_train", tag="latest")
        container.wait()

    def run(self):
        print("run")
        container = self.docker_client.containers.run("local_train", detach=True)
        exit_code = container.wait()["StatusCode"]
        print(f"{exit_code} run fin")
        f = open(f'{self.train_state_dict["build_dir"]}results.tar', 'wb')
        results = container.get_archive('opt/pht_results')
        bits, stat = results
        for chunk in bits:
            f.write(chunk)
        f.close()

    def save_results(self):
        with open(f'{self.train_state_dict["build_dir"]}results.tar', 'rb') as results_tar:
            asyncio.run(self.minio_client.store_files(bucket=self.bucket_name, name="results.tar", file=results_tar))

    def _add_run_files(self, container):
        # TODO make selectet by configuraion.
        tar = self._minIO_bytes_to_tar(self.minio_client.get_file(self.bucket_name, "endpoint.py"), "endpoint.py")
        with open(tar, 'rb') as fd:
            respons = container.put_archive("/opt/pht_train", fd)
            container.wait()

        print(f"{respons = }")

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

    def _minIO_bytes_to_tar(self, bytes, name):
        tarfile_name = f"{name}.tar"
        with tarfile.TarFile(tarfile_name, 'w') as tar:
            data_file = tarfile.TarInfo(name='endpoint.py')
            data_file.size = len(bytes)
            tar.addfile(data_file, io.BytesIO(bytes))

        return tarfile_name

    def get_repository(self):
        return self.train_state_dict["repository"]

    def get_tag(self):
        return self.train_state_dict["tag"]


if __name__ == '__main__':
    context = {
        "repository": "harbor-pht.tada5hi.net/master/python/ubuntu",
        "tag": "latest",
        "build_dir": "./temp/"
    }
    local_train_client = DockerClientLocalTrain(context)
    local_train_client.pull_master_image()
    local_train_client.build_train()
    local_train_client.run()
    local_train_client.save_results()
