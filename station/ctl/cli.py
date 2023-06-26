import os

import click

from station.common.config.generators import generate_self_signed_cert
from station.common.constants import Icons
from station.ctl.config import find_config, load_config
from station.ctl.config.command import settings
from station.ctl.fhir.command import fhir
from station.ctl.install.command import install


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to config file. If none is given assumes config file is located in current working directory.",
)
@click.pass_context
def cli(ctx, config):
    if config:
        ctx.obj["station_config"] = load_config(config)
        ctx.obj["config_path"] = config
    else:
        click.echo(
            f"No config file given. Looking for config file in current directory({str(os.getcwd())})... ",
            nl=False,
        )
        try:
            config_dict, path = find_config(os.getcwd())
            if not ctx.obj:
                ctx.obj = {}
            ctx.obj["station_config"] = config_dict
            ctx.obj["config_path"] = path
            click.echo(Icons.CHECKMARK.value)
        except FileNotFoundError:
            click.echo(Icons.CROSS.value)
            click.echo("No config file found.")


@cli.command(help="Uninstall the station software. Coming soon..")
@click.pass_context
def uninstall(ctx):
    # todo
    print(ctx.obj)
    click.echo("Coming soon...")


@cli.command(help="Update the station software. Coming soon..")
@click.pass_context
def update(ctx):
    # todo
    click.echo("Coming soon...")


@cli.command(
    help="Generate self signed certificates for the given domain to be used for development/testing purposes."
)
@click.argument("domain")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True),
    help="Path to the directory where the certificates should be stored. If none assumes CWD.",
)
@click.pass_context
def certs(ctx, domain, path):
    generate_self_signed_cert(domain, path)


cli.add_command(install)
cli.add_command(settings)
cli.add_command(fhir)

if __name__ == "__main__":
    cli()
