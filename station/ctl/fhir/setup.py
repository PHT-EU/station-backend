import re
from typing import List

import click

import docker
from station.ctl.constants import DockerNetworks, Icons, ServiceImages


def setup_cli(ctx: click.Context, name: str):
    if not name:
        name = click.prompt("Please enter a name for the server")

    name = _validate_server_name(name)
    port = click.prompt(
        "If you would like to expose the server on the host machine please enter the port number",
        default="",
    )
    domain = ctx.obj["https"]["domain"]
    click.echo(
        f"Setting up server with base url: {domain}/fhir-servers/{name}... ", nl=False
    )
    try:
        setup_server(domain, name, port)
        click.echo(f"{Icons.CHECKMARK.value}")
    except Exception as e:
        click.echo(Icons.CROSS.value)
        click.echo(f"Error: {e}")


def setup_server(domain: str, name: str, port: str = None):
    client = docker.from_env()
    volume = _setup_volume(client, name)
    labels = _make_labels(domain, name)
    env = _make_env(domain, name)
    client.containers.run(
        ServiceImages.BLAZE.value,
        volumes=volume,
        labels=labels,
        environment=env,
        detach=True,
        name=name,
        network=DockerNetworks.STATION.value,
        ports={port: "8080"} if port else None,
    )


def _setup_volume(client: docker.DockerClient, name: str) -> List[str]:
    volume_name = f"blaze-{name}"
    client.volumes.create(name=volume_name)
    volume_list = [f"{volume_name}:/app/data"]
    return volume_list


def _make_labels(domain: str, name: str) -> dict:
    return {
        "traefik.enable": "true",
        f"traefik.http.routers.{'fhir-' + name}.tls": "true",
        f'traefik.http.routers.{"fhir-" + name}.rule': f'Host("{domain}") && PathPrefix("/fhir-servers/{name}")',
        f"traefik.http.services.{'fhir-' + name}.loadbalancer.server.port": "8080",
    }


def _make_env(domain: str, name: str) -> List[str]:
    # todo add station auth server oidc connection variables
    return [
        "JAVA_TOOL_OPTIONS=-Xmx2g",
        f"BASE_URL=https://{domain}/fhir-servers/{name}",
    ]


def _validate_server_name(name: str) -> str:
    match = re.match(r"^[a-zA-Z\d_-]*$", name)
    if not match:
        name = click.prompt(
            f"Invalid server name: {name}. Enter a valid server name containing only [a-zA-Z0-9_-]."
        )
        return _validate_server_name(name)
    return name
