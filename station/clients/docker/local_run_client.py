import docker
import os


class DockerClientLocalTrain:

    def __init__(self, context):
        repository, tag, env, volumes = [context['dag_run'].conf.get(_, None) for _ in
                                         ['repository', 'tag', 'env', 'volumes']]
        img = repository + ":" + tag

        self.train_state_dict = {
            "repository": repository,
            "tag": tag,
            "img": img,
            "env": env,
            "volumes": volumes
        }
        self.client = docker.from_env()

    def pull_master_image(self):
        harbor_address = os.getenv("HARBOR_API_URL")
        self.client.login(username=os.getenv("HARBOR_USER"), password=os.getenv("HARBOR_PW"),
                          registry=harbor_address)
        self.client.images.pull(repository=self.get_repository(), tag=self.get_tag())
        print("DAG run")
        images = self.client.images.list()
        print(images)

    def build_train(self):
        self._make_build_file()

    def run(self):
        pass

    def save_results(self):
        pass

    def _make_build_file(self):
        pass


    def get_repository(self):
        return self.train_state_dict["repository"]

    def get_tag(self):
        return self.train_state_dict["tag"]
