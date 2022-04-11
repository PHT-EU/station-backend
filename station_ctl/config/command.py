import os

import click
from rich.console import Console

from station_ctl.config import load_config, find_config, validate_config, fix_config
from station_ctl.config.validators import ConfigItemValidationStatus, ConfigIssueLevel
from station_ctl.constants import Icons


@click.command(help="Validate and/or fix a station configuration file")
@click.option('-f', '--file', help="Path to the configuration file to validate/fix")
@click.pass_context
def config(ctx, file):
    """Validate and/or fix the configuration file"""

    if not file:
        click.echo("No configuration file specified. Looking for a config file in the current directory...", nl=False)
        station_config = find_config(os.getcwd())
        click.echo(f"{Icons.CHECKMARK.value}")
    else:
        station_config = load_config(file)

    click.echo(f"Validating configuration file...")

    results, table = validate_config(station_config)
    issues = [result for result in results if result.status != ConfigItemValidationStatus.VALID]
    if issues:
        console = Console()
        console.print(table)
        num_warnings = len([result for result in issues if result.level == ConfigIssueLevel.WARN])
        num_errors = len([result for result in issues if result.level == ConfigIssueLevel.ERROR])
        warning_styled = click.style(f"{num_warnings}", fg="yellow")
        errors_styled = click.style(f"{num_errors}", fg="red")
        click.echo(f"Found {warning_styled} warnings and {errors_styled} errors")
        click.confirm('Fix issues now?', abort=True)
        fixed_config = fix_config(station_config, results)
    else:
        click.echo('Configuration file is valid.')
