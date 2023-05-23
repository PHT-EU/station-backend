import click

import docker
from station.common.constants import Icons


def start_server(name: str):
    name = _get_name_if_not_exists(name)
    client = docker.from_env()
    click.echo(f"Starting server {name}...", nl=False)
    try:
        container = client.containers.get(name)
        container.start()
        click.echo(Icons.CHECKMARK.value)
    except Exception as e:
        click.echo(Icons.CROSS.value)
        click.echo(f"Error starting server:\n {e}")


def stop_server(name: str):
    name = _get_name_if_not_exists(name)
    client = docker.from_env()
    click.echo(f"Stopping server {name}...", nl=False)
    try:
        container = client.containers.get(name)
        container.stop()
        click.echo(Icons.CHECKMARK.value)
    except Exception as e:
        click.echo(Icons.CROSS.value)
        click.echo(f"Error stopping server:\n {e}")


def remove_server(name: str):
    name = _get_name_if_not_exists(name)
    client = docker.from_env()
    click.echo(f"Removing server {name}...", nl=False)
    try:
        container = client.containers.get(name)
        container.remove()
        click.echo(Icons.CHECKMARK.value)
    except Exception as e:
        click.echo(Icons.CROSS.value)
        click.echo(f"Error removing server:\n {e}")


def list_servers():
    client = docker.from_env()
    client.containers.list()
    # todo
    click.echo("coming soon...")


def _get_name_if_not_exists(name: str) -> str:
    if name:
        return name
    else:
        name = click.prompt("Please enter the name of the server")
    return name
