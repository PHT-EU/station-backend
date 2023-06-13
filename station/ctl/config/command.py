import os

import click
from rich.console import Console

from station.common.constants import Icons
from station.ctl.config import find_config, fix_config, load_config
from station.ctl.config.validate import validate_config
from station.ctl.util import get_template_env


@click.command(help="Validate and/or fix a station configuration file")
@click.option("-f", "--file", help="Path to the configuration file to validate/fix")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Do not write the fixed config to disk. But print it instead.",
)
@click.pass_context
def settings(ctx, file, dry_run):
    """Validate and/or fix the configuration file"""

    if not file:
        click.echo(
            "No configuration file specified. Looking for a config file in the current directory... ",
            nl=False,
        )
        station_config, file = find_config(os.getcwd())
        click.echo(f"{Icons.CHECKMARK.value}")
    else:
        station_config = load_config(file)

    click.echo("Validating configuration file...")

    results = validate_config(station_config)

    if results is not None:
        table, results = results
        console = Console()
        console.print(table)
        click.confirm("Fix issues now?", abort=True)
        fixed_config = fix_config(ctx.obj, station_config, results)
        render_config(fixed_config, file)
        if not dry_run:
            click.echo(f"Fixed configuration file written to: {file}")

    else:
        click.echo("Configuration file is valid.")


def render_config(config: dict, path: str, dry_run: bool = False) -> str | None:
    env = get_template_env()
    template = env.get_template("station_config.yml.tmpl")
    # write out the correct path to key file on host when rendering the template from docker container

    # todo check and improve this
    if config.get("host_path"):
        key_name = config["station_config"]["central"]["private_key"].split("/")[-1]
        key_path = os.path.join(config["host_path"], key_name)
        config["station_config"]["central"]["private_key"] = key_path

    # todo fix this hack
    # extract https certs from config
    certs = config["station_config"]["https"].pop("certificate")

    out_config = template.render(certificate=certs, **config["station_config"])

    # print the rendered config to stdout and return it if dry_run is True
    if dry_run:
        click.echo(out_config)
        return out_config
    else:
        with open(path, "w") as f:
            f.write(out_config)
