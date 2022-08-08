import time

import pytest

from station.app.local_trains.docker import make_docker_file
from station.app.local_trains.build import build_train
from io import BytesIO
import tarfile


@pytest.fixture
def simple_file_archive() -> BytesIO:
    archive = BytesIO()
    with tarfile.TarFile(fileobj=archive, mode="w") as tar:
        content = "import os\n\nif __name__ == '__main__':\n    print('hello')\n"
        file = BytesIO(content.encode("utf-8"))
        info = tarfile.TarInfo(name="entrypoint.py")
        info.size = len(file.getbuffer())
        info.mtime = time.time()
        tar.addfile(info, file)

    archive.seek(0)
    return archive


def test_make_docker_file():
    master_image = "ubuntu:latest"
    entrypoint_file = "entrypoint.sh"
    command = "bash"
    command_args = ["-c", "echo 'hello'"]

    docker_file = make_docker_file(master_image, entrypoint_file, command, command_args)

    print(docker_file.read())

    docker_file = make_docker_file(master_image, entrypoint_file, command)
    print(docker_file.read())


def test_build_basic(simple_file_archive):

    train = build_train(
        train_id="test",
        master_image_id="python:3.8",
        files=simple_file_archive,
        command="python",
        entrypoint_file="entrypoint.py",
    )

    print(train)


