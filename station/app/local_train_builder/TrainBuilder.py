from station.clients.docker.client import dockerClient


class TrainBuilderLocal:
    def __init__(self):
        self.docker_client = dockerClient

    def build_train(self,build_data:dict):

        self.docker_client.get_master_images(build_data["masterImage"])

        docker_file_obj = self._make_dockerfile(
            master_image=build_data["masterImage"],
            executable=build_data["entrypointExecutable"],
            entrypoint_file=build_data["entrypointPath"])


