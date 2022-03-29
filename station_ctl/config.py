import re
from typing import Any, Callable, Tuple, Union, List, Optional

import yaml
from enum import Enum
import os
from pydantic import BaseSettings, BaseModel
import click
from rich.table import Table
import random
import string

from station_ctl.constants import Icons, DefaultValues


class ApplicationEnvironment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class StationConfig(BaseSettings):
    station_id: str
    environment: ApplicationEnvironment
    version: str
    host: str


class ConfigItemValidationStatus(str, Enum):
    VALID = 0
    INVALID = 1
    MISSING = 2
    FORBIDDEN_DEFAULT = 3


class ConfigIssueLevel(str, Enum):
    WARN = "WARNING"
    ERROR = "ERROR"


class ConfigItemValidationResult(BaseModel):
    status: ConfigItemValidationStatus
    level: Optional[ConfigIssueLevel] = ConfigIssueLevel.WARN
    field: str
    display_field: str
    value: Optional[Any] = None
    message: Optional[str] = ""
    generator: Optional[Callable[[], Any]] = None
    fix_hint: Optional[str] = ""


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


def validate_config(config: dict) -> Tuple[List[ConfigItemValidationResult], Table]:
    """
    Validates a config file and returns a table containing the validation results
    """

    strict = config["environment"] != "development"
    validation_results = []
    # validate top level config items station_id, environment etc.
    top_level_results = _validate_top_level_config(config, strict)
    validation_results.extend(top_level_results)

    # validate configuration for central services
    central_results = _validate_central_config(config.get("central"), strict)
    validation_results.extend(central_results)

    table = generate_results_table(validation_results)
    return validation_results, table


def generate_results_table(results: List[ConfigItemValidationResult]) -> Table:
    table = Table(title="Station config validation", show_lines=True, header_style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Field", justify="center")
    table.add_column("Message", justify="center")
    table.add_column("Fix", justify="center")

    for result in results:
        if result.status != ConfigItemValidationStatus.VALID:
            table.add_row(result.level.value, result.display_field, result.message, result.fix_hint)

    return table


def _validate_central_config(central_config: dict, strict: bool = True) -> List[ConfigItemValidationResult]:
    """
    Validates the central services config items
    """

    if not central_config:
        return [ConfigItemValidationResult(
            status=ConfigItemValidationStatus.MISSING,
            level=ConfigIssueLevel.ERROR,
            field="central",
            display_field="central",
            message="Central services configuration missing",
            fix_hint="Add address and credentials for the central API (available in the UI) to the station config file."
        )]

    validation_results = []

    api_url_result = _validate_config_value(
        central_config,
        field="api_url",
        prefix="central",
        validator=_validate_url,
        default_value=None)
    if api_url_result.status != ConfigItemValidationStatus.MISSING:
        api_url_result.fix_hint = "Add address for the central API ({central_domain}/api) to the station config file."
    elif api_url_result.status != ConfigItemValidationStatus.INVALID:
        api_url_result.fix_hint = f'Malformed central API URL: {api_url_result.value}'
    api_url_result.level = ConfigIssueLevel.ERROR
    validation_results.append(api_url_result)

    return validation_results


def _validate_top_level_config(config: dict, strict: bool = True) -> List[ConfigItemValidationResult]:
    """
    Validates the top level config items
    """

    validation_issues = []

    # validate station_id
    id_result = _validate_config_value(config, "station_id", None, None, None)

    if id_result.status != ConfigItemValidationStatus.VALID:
        id_result.fix_hint = "Login to user interface to obtain your station id and set it in the config file"
        id_result.level = ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN
        validation_issues.append(id_result)

    # validate runtime environment
    environment_result = _validate_config_value(config, "environment", None, _environment_validator,
                                                None)
    if environment_result.status != ConfigItemValidationStatus.VALID:
        environment_result.fix_hint = "Set environment to development or production"
    # todo validate pht version
    return validation_issues


def _validate_config_value(
        config: dict,
        field: str,
        prefix: str = None,
        default_value: Any = None,
        validator: Callable[[Any], Tuple[bool, str]] = None,
        generator: Callable[[], Any] = None) -> ConfigItemValidationResult:
    field_value = config.get(field)
    display_field = f"{prefix}.{field}" if prefix else field
    status = ConfigItemValidationStatus.VALID
    message = None
    if not field_value:
        status = ConfigItemValidationStatus.MISSING
        message = f"{display_field} is not allowed to be empty"

    if default_value and field_value:
        if field_value == default_value:
            status = ConfigItemValidationStatus.FORBIDDEN_DEFAULT
            message = f'{display_field} can not be set to default value "{default_value}"'

    if validator:
        valid, message = validator(field_value)
        status = ConfigItemValidationStatus.VALID if valid else ConfigItemValidationStatus.INVALID

    result = ConfigItemValidationResult(
        status=status,
        field=field,
        display_field=display_field,
        message=message,
        generator=generator,
    )

    return result


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
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # path

    if re.match(regex, url):
        return True, None
    else:
        return False, f'Malformed url "{url}"'


def _password_generator() -> str:
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])
