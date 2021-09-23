import docker
import os
#from station.clients.minio import MinioClient

class DockerClientLocalTrain:

    def __init__(self, context):
        repository, tag, env, volumes, build_dir = [context['dag_run'].conf.get(_, None) for _ in
                                                    ['repository', 'tag', 'env', 'volumes', 'build_dir']]
        if repository is None:
            # docker pull harbor-pht.tada5hi.net/master/python/ubuntu@sha256:490012782ddf22e66c556ef837209cb75d4644430286b70f50f4b4edcdfdcc64
            repository = "harbor-pht.tada5hi.net/master/python/ubuntu"
        if tag is None:
            tag = "latest"
        img = repository + ":" + tag
        self.bucket_name = "localtrain"
        self.train_state_dict = {
            "repository": repository,
            "tag": tag,
            "img": img,
            "env": env,
            "volumes": volumes,
            "build_dir": build_dir,
        }
        self.client = docker.from_env()
        #self.minio_client = MinioClient(minio_server = "0.0.0.0:9000")

    def pull_master_image(self):
        harbor_address = os.getenv("HARBOR_API_URL")
        print(harbor_address)
        self.client.login(username=os.getenv("HARBOR_USER"), password=os.getenv("HARBOR_PW"),
                          registry=harbor_address)
        self.client.images.pull(repository=self.get_repository(), tag=self.get_tag())
        print("DAG run")
        images = self.client.images.list()
        print(images)

    def build_train(self):
        #self._make_build_file()
        self._get_run_files()
        image, logs = self.client.images.build(path=self.train_state_dict["build_dir"])
        image.run()

    def run(self):
        pass

    def save_results(self):
        pass

    def _get_run_files(self):
        #TODO make selectet by configuraion.
        #print(minio_client.get_file_names(self.bucket_name))
        #endpoint_file = minio_client.get_file(self.bucket_name, "endpoint.py")
        pass

    def _make_build_file(self):
        path = os.getcwd()
        print(path)
        os.mkdir(self.train_state_dict["build_dir"])
        with open(os.path.join(os.path.abspath(self.train_state_dict["build_dir"]), "Dockerfile"), "w") as df:
            df.write("From " + self.train_state_dict["img"] + "\n")
            df.write("COPY " + "endpoint.py" + "/opt/pht_train\n")
            df.write("RUN mkdir /opt/pht_results\n")
            df.write('CMD ["python", "/opt/pht_train/endpoint.py"]')

        print(os.path.join(os.path.abspath(self.train_state_dict["build_dir"]), "Dockerfile"))

    def get_repository(self):
        return self.train_state_dict["repository"]

    def get_tag(self):
        return self.train_state_dict["tag"]
