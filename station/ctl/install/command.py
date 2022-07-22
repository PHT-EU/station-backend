import os
import pprint
import sys
from typing import Tuple

import click
import docker
from rich.console import Console

from station.clients.central.central_client import CentralApiClient
from station.ctl.config import validate_config, fix_config
from station.ctl.config.command import render_config
from station.ctl.config.validators import ConfigItemValidationStatus
from station.ctl.constants import Icons, PHTDirectories, PHTImages
from station.ctl.install.docker import setup_docker, download_docker_images
from station.ctl.install import templates
from station.ctl.install.fs import check_create_pht_dirs


@click.command(help="Install the station software based on the configuration file.")
@click.option('--install-dir',
              type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Install location for station software. Defaults to current working directory.')
@click.option('--host-path', type=str, help='Host path for containerized execution of the installer', required=False)
@click.pass_context
def install(ctx, install_dir, host_path):
    # validate configuration before installing
    click.echo('Validating configuration... ', nl=False)
    ctx.obj["host_path"] = host_path
    validation_results, table = validate_config(ctx.obj, host_path=host_path)
    issues = [result for result in validation_results if result.status != ConfigItemValidationStatus.VALID]

    if issues:
        click.echo(Icons.CROSS.value)
        console = Console()
        console.print(table)
        click.confirm(f"Station configuration is invalid. Please fix the errors displayed above. \n"
                      f"Would you like to fix the configuration now?", abort=True)
        station_config = fix_config(ctx.obj, ctx.obj, validation_results)
        ctx.obj = station_config

    else:
        click.echo(Icons.CHECKMARK.value)

    if not install_dir:
        install_dir = os.getcwd()

    ctx.obj['install_dir'] = install_dir
    host_path = ctx.obj.get("host_path")
    click.echo('Installing station software to {}'.format(host_path if host_path else install_dir))
    # ensure file system is set up
    check_create_pht_dirs(install_dir)

    # get credentials for registry
    reg_credentials = _request_registry_credentials(ctx)

    ctx.obj["registry"]["project"] = reg_credentials["external_name"]

    # setup docker
    setup_docker()
    download_docker_images(ctx)
    _setup_auth_server(ctx)

    # render templates according to configuration and store output paths in configuration object
    ctx.obj["init_sql_path"] = write_init_sql(ctx)
    traefik_config_path, router_config_path = write_traefik_configs(ctx)
    ctx.obj["traefik_config_path"] = traefik_config_path
    ctx.obj["router_config_path"] = router_config_path
    ctx.obj["airflow_config_path"] = write_airflow_config(ctx)

    # render the updated configuration file
    render_config(ctx.obj, ctx.obj['config_path'])

    # render the final compose template
    write_compose_file(ctx)


def _request_registry_credentials(ctx):
    click.echo('Requesting registry credentials from central api... ', nl=False)
    url = ctx.obj['central']['api_url']
    client = ctx.obj['central']['robot_id']
    secret = ctx.obj['central']['robot_secret']
    client = CentralApiClient(url, client, secret)

    credentials = client.get_registry_credentials(ctx.obj["station_id"])
    click.echo(Icons.CHECKMARK.value)


    return credentials


def _setup_auth_server(ctx):
    click.echo('Setting up auth server... ', nl=False)
    client = docker.from_env()

    auth_image = f"{PHTImages.AUTH.value}:{ctx.obj['version']}"
    command = "setup"

    if ctx.obj.get("host_path"):
        writable_dir = os.path.join(ctx.obj['host_path'], PHTDirectories.SERVICE_DATA_DIR.value, "auth")
    else:
        writable_dir = os.path.join(ctx.obj['install_dir'], PHTDirectories.SERVICE_DATA_DIR.value, "auth")

    auth_volumes = {
        str(writable_dir): {
            "bind": "/usr/src/app/writable",
            "mode": "rw"
        }
    }

    environment = {
        "ADMIN_USER": "admin",
        "ADMIN_PASSWORD": ctx.obj['admin_password'],
    }

    container = client.containers.run(auth_image,
                                      command,
                                      remove=True,
                                      detach=True,
                                      environment=environment,
                                      volumes=auth_volumes)

    output = container.attach(stdout=True, stream=True, logs=True, stderr=True)

    robot_id = None
    robot_secret = None

    logs = []
    for line in output:
        decoded = line.decode("utf-8")
        logs.append(decoded)
        if "Robot ID" in decoded and "Robot Secret" in decoded:
            robot_id_index = decoded.find("Robot ID")
            robot_secret_index = decoded.find("Robot Secret")
            robot_id = decoded[robot_id_index + len("Robot ID:"):robot_secret_index - 2].strip()
            robot_secret = decoded[robot_secret_index + len("Robot Secret:"):].strip()

    if not robot_id or not robot_secret:
        click.echo(Icons.CROSS.value)
        click.echo("Failed to setup auth server", err=True)
        pprint.pp(logs)
        raise Exception("Could not get robot credentials from auth server")

    else:

        auth = {
            "robot_id": robot_id,
            "robot_secret": robot_secret,
        }
        ctx.obj["auth"] = auth
        click.echo(Icons.CHECKMARK.value)


def write_init_sql(ctx) -> str:
    click.echo('Setting up database... ', nl=False)
    try:

        db_config = ctx.obj['db']
        init_sql_path = os.path.join(
            ctx.obj['install_dir'],
            PHTDirectories.SETUP_SCRIPT_DIR.value,
            'init.sql'
        )
        with open(init_sql_path, 'w') as f:
            f.write(templates.render_init_sql(db_user=db_config["admin_user"]))

        click.echo(Icons.CHECKMARK.value)
        return str(init_sql_path)

    except Exception as e:
        click.echo(Icons.CROSS.value)
        click.echo(f'Error creating init sql: {e}', err=True)
        sys.exit(1)


def write_traefik_configs(ctx) -> Tuple[str, str]:
    click.echo('Setting up traefik... ', nl=False)
    try:
        traefik_config, router_config = templates.render_traefik_configs(
            http_port=ctx.obj['http']['port'],
            https_port=ctx.obj['https']['port'],
            https_enabled=True,
            domain=ctx.obj['https']['domain'],
            certs=ctx.obj['https']['certs']
        )

        traefik_path = os.path.join(
            ctx.obj['install_dir'],
            PHTDirectories.CONFIG_DIR.value,
            'traefik'
        )

        traefik_config_path = os.path.join(traefik_path, "traefik.yml")
        router_config_path = os.path.join(traefik_path, "config.yml")

        os.makedirs(traefik_path, exist_ok=True)

        with open(traefik_config_path, 'w') as f:
            f.write(traefik_config)

        with open(router_config_path, 'w') as f:
            f.write(router_config)

        click.echo(Icons.CHECKMARK.value)
        host_path = ctx.obj.get("host_path")
        if host_path:
            traefik_config_path = os.path.join(host_path, PHTDirectories.CONFIG_DIR.value, "traefik", "traefik.yml")
            router_config_path = os.path.join(host_path, PHTDirectories.CONFIG_DIR.value, "traefik", "config.yml")
        return str(traefik_config_path), str(router_config_path)

    except Exception as e:
        click.echo(Icons.CROSS.value)
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


def write_airflow_config(ctx) -> str:
    click.echo('Setting up airflow... ', nl=False)
    try:

        db_connection_string = f"postgresql+psycopg2://{ctx.obj['db']['admin_user']}:{ctx.obj['db']['admin_password']}" \
                               f"@postgres/airflow"
        airflow_config = templates.render_airflow_config(
            sql_alchemy_conn=db_connection_string,
            domain=ctx.obj['https']['domain']
        )

        host_path = ctx.obj.get('host_path')
        if host_path:
            path = host_path
        else:
            path = ctx.obj['install_dir']

        airflow_config_path = os.path.join(
            path,
            PHTDirectories.CONFIG_DIR.value,
            'airflow.cfg'
        )

        write_path = os.path.join(
            ctx.obj['install_dir'],
            PHTDirectories.CONFIG_DIR.value,
            'airflow.cfg'
        )

        with open(write_path, 'w') as f:
            f.write(airflow_config)

        click.echo(Icons.CHECKMARK.value)
        return str(airflow_config_path)

    except Exception as e:
        click.echo(Icons.CROSS.value)
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


def write_compose_file(ctx):
    host_path = ctx.obj.get("host_path")
    if host_path:
        host_path = os.path.join(ctx.obj["host_path"], "docker-compose.yml")

    compose_path = os.path.join(ctx.obj["install_dir"], "docker-compose.yml")
    click.echo(f'Writing compose file to {host_path if host_path else compose_path}... ', nl=False)

    content = templates.render_compose(config=ctx.obj)
    with open(compose_path, 'w') as f:
        f.write(content)

    click.echo(Icons.CHECKMARK.value)
