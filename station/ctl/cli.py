import os

import click

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
        ctx.obj = load_config(config)
    else:
        click.echo(
            f"No config file given. Looking for config file in current directory({str(os.getcwd())})... ",
            nl=False,
        )
        try:
            config_dict, path = find_config(os.getcwd())
            ctx.obj = config_dict
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


cli.add_command(install)
cli.add_command(settings)
cli.add_command(fhir)

if __name__ == "__main__":
    cli()
