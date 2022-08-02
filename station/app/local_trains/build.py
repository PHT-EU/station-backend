import os
from typing import Union, List
import docker
from docker.models.images import Image

from station.app.local_trains.docker import make_docker_file
from station.clients.minio import MinioClient
from station.app.models.local_trains import LocalTrain


def build_train(
        train_id: str,
        master_image_id: str = None,
        entrypoint_file: str = None,
        custom_image: str = None,
        fhir_query: Union[str, dict] = None) -> Image:
    minio_client = MinioClient()

    files = minio_client.get_local_train_files(train_id)

    image = _make_train_image(train_id, files, master_image_id, entrypoint_file, custom_image)
    return image


def _make_train_image(
        train_id: str,
        files: list,
        master_image: str = None,
        entrypoint_file: str = None,
        command: str = None,
        custom_image: str = None,
        command_args: List[str] = None) -> Image:
    docker_client = docker.from_env()
    if not entrypoint_file and not custom_image:
        raise ValueError("Must specify an entrypoint file with master image or a custom image")
    if custom_image:
        image = docker_client.images.get(custom_image)
    elif master_image:
        image = master_image
        dockerfile = make_docker_file(image, entrypoint_file, command=command, command_args=command_args)
        image = docker_client.images.build(fileobj=dockerfile)
    else:
        raise ValueError("Must specify an entrypoint file with master image or a custom image")
    image.tag(repository=train_id, tag="latest")
    print(image)
    return image


def _add_train_files(docker_client: docker.DockerClient, files: list, image: str):
    container = docker_client.containers.run(image, detach=True)
    # todo make tarfile
    # todo add tarfile to container and commit to image
