import click

import docker
import docker.errors
from docker import DockerClient
from station.ctl import constants


def setup_docker():
    client = _get_docker_client()
    click.echo('Creating docker volumes... ', nl=False)
    for vol in constants.DockerVolumes:

        try:
            volume = client.volumes.get(vol.value)
            if click.prompt(f"\nVolume {vol.value} already exists. Do you want to reset it? [y/N]", default='N') == 'y':
                volume.remove()
                client.volumes.create(name=vol.value)
                click.echo(f"Volume was reset {vol.value}")

        except docker.errors.NotFound:
            try:
                client.volumes.create(name=vol.value)
                click.echo(constants.Icons.CHECKMARK.value)

            except Exception as e:
                click.echo(f"{constants.Icons.CROSS.value} Failed to create volume: \n {e}")
                raise e

        except Exception as e:
            click.echo(f"{constants.Icons.CROSS.value} Failed to create volume: \n {e}")
            raise e

    click.echo('Creating docker networks... ', nl=False)
    for net in constants.DockerNetworks:
        try:
            network = client.networks.get(net.value)
        except docker.errors.NotFound:
            try:
                client.networks.create(name=net.value)


            except Exception as e:
                click.echo(f"{constants.Icons.CROSS.value} Failed to create network: \n {e}")
                raise e
        except Exception as e:
            click.echo(f"{constants.Icons.CROSS.value} Failed to create network: \n {e}")
            raise e
    click.echo(constants.Icons.CHECKMARK.value)


def download_docker_images(ctx):
    client = _get_docker_client()

    click.echo('Downloading PHT Station images:')
    version = ctx.obj['version']
    # download pht images
    for image in constants.PHTImages:
        _download_image(client, image.value, version)
    click.echo('Downloading service images:')
    for image in constants.ServiceImages:
        _download_image(client, image.value)


def _download_image(client, image: str, tag=None):
    if not tag:
        image_tag = image.split(':')
        if len(image_tag) == 2:
            image = image_tag[0]
            tag = image_tag[1]

    click.echo(f"\tDownloading {image}:{tag}... ", nl=False)
    try:
        client.images.pull(image, tag=tag)
        click.echo(constants.Icons.CHECKMARK.value)

    except Exception as e:
        click.echo(f"{constants.Icons.CROSS.value} Failed to download image: \n {e}")


def _get_docker_client() -> DockerClient:
    try:
        client = docker.from_env()
    except Exception as e:
        click.echo(f"{constants.Icons.CROSS.value} Failed to connect to docker: \n {e}")
        raise e

    return client
