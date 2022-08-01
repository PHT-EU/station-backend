import os
from typing import Union
import docker

from station.clients.minio import MinioClient
from station.app.models.local_trains import LocalTrain


def build_train(
        train_id: str,
        master_image_id: str = None,
        entrypoint_file: str = None,
        custom_image: str = None,
        fhir_query: Union[str, dict] = None) -> None:
    minio_client = MinioClient()

    files = minio_client.get_local_train_files(train_id)

    image = _make_train_image(files, master_image_id, entrypoint_file, custom_image, fhir_query)


def _make_train_image(files: list, master_image: str = None, entrypoint_file: str = None, custom_image: str = None,
                      fhir_query: Union[str, dict] = None):
    docker_client = docker.from_env()
    if custom_image:
        image = custom_image
    else:
        image = master_image

    return image


def _add_train_files(docker_client: docker.DockerClient, files: list, image: str):
    container = docker_client.containers.run(image, detach=True)
    # todo make tarfile
    # todo add tarfile to container and commit to image
