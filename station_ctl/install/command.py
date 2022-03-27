import os

import click
from station.clients.central.central_client import CentralApiClient
from station_ctl.constants import Icons

@click.command(help="Install the station software based on the configuration file.")
@click.option('--install-dir',
              type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Install location for station software. Defaults to current working directory.')
@click.pass_context
def install(ctx, output_dir):
    if not output_dir:
        output_dir = os.getcwd()
    ctx.obj['output_dir'] = output_dir
    click.echo('Installing station software to {}'.format(output_dir))
    credentials = _request_registry_credentials(ctx)


def _request_registry_credentials(ctx):
    click.echo('Requesting credentials from central api... ', nl=False)
    url = ctx.obj['central']['api_url']
    client = ctx.obj['central']['client_id']
    secret = ctx.obj['central']['client_secret']
    client = CentralApiClient(url, client, secret)

    credentials = client.get_registry_credentials(ctx.obj["station_id"])
    click.echo(Icons.CHECKMARK.value)
    return credentials
