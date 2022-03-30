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
    central_results = _validate_central_config(config.get("central"))
    validation_results.extend(central_results)

    web_results = _validate_web_config(config, strict=strict)
    validation_results.extend(web_results)

    table = generate_results_table(validation_results)
    return validation_results, table


def generate_results_table(results: List[ConfigItemValidationResult]) -> Table:
    table = Table(title="Station config validation", show_lines=True, header_style="bold")
    table.add_column("Level", justify="center")
    table.add_column("Field", justify="center")
    table.add_column("Issue", justify="center")
    table.add_column("Fix", justify="center")

    for result in results:
        if result.status != ConfigItemValidationStatus.VALID:
            table.add_row(result.level.value, result.display_field, result.message, result.fix_hint)

    return table


def _validate_web_config(config: dict, strict: bool = True) -> List[ConfigItemValidationResult]:
    """
    Validates the web configuration
    """

    validation_results = []

    # validate http web configuration
    http_config = config.get("http")
    if http_config is None:
        # issue warning if http config is not present
        validation_results.append(
            ConfigItemValidationResult(
                status=ConfigItemValidationStatus.MISSING,
                level=ConfigIssueLevel.WARN,
                field="http",
                display_field="http",
                message="HTTP configuration is missing",
                generator=lambda: DefaultValues.HTTP_PORT.value,
                fix_hint="Add http.port to config file if a specific port is desired. Defaults to {}".format(
                    DefaultValues.HTTP_PORT.value)
            )
        )
    else:
        # validate http port
        http_port = _validate_config_value(http_config, "port", validator=_validate_int, prefix="http")
        http_port.generator = lambda: DefaultValues.HTTP_PORT.value
        if http_port.status == ConfigItemValidationStatus.MISSING:
            http_port.level = ConfigIssueLevel.WARN
            http_port.fix_hint = "Add http.port to config file if a specific port is desired. Defaults to {}".format(
                DefaultValues.HTTP_PORT.value)
        elif http_port.status == ConfigItemValidationStatus.INVALID:
            http_port.level = ConfigIssueLevel.ERROR
            http_port.fix_hint = "Change http.port to a valid port number"

        validation_results.append(http_port)

    # validate https web configuration
    https_config = config.get("https")

    if not https_config:
        # issue warning if https config is not present
        validation_results.append(
            ConfigItemValidationResult(
                status=ConfigItemValidationStatus.MISSING,
                level=ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN,
                field="https",
                display_field="https",
                message="HTTPS configuration is missing",
                generator=lambda: DefaultValues.HTTPS_PORT.value,
                fix_hint="Add https.port to config file if a specific port is desired. Defaults to {}".format(
                    DefaultValues.HTTPS_PORT.value)
            )
        )

    else:
        # validate https port
        https_port = _validate_config_value(https_config, "port", validator=_validate_int, prefix="https")
        https_port.generator = lambda: DefaultValues.HTTPS_PORT.value
        if https_port.status == ConfigItemValidationStatus.MISSING:
            https_port.level = ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN
            https_port.fix_hint = "Add https.port to config file if a specific port is desired. Defaults to {}".format(
                DefaultValues.HTTPS_PORT.value)
        elif https_port.status == ConfigItemValidationStatus.INVALID:
            https_port.level = ConfigIssueLevel.ERROR
            https_port.fix_hint = "Change https.port to a valid port number"

        validation_results.append(https_port)

        # validate domain
        https_domain = _validate_config_value(
            https_config,
            "domain",
            validator=_validate_url,
            prefix="https",
        )
        if https_domain.status == ConfigItemValidationStatus.MISSING:
            https_domain.level = ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN
            https_domain.fix_hint = "Add a valid https domain to config file when using https"

        elif https_domain.status == ConfigItemValidationStatus.INVALID:
            https_domain.level = ConfigIssueLevel.ERROR
            https_domain.fix_hint = f"Change https.domain ({https_domain.value}) to a valid domain"

        validation_results.append(https_domain)

        # validate certificates and keys
        certs = https_config.get("certs")
        if not certs:
            validation_results.append(
                ConfigItemValidationResult(
                    status=ConfigItemValidationStatus.MISSING,
                    level=ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN,
                    field="certs",
                    display_field="https.certs",
                    message="No HTTPS certificates configured",
                    fix_hint="Add https.certs to config file if a certificate is desired. In development mode, you can"
                             "later generate a self-signed certificate"
                )
            )
        else:
            if not isinstance(certs, list):
                validation_results.append(
                    ConfigItemValidationResult(
                        status=ConfigItemValidationStatus.INVALID,
                        level=ConfigIssueLevel.ERROR,
                        field="certs",
                        display_field="https.certs",
                        message="https.certs must be a list of cert/key objects",
                        fix_hint="Change https.certs to a list of cert/key objects"
                    )
                )
            else:
                for i, cert in enumerate(certs):
                    if not isinstance(cert, dict):
                        validation_results.append(
                            ConfigItemValidationResult(
                                status=ConfigItemValidationStatus.INVALID,
                                level=ConfigIssueLevel.ERROR,
                                field="certs",
                                display_field=f"https.certs[{i}]",
                                message="Cert entry is not a valid cer/key object",
                                fix_hint=f"Change https.certs[{i}] to a valid cert/key object"
                            )
                        )
                    else:
                        cert_path = cert.get("cert")
                        key_path = cert.get("key")
                        if not cert_path and key_path:
                            message = "Certificate path is missing from https.certs[{}]".format(i)
                            status = ConfigItemValidationStatus.MISSING
                        elif not key_path and cert_path:
                            status = ConfigItemValidationStatus.MISSING
                            message = "Key path is missing from https.certs[{}]".format(i)
                        elif not cert_path and not key_path:
                            status = ConfigItemValidationStatus.MISSING
                            message = "Certificate and key paths are missing from https.certs[{}]".format(i)

                        else:
                            if not os.path.isfile(cert_path) and not os.path.isfile(key_path):
                                status = ConfigItemValidationStatus.INVALID
                                message = "Cert file {} and key file {} do not exist".format(
                                    cert_path,
                                    key_path
                                )
                            if not os.path.isfile(cert_path):
                                status = ConfigItemValidationStatus.INVALID
                                message = f"Certificate path ({cert_path}) does not exist"
                            elif not os.path.isfile(key_path):
                                status = ConfigItemValidationStatus.INVALID
                                message = f"Key path ({key_path}) does not exist"

    return validation_results


def _validate_central_config(central_config: dict) -> List[ConfigItemValidationResult]:
    """
    Validates the central services' config items
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

    # validate central api address
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

    # validate central credentials
    for robot_field in ["robot_id", "robot_secret"]:

        default = DefaultValues.ROBOT_ID.value if robot_field == "robot_id" else DefaultValues.ROBOT_SECRET.value
        robot_field_result = _validate_config_value(central_config, field=robot_field,
                                                    prefix="central", default_value=default)
        if robot_field_result.status in (
                ConfigItemValidationStatus.MISSING, ConfigItemValidationStatus.FORBIDDEN_DEFAULT):
            robot_field_result.fix_hint = "Set robot credentials from the central UI to the station config file."
            robot_field_result.level = ConfigIssueLevel.ERROR
        elif robot_field_result.status != ConfigItemValidationStatus.INVALID:
            robot_field_result.fix_hint = f'Malformed {robot_field}: {robot_field_result.value}'
            robot_field_result.level = ConfigIssueLevel.ERROR
        validation_results.append(robot_field_result)

    # validate central private key
    # todo add generator function for private key and submit to central api
    private_key_result = _validate_config_value(central_config,
                                                field="private_key",
                                                default_value=DefaultValues.PRIVATE_KEY.value,
                                                prefix="central",
                                                validator=_validate_private_key)

    if private_key_result.status == ConfigItemValidationStatus.MISSING:
        private_key_result.fix_hint = "Set path to private key registered in the central UI to the station config file."
        private_key_result.level = ConfigIssueLevel.ERROR
    elif private_key_result.status == ConfigItemValidationStatus.INVALID:
        private_key_result.fix_hint = f'Ensure that the private key in "{private_key_result.value}" is readable and ' \
                                      f'a valid PEM file.'
        private_key_result.level = ConfigIssueLevel.ERROR
    validation_results.append(private_key_result)

    return validation_results


def _validate_top_level_config(config: dict, strict: bool = True) -> List[ConfigItemValidationResult]:
    """
    Validates the top level config items
    """

    validation_issues = []

    # validate station_id
    id_result = _validate_config_value(config, "station_id")

    if id_result.status != ConfigItemValidationStatus.VALID:
        id_result.fix_hint = "Login to user interface to obtain your station id and set it in the config file"
        id_result.level = ConfigIssueLevel.ERROR
        validation_issues.append(id_result)

    # validate runtime environment
    environment_result = _validate_config_value(config, "environment", validator=_environment_validator)
    if environment_result.status != ConfigItemValidationStatus.VALID:
        environment_result.fix_hint = "Set environment to production. All values other than development will " \
                                      "default to production"
        environment_result.level = ConfigIssueLevel.WARN
        validation_issues.append(environment_result)
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

    elif default_value and field_value:
        if field_value == default_value:
            status = ConfigItemValidationStatus.FORBIDDEN_DEFAULT
            message = f'{display_field} can not be set to default value "{default_value}"'

    elif validator and field_value:
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


def _validate_int(value: Any) -> Tuple[bool, Union[str, None]]:
    try:
        int(value)
        return True, None
    except Exception as e:
        return False, f'Invalid integer "{value}" \n {e}'


def _validate_private_key(key_path: str) -> Tuple[bool, Union[str, None]]:
    if not os.path.isfile(key_path):
        return False, f'Private key file "{key_path}" does not exist'
    if not os.access(key_path, os.R_OK):
        return False, f'Private key file "{key_path}" is not readable'

    # todo validate loading private key
    return True, None


def _password_generator() -> str:
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])


def _generate_private_key() -> str:
    # todo generate private key
    pass
