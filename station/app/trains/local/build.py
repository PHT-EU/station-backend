import os
from io import BytesIO
from typing import Union, List
import docker
from docker.models.images import Image
from sqlalchemy.orm import Session
from train_lib.docker_util.docker_ops import add_archive

from station.app.trains.local.docker import make_docker_file
from station.clients.minio import MinioClient
from station.app.models.local_trains import LocalTrain
from station.app.crud.crud_local_train import CRUDLocalTrain
from loguru import logger


def build_train(
        db: Session,
        train_id: str,
        master_image_id: str = None,
        files: BytesIO = None,
        custom_image: str = None,
) -> str:
    if master_image_id and not files:
        raise ValueError("Must specify files with master image")

    local_crud = CRUDLocalTrain(LocalTrain)
    train = local_crud.get(db, train_id)

    print(train.entrypoint)

    image = _make_train_image(
        train_id=train_id,
        master_image=master_image_id,
        entrypoint_file=train.entrypoint,
        custom_image=custom_image,
        command=train.command,
        command_args=train.command_args
    )

    image = _add_train_files(files=files, image=image)

    return image


def _make_train_image(
        train_id: str,
        master_image: str = None,
        entrypoint_file: str = None,
        custom_image: str = None,
        command: str = None,
        command_args: Union[List[str], str] = None) -> Image:
    docker_client = docker.from_env()
    if not entrypoint_file and not custom_image:
        raise ValueError("Must specify an entrypoint file with master image or a custom image")
    if custom_image:
        image = docker_client.images.get(custom_image)
    elif master_image:
        dockerfile = make_docker_file(master_image, entrypoint_file, command=command, command_args=command_args)
        image, logs = docker_client.images.build(fileobj=dockerfile)
        logger.debug(logs)
    else:
        raise ValueError("Must specify an entrypoint file with master image or a custom image")

    if image.tag(repository=f"pht-local/{train_id}", tag="latest"):
        logger.debug(f"Tagged image {image.id} as pht-local/{train_id}:latest")
    else:
        raise ValueError("Failed to tag image")
    return image


def _add_train_files(files: BytesIO, image: Image) -> str:
    # add archive to container
    tag = image.tags[0]
    add_archive(tag, files, path="/opt/train")

    return tag
