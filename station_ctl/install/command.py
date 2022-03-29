import os
from typing import Any, Callable, Tuple

import click
import docker
from rich.console import Console
from rich.table import Column, Table

from station.clients.central.central_client import CentralApiClient
from station_ctl.config import StationConfig, ApplicationEnvironment
from station_ctl.constants import Icons, PHTImages, ServiceImages
from station_ctl.install.fs import check_create_pht_dirs


@click.command(help="Install the station software based on the configuration file.")
@click.option('--install-dir',
              type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Install location for station software. Defaults to current working directory.')
@click.pass_context
def install(ctx, install_dir):
    if not install_dir:
        install_dir = os.getcwd()
    ctx.obj['install_dir'] = install_dir
    click.echo('Installing station software to {}'.format(install_dir))
    check_create_pht_dirs(install_dir)
    credentials = _request_registry_credentials(ctx)
    # _download_docker_images(ctx)


def _request_registry_credentials(ctx):
    click.echo('Requesting registry credentials from central api... ', nl=False)
    url = ctx.obj['central']['api_url']
    client = ctx.obj['central']['client_id']
    secret = ctx.obj['central']['client_secret']
    client = CentralApiClient(url, client, secret)

    credentials = client.get_registry_credentials(ctx.obj["station_id"])
    click.echo(Icons.CHECKMARK.value)
    return credentials


def _download_docker_images(ctx):
    try:
        client = docker.from_env()
    except Exception as e:
        click.echo(f"{Icons.CROSS.value} Failed to connect to docker: \n {e}")
        raise e

    click.echo('Downloading PHT Station images:')
    version = ctx.obj['version']
    # download pht images
    for image in PHTImages:
        _download_image(client, image.value, version)
    click.echo('Downloading service images:')
    for image in ServiceImages:
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
        click.echo(Icons.CHECKMARK.value)

    except Exception as e:
        click.echo(f"{Icons.CROSS.value} Failed to download image: \n {e}")
