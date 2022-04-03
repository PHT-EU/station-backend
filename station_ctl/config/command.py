import os

import click
from rich.console import Console

from station_ctl.config import load_config, find_config, validate_config, fix_config
from station_ctl.config.validators import ConfigItemValidationStatus


@click.command(help="Validate and/or fix a station configuration file")
@click.option('-f', '--file', help="Path to the configuration file to validate/fix")
@click.pass_context
def config(ctx, file):
    """Validate and/or fix the configuration file"""

    if not file:
        station_config = find_config(os.getcwd())
    else:
        station_config = load_config(file)

    results, table = validate_config(station_config)
    issues = [result for result in results if result.status != ConfigItemValidationStatus.VALID]
    if issues:
        console = Console()
        console.print(table)

        click.confirm('Press enter to fix the configuration file', abort=True)
        fix_config(station_config, results)
