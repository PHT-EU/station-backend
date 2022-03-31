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

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

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
    validator: Optional[Callable[[Any], Tuple[bool, Union[None, str]]]] = None


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
    top_level_results = _validate_top_level_config(config)
    validation_results.extend(top_level_results)

    # validate configuration for central services
    central_results = _validate_central_config(config.get("central"))
    validation_results.extend(central_results)

    # validate http/https config
    web_results = _validate_web_config(config, strict=strict)
    validation_results.extend(web_results)

    # validate db config
    db_results = _validate_db_config(config.get("db"))
    validation_results.extend(db_results)

    # validate airflow config
    airflow_results = _validate_airflow_config(config.get("airflow"))
    validation_results.extend(airflow_results)

    # validate minio config
    minio_results = _validate_minio_config(config.get("minio"))
    validation_results.extend(minio_results)

    # validate api config
    api_results = _validate_api_config(config.get("api"))
    validation_results.extend(api_results)

    table = generate_results_table(validation_results)
    return validation_results, table


def fix_config(config: dict, results: List[ConfigItemValidationResult]) -> dict:
    """
    Allows for interactive fixes of issues in the station configuration
    Args:
        config: initial dictionary containing the config in the config yaml file
        results: validation results of the given dictionary

    Returns:

    """
    strict = config["environment"] != "development"
    fixed_config = config.copy()
    for result in results:
        if result.status != ConfigItemValidationStatus.VALID:
            pass
    return config