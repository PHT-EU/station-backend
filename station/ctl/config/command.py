import os
import pprint
from typing import List

import click
from rich.console import Console
from rich.table import Table

from station.ctl.config import load_config, find_config, validate_config, fix_config
from station.ctl.config.validators import ConfigItemValidationStatus, ConfigIssueLevel, ConfigItemValidationResult
from station.ctl.constants import Icons
from station.ctl.util import get_template_env


@click.command(help="Validate and/or fix a station configuration file")
@click.option('-f', '--file', help="Path to the configuration file to validate/fix")
@click.pass_context
def config(ctx, file):
    """Validate and/or fix the configuration file"""

    if not file:
        click.echo("No configuration file specified. Looking for a config file in the current directory...", nl=False)
        station_config, file = find_config(os.getcwd())
        click.echo(f"{Icons.CHECKMARK.value}")
    else:
        station_config = load_config(file)

    click.echo(f"Validating configuration file...")
    results, table = validate_config(station_config)
    issues = [result for result in results if result.status != ConfigItemValidationStatus.VALID]
    if issues:
        _display_issues(issues, table)
        click.confirm('Fix issues now?', abort=True)
        fixed_config = fix_config(ctx.obj, station_config, results)
        render_config(fixed_config, file)
        click.echo(f"Fixed configuration file written to: {file}")

    else:
        click.echo('Configuration file is valid.')


def _display_issues(issues: List[ConfigItemValidationResult], table: Table):
    console = Console()
    console.print(table)
    num_warnings = len([result for result in issues if result.level == ConfigIssueLevel.WARN])
    num_errors = len([result for result in issues if result.level == ConfigIssueLevel.ERROR])
    warning_styled = click.style(f"{num_warnings}", fg="yellow")
    errors_styled = click.style(f"{num_errors}", fg="red")
    click.echo(f"Found {warning_styled} warnings and {errors_styled} errors")


def render_config(config: dict, path: str):

    env = get_template_env()
    template = env.get_template('station_config.yml.tmpl')
    # write out the correct path to key file on host when rendering the template from docker container
    if config.get("host_path"):
        key_name = config["central"]["private_key"].split("/")[-1]
        key_path = os.path.join(config["host_path"], key_name)
        config["central"]["private_key"] = key_path

    out_config = template.render(
        station_id=config['station_id'],
        version=config['version'],
        admin_password=config['admin_password'],
        environment=config['environment'],
        central=config['central'],
        http=config['http'],
        https=config['https'],
        registry=config['registry'],
        db=config['db'],
        api=config['api'],
        airflow=config['airflow'],
        minio=config['minio'],
        auth=config['auth'],
    )

    with open(path, 'w') as f:
        f.write(out_config)
