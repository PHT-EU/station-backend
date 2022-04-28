import os
import sys

import click
from rich.console import Console

from station.clients.central.central_client import CentralApiClient
from station.ctl.config import validate_config, fix_config
from station.ctl.config.command import render_config
from station.ctl.config.validators import ConfigItemValidationStatus
from station.ctl.constants import Icons, PHTDirectories
from station.ctl.install.docker import setup_docker
from station.ctl.install import templates
from station.ctl.install.fs import check_create_pht_dirs


@click.command(help="Install the station software based on the configuration file.")
@click.option('--install-dir',
              type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Install location for station software. Defaults to current working directory.')
@click.pass_context
def install(ctx, install_dir):
    # validate configuration before installing
    click.echo('Validating configuration... ', nl=False)
    validation_results, table = validate_config(ctx.obj)

    issues = [result for result in validation_results if result.status != ConfigItemValidationStatus.VALID]

    if issues:
        click.echo(Icons.CROSS.value)
        console = Console()
        console.print(table)
        click.confirm(f"Station configuration is invalid. Please fix the errors displayed above. \n"
                      f"Would you like to fix the configuration now?", abort=True)

        station_config = fix_config(ctx.obj, ctx.obj, validation_results)
        render_config(station_config, ctx.obj['config_path'])
        ctx.obj = station_config

    else:
        click.echo(Icons.CHECKMARK.value)

    if not install_dir:
        install_dir = os.getcwd()

    ctx.obj['install_dir'] = install_dir
    click.echo('Installing station software to {}'.format(install_dir))
    # ensure file system is setup
    check_create_pht_dirs(install_dir)

    # get credentials for registry
    reg_credentials = _request_registry_credentials(ctx)
    ctx.obj["registry"] = reg_credentials

    # setup docker
    setup_docker()
    # download_docker_images(ctx)

    # render templates according to configuration
    write_init_sql(ctx)


def _request_registry_credentials(ctx):
    click.echo('Requesting registry credentials from central api... ', nl=False)
    url = ctx.obj['central']['api_url']
    client = ctx.obj['central']['robot_id']
    secret = ctx.obj['central']['robot_secret']
    client = CentralApiClient(url, client, secret)

    credentials = client.get_registry_credentials(ctx.obj["station_id"])
    click.echo(Icons.CHECKMARK.value)
    return credentials


def write_init_sql(ctx):
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

    except Exception as e:
        click.echo(Icons.CROSS.value)
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
