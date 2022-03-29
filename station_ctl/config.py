from typing import Any, Callable, Tuple, Union

import yaml
from enum import Enum
import os
from pydantic import BaseSettings
import click
from rich.console import Console
from rich.table import Table

from station_ctl.constants import Icons


class ApplicationEnvironment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class StationConfig(BaseSettings):
    station_id: str
    environment: ApplicationEnvironment
    version: str
    host: str


class ConfigFiles(Enum):
    """
    Enum for config file names
    """
    STATION_CONFIG = 'station_config.yml'
    STATION_CONFIG_SHORT = 'config.yml'
    STATION = 'station.yml'


def load_config(file_name) -> dict:
    """
    Loads a config file and returns a dict with the content
    """
    with open(file_name, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

        except FileNotFoundError:
            FileNotFoundError(f'Config file {file_name} not found')


def find_config(directory) -> dict:
    """
    Finds a config file in a directory and returns a dict with the content
    """
    for file_name in ConfigFiles:
        try:
            return load_config(os.path.join(directory, file_name.value))
        except FileNotFoundError:
            pass
    raise FileNotFoundError(f'No config file found in {directory}')


def validate_config(config: dict) -> Table:
    """
    Validates a config file and returns a dict with the content
    """
    strict = config["environment"] != "development"

    table = Table(title="Config validation issues")
    table.add_column("Status", justify="center")
    table.add_column("Field", justify="center")
    table.add_column("Message", justify="center")
    table.add_column("Fix", justify="center")

    # validate top level config items
    result, field, generator, message = _validate_config_value(config, "station_id", None, None, None)
    if result == "valid":
        table.add_row(result, field, message, "Generate a new station_id")
    table.add_row(result, field, message, None)
    result, field, generator, message = _validate_config_value(config, "environment", None, _environment_validator,
                                                               None)
    table.add_row(result, field, message, "default to production environment")

    return table



def _validate_config_value(
        config: dict,
        field: str,
        default_value: Any = None,
        validator: Callable[[Any], Tuple[bool, str]] = None,
        generator: Callable[[], Any] = None) -> Any:

    field_value = config.get(field)
    if not field_value:
        return "missing", field, generator, None

    if default_value:
        if field_value == default_value:
            return "default", field, generator, None

    if validator:
        valid, message = validator(field_value)
        if not valid:
            return "invalid", field, generator, message

    return "valid", field, generator, None


def _environment_validator(environment: str) -> Tuple[bool, Union[str, None]]:
    try:
        env = ApplicationEnvironment(environment)
        if env == ApplicationEnvironment.DEVELOPMENT:
            click.echo(f'{Icons.WARNING} {env.value} is not a production environment')

        return True, None
    except ValueError:
        return False, f'Invalid environment "{environment}". Defaulting to production environment'
