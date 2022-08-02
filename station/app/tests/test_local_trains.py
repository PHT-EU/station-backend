from station.app.local_trains.docker import make_docker_file


def test_make_docker_file():
    master_image = "ubuntu:latest"
    entrypoint_file = "entrypoint.sh"
    command = "bash"
    command_args = ["-c", "echo 'hello'"]

    docker_file = make_docker_file(master_image, entrypoint_file, command, command_args)

    print(docker_file.read())

    docker_file = make_docker_file(master_image, entrypoint_file, command)
    print(docker_file.read())


def test_build():
    pass
