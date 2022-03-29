import re
from typing import Any, Callable, Tuple, Union

import yaml
from enum import Enum
import os
from pydantic import BaseSettings
import click
from rich.console import Console
from rich.table import Table
import random
import string

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
    Validates a config file and returns a table containing the validation results
    """

    strict = config["environment"] != "development"
    table = Table(title="Station config validation", show_lines=True, header_style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Field", justify="center")
    table.add_column("Message", justify="center")
    table.add_column("Fix", justify="center")

    # validate top level config items station_id, environment etc.
    table = _validate_top_level_config(table, config, strict)

    # validate configuration for central services
    table = _validate_central_config(table, config.get("central"), strict)

    return table


def _validate_central_config(table: Table, config: dict, strict: bool = True):
    """
    Validates the central services config items
    """

    if not config:
        if strict:
            table.add_row("ERROR", "central", "central services config is missing",
                          "Add central services configuration to config file")
            return table
        else:
            table.add_row("WARNING", "central", "central services config is missing", )

    result, field, generator, message = _validate_config_value(
        config,
        field="api_url",
        prefix="central",
        default_value=None)

    if result != "valid":
        display_result = "ERROR" if strict else "WARN"
        table.add_row(display_result, field, message,
                      "Login to user interface to obtain your station id and set it in the config file")
    return table


def _validate_top_level_config(table: Table, config: dict, strict: bool = True):
    """
    Validates the top level config items
    """

    # validate station_id
    result, field, generator, message = _validate_config_value(config, "station_id", None, None, None)
    if result != "valid":
        display_result = "ERROR" if strict else "WARNING"
        table.add_row(display_result, field, message,
                      "Login to user interface to obtain your station id and set it in the config file")

    # validate runtime environment
    result, field, generator, message = _validate_config_value(config, "environment", None, _environment_validator,
                                                               None)
    if result != "valid":
        display_result = "WARNING"
        table.add_row(display_result, field, message, "defaults to production environment")

    # todo validate pht version
    return table


def _validate_config_value(
        config: dict,
        field: str,
        prefix: str = None,
        default_value: Any = None,
        validator: Callable[[Any], Tuple[bool, str]] = None,
        generator: Callable[[], Any] = None) -> Any:
    field_value = config.get(field)
    display_field = f"{prefix}.{field}" if prefix else field
    status = "valid"
    message = None
    if not field_value:
        status = "missing"
        message = f"{display_field} is missing"

    if default_value:
        if field_value == default_value:
            status = "default"
            message = f"{display_field} is set to default value"

    if validator:
        valid, message = validator(field_value)
        status = "invalid" if not valid else "valid"

    return status, display_field, generator, message


def _environment_validator(environment: str) -> Tuple[bool, Union[str, None]]:
    try:
        env = ApplicationEnvironment(environment)
        if env == ApplicationEnvironment.DEVELOPMENT:
            click.echo(f'{Icons.WARNING} {env.value} is not a production environment')

        return True, None
    except ValueError:
        return False, f'Invalid environment "{environment}"'


def _validate_url(url: str) -> Tuple[bool, Union[str, None]]:
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'[A-Za-z0-9_-]*|'  # single word with hyphen/underscore for docker
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if re.match(regex, url):
        return True, None
    else:
        return False, f'Invalid url "{url}"'


def _password_generator() -> str:
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])
