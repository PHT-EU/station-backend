import os
import re
from enum import Enum
from typing import Any, Callable, List, Optional, Tuple, Union

from cryptography.fernet import Fernet
from pydantic import BaseModel

from station.common.config.generators import generate_fernet_key, password_generator
from station.common.constants import (
    ApplicationEnvironment,
    DefaultValues,
    PHTDirectories,
)


class ConfigItemValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    MISSING = "MISSING"
    FORBIDDEN_DEFAULT = "FORBIDDEN_DEFAULT"


class ConfigIssueLevel(str, Enum):
    WARN = "WARNING"
    ERROR = "ERROR"
    NONE = "NONE"


class ConfigValidationError(AssertionError):
    def __init__(self, message, status: ConfigItemValidationStatus):
        self.message = message
        self.status = status

    def __str__(self):
        return f"{self.status}: {self.message}"


class ConfigItemValidationResult(BaseModel):
    status: ConfigItemValidationStatus
    level: ConfigIssueLevel = ConfigIssueLevel.WARN
    field: str
    display_field: str
    value: Optional[Any] = None
    message: Optional[str] = ""
    generator: Optional[Callable[[], Any]] = None
    fix_hint: Optional[str] = ""
    validator: Optional[Callable[[Any], Tuple[bool, Union[None, str]]]] = None

    class Config:
        use_enum_values = True


def validate_registry_config(registry_config: dict) -> List[ConfigItemValidationResult]:
    validation_results = []
    # error if no registry config is given at all
    if registry_config is None:
        validation_results.append(
            ConfigItemValidationResult(
                status=ConfigItemValidationStatus.MISSING,
                level=ConfigIssueLevel.ERROR,
                field="registry",
                display_field="registry",
                message="Registry configuration missing",
                fix_hint="Add registry configuration to the configuration file",
            )
        )
        return validation_results

    # validate registry domain
    validation_results.append(
        _validate_config_value(
            registry_config, "address", prefix="registry", validator=_validate_domain
        )
    )

    user_result = _validate_config_value(registry_config, "user", prefix="registry")
    password_result = _validate_config_value(
        registry_config, "password", prefix="registry"
    )
    # todo add fix hints for validation
    validation_results.extend([user_result, password_result])

    return validation_results


def validate_db_config(db_config: dict) -> List[ConfigItemValidationResult]:
    validation_results = []
    # error if no db config is given at all
    if db_config is None:
        validation_results.append(
            ConfigItemValidationResult(
                status=ConfigItemValidationStatus.MISSING,
                level=ConfigIssueLevel.ERROR,
                field="db",
                display_field="db",
                message="Database configuration missing",
                fix_hint="Add database admin user and password to the configuration to the configuration file",
            )
        )
        return validation_results
    else:
        # validate db user
        user_result = _validate_config_value(
            db_config, "admin_user", prefix="db", generator=lambda: "admin"
        )
        if user_result.status != ConfigItemValidationStatus.VALID:
            user_result.fix_hint = "Add database admin user to the db configuration in the configuration file."
        validation_results.append(user_result)

        # validate db password
        validation_results.append(_validate_admin_password(db_config, prefix="db"))

    return validation_results


def validate_api_config(api_config: dict) -> List[ConfigItemValidationResult]:
    validation_results = []
    # error if no api config is given at all
    if not api_config:
        validation_results.append(
            ConfigItemValidationResult(
                status=ConfigItemValidationStatus.MISSING,
                level=ConfigIssueLevel.ERROR,
                field="api",
                display_field="api",
                message="API configuration missing",
                fix_hint="Add api configuration to the configuration file",
            )
        )
        return validation_results
    else:
        # validate fernet key
        fernet_result = _validate_config_value(
            api_config,
            "fernet_key",
            prefix="api",
            generator=generate_fernet_key,
            default_value=DefaultValues.FERNET_KEY.value,
            validator=_validate_fernet_key,
        )

        if fernet_result.status != ConfigItemValidationStatus.VALID:
            fernet_result.fix_hint = (
                "Add or update the fernet key into the api configuration of the "
                "configuration file."
            )

        validation_results.append(fernet_result)

    return validation_results


def validate_minio_config(minio_config: dict) -> List[ConfigItemValidationResult]:
    validation_results = []
    # error if no minio config is given at all
    if minio_config is None:
        validation_results.append(
            ConfigItemValidationResult(
                status=ConfigItemValidationStatus.MISSING,
                level=ConfigIssueLevel.ERROR,
                field="minio",
                display_field="minio",
                message="Minio configuration missing",
                fix_hint="Add minio configuration to the configuration file",
            )
        )
        return validation_results
    else:
        # validate password
        validation_results.append(
            _validate_admin_password(minio_config, prefix="minio")
        )

    return validation_results


def validate_airflow_config(airflow_config: dict) -> List[ConfigItemValidationResult]:
    validation_results = []
    # error if no airflow config is given at all
    if airflow_config is None:
        validation_results.append(
            ConfigItemValidationResult(
                status=ConfigItemValidationStatus.MISSING,
                level=ConfigIssueLevel.ERROR,
                field="airflow",
                display_field="airflow",
                message="Airflow configuration missing",
                fix_hint="Add airflow configuration to the configuration file",
            )
        )
        return validation_results
    else:
        # validate airflow admin user
        user_result = _validate_config_value(
            airflow_config, "admin_user", prefix="airflow", generator=lambda: "admin"
        )
        if user_result.status != ConfigItemValidationStatus.VALID:
            user_result.fix_hint = "Add airflow admin user to the airflow configuration in the configuration file."
        validation_results.append(user_result)

        # validate airflow admin password
        validation_results.append(
            _validate_admin_password(airflow_config, prefix="airflow")
        )

        # validate optional custom config file
        airflow_config_file = airflow_config.get("config_file")
        if airflow_config_file:
            config_results = _validate_config_value(
                airflow_config,
                "config_file",
                prefix="airflow",
                validator=_validate_file_path,
            )
            if config_results.status != ConfigItemValidationStatus.VALID:
                config_results.level = ConfigIssueLevel.ERROR
                config_results.fix_hint = "Update the path to the airflow configuration file in the configuration file."
            validation_results.append(config_results)

        # validate optional additional dags directory
        airflow_dags_dir = airflow_config.get("extra_dags_dir")
        if airflow_dags_dir:
            dags_dir_result = _validate_config_value(
                airflow_config,
                "extra_dags_dir",
                prefix="airflow",
                validator=_validate_file_path,
            )
            if dags_dir_result.status != ConfigItemValidationStatus.VALID:
                dags_dir_result.level = ConfigIssueLevel.ERROR
                dags_dir_result.fix_hint = (
                    "Update the path to the directory containing additional DAGs in the "
                    "configuration file."
                )
            validation_results.append(dags_dir_result)

    return validation_results


def validate_web_config(
    config: dict, strict: bool = True, host_path: str = None
) -> List[ConfigItemValidationResult]:
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
                    DefaultValues.HTTP_PORT.value
                ),
            )
        )
    else:
        # validate http port
        http_port = _validate_config_value(
            http_config, "port", validator=_validate_int, prefix="http"
        )
        http_port.generator = lambda: DefaultValues.HTTP_PORT.value
        if http_port.status == ConfigItemValidationStatus.MISSING:
            http_port.level = ConfigIssueLevel.WARN
            http_port.fix_hint = "Add http.port to config file if a specific port is desired. Defaults to {}".format(
                DefaultValues.HTTP_PORT.value
            )
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
                    DefaultValues.HTTPS_PORT.value
                ),
            )
        )

    else:
        # validate https port
        https_port = _validate_config_value(
            https_config, "port", validator=_validate_int, prefix="https"
        )
        https_port.generator = lambda: DefaultValues.HTTPS_PORT.value
        if https_port.status == ConfigItemValidationStatus.MISSING:
            https_port.level = (
                ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN
            )
            https_port.fix_hint = "Add https.port to config file if a specific port is desired. Defaults to {}".format(
                DefaultValues.HTTPS_PORT.value
            )
        elif https_port.status == ConfigItemValidationStatus.INVALID:
            https_port.level = ConfigIssueLevel.ERROR
            https_port.fix_hint = "Change https.port to a valid port number"

        validation_results.append(https_port)

        # validate domain
        https_domain = _validate_config_value(
            https_config,
            "domain",
            validator=_validate_domain,
            prefix="https",
        )
        if https_domain.status == ConfigItemValidationStatus.MISSING:
            https_domain.level = (
                ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN
            )
            https_domain.fix_hint = (
                "Add a valid https domain to config file when using https"
            )

        elif https_domain.status == ConfigItemValidationStatus.INVALID:
            https_domain.level = ConfigIssueLevel.ERROR
            https_domain.fix_hint = (
                f"Change https.domain ({https_domain.value}) to a valid domain"
            )

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
                    fix_hint="Add https.certs to config file if a certificate is desired. In development mode, you can "
                    "later generate a self-signed certificate",
                )
            )
        else:
            # validate certificate
            if not isinstance(certs, dict):
                validation_results.append(
                    ConfigItemValidationResult(
                        status=ConfigItemValidationStatus.INVALID,
                        level=ConfigIssueLevel.ERROR,
                        field="certs",
                        display_field="https.certs",
                        message="HTTPS certificates must be a dictionary",
                        fix_hint="Change https.certs to a dictionary",
                    )
                )

            else:

                def _validate_certs_val(val_result, path):
                    valid, message = _validate_file_path(path)
                    if not valid:
                        val_result.status = ConfigItemValidationStatus.INVALID
                        val_result.message = message
                        val_result.level = ConfigIssueLevel.ERROR
                        val_result.fix_hint = (
                            f"Change {val_result.field} to a valid file"
                        )

                cert = _validate_config_value(certs, "cert", prefix="https.certs")

                install_dir = config.get("install_dir", os.getcwd())
                cert_path = os.path.join(install_dir, "certs", cert.value)

                _validate_certs_val(cert, cert_path)

                if cert.status == ConfigItemValidationStatus.MISSING:
                    cert.level = (
                        ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN
                    )
                    cert.fix_hint = (
                        "Add a valid https certificate to config file when using https"
                    )
                elif cert.status == ConfigItemValidationStatus.INVALID:
                    cert.level = ConfigIssueLevel.ERROR
                    cert.fix_hint = (
                        "Change https.certs.cert to a valid certificate file path"
                    )

                validation_results.append(cert)

                # validate key
                key = _validate_config_value(certs, "key", prefix="https.certs")
                key_path = os.path.join(install_dir, "certs", key.value)
                _validate_certs_val(key, key_path)
                if key.status == ConfigItemValidationStatus.MISSING:
                    key.level = (
                        ConfigIssueLevel.ERROR if strict else ConfigIssueLevel.WARN
                    )
                    key.fix_hint = (
                        "Add a valid https key to config file when using https"
                    )
                elif key.status == ConfigItemValidationStatus.INVALID:
                    key.level = ConfigIssueLevel.ERROR
                    key.fix_hint = "Change https.certs.key to a valid key file path"

                validation_results.append(key)

    return validation_results


def validate_central_config(
    central_config: dict, host_path: str = None
) -> List[ConfigItemValidationResult]:
    """
    Validates the central services' config items
    """

    if not central_config:
        return [
            ConfigItemValidationResult(
                status=ConfigItemValidationStatus.MISSING,
                level=ConfigIssueLevel.ERROR,
                field="central",
                display_field="central",
                message="Central services configuration missing",
                fix_hint="Add address and credentials for the central API (available in the UI)"
                " to the station config file.",
            )
        ]

    validation_results = []

    # validate central api address
    api_url_result = _validate_config_value(
        central_config,
        field="api_url",
        prefix="central",
        validator=_validate_url,
        default_value=None,
    )
    api_url_result.level = ConfigIssueLevel.ERROR
    if api_url_result.status != ConfigItemValidationStatus.MISSING:
        api_url_result.fix_hint = "Add address for the central API ({central_domain}/api) to the station config file."
    elif api_url_result.status != ConfigItemValidationStatus.INVALID:
        api_url_result.fix_hint = f"Malformed central API URL: {api_url_result.value}"
    else:
        api_url_result.level = ConfigIssueLevel.NONE

    validation_results.append(api_url_result)

    # validate central credentials
    for robot_field in ["robot_id", "robot_secret"]:
        default = (
            DefaultValues.ROBOT_ID.value
            if robot_field == "robot_id"
            else DefaultValues.ROBOT_SECRET.value
        )
        robot_field_result = _validate_config_value(
            central_config, field=robot_field, prefix="central", default_value=default
        )
        if robot_field_result.status in (
            ConfigItemValidationStatus.MISSING,
            ConfigItemValidationStatus.FORBIDDEN_DEFAULT,
        ):
            robot_field_result.fix_hint = (
                "Set robot credentials from the central UI to the station config file."
            )
            robot_field_result.level = ConfigIssueLevel.ERROR
        elif robot_field_result.status != ConfigItemValidationStatus.INVALID:
            robot_field_result.fix_hint = (
                f"Malformed {robot_field}: {robot_field_result.value}"
            )
            robot_field_result.level = ConfigIssueLevel.ERROR
        validation_results.append(robot_field_result)

    # validate central private key

    if host_path and central_config.get("private_key"):
        private_key_path = (
            "/mnt/station/" + central_config.get("private_key").split("/")[-1]
        )
        central_config["private_key"] = private_key_path

    private_key_result = _validate_config_value(
        central_config,
        field="private_key",
        default_value=DefaultValues.PRIVATE_KEY.value,
        prefix="central",
        validator=_validate_private_key,
    )

    if private_key_result.status in [
        ConfigItemValidationStatus.MISSING,
        ConfigItemValidationStatus.FORBIDDEN_DEFAULT,
    ]:
        private_key_result.fix_hint = "Set path to private key registered in the central UI to the station config file."
        private_key_result.level = ConfigIssueLevel.ERROR
    elif private_key_result.status == ConfigItemValidationStatus.INVALID:
        private_key_result.fix_hint = (
            f'Ensure that the private key in "{private_key_result.value}" is readable and '
            f"a valid PEM file."
        )
        private_key_result.level = ConfigIssueLevel.ERROR

    validation_results.append(private_key_result)

    return validation_results


def validate_top_level_config(config: dict) -> List[ConfigItemValidationResult]:
    """
    Validates the top level config items which are version, admin password and station id, runtime environment and
    station data directory
    """

    validation_issues = []
    # validate station_id
    id_result = _validate_config_value(config, "station_id")

    if id_result.status != ConfigItemValidationStatus.VALID:
        id_result.fix_hint = "Login to user interface to obtain your station id and set it in the config file"
        id_result.level = ConfigIssueLevel.ERROR
        validation_issues.append(id_result)

    # validate runtime environment
    environment_result = _validate_config_value(
        config, "environment", validator=_environment_validator
    )
    if environment_result.status != ConfigItemValidationStatus.VALID:
        environment_result.fix_hint = (
            "Set environment to production. All values other than development will "
            "default to production"
        )
        environment_result.level = ConfigIssueLevel.WARN
        validation_issues.append(environment_result)
    # todo validate pht version

    admin_password_result = _validate_config_value(
        config,
        "admin_password",
        default_value=DefaultValues.ADMIN.value,
        generator=password_generator,
    )

    if admin_password_result.status != ConfigItemValidationStatus.VALID:
        admin_password_result.fix_hint = "Set admin password to a strong password"
        admin_password_result.level = ConfigIssueLevel.ERROR
        validation_issues.append(admin_password_result)

    # if no station data directory is specified use the default <install-dir>/station_data

    # get host path or install dir for creating a default station data dir
    install_dir = config.get("host_path")
    if not install_dir:
        install_dir = config.get("install_dir", os.getcwd())
    station_data_dir = os.path.join(install_dir, PHTDirectories.STATION_DATA_DIR.value)
    station_data_dir_result = _validate_config_value(
        config, "station_data_dir", default_value=station_data_dir
    )

    if station_data_dir_result.status != ConfigItemValidationStatus.VALID:
        station_data_dir_result.fix_hint = "Set station_data_dir to a valid directory"
        station_data_dir_result.level = ConfigIssueLevel.ERROR
        validation_issues.append(station_data_dir_result)

    return validation_issues


def _validate_admin_password(
    service_dict: dict, prefix: str
) -> ConfigItemValidationResult:
    """
    Validates the admin password
    """
    field = "admin_password"

    result = _validate_config_value(
        service_dict,
        field=field,
        prefix=prefix,
        default_value=DefaultValues.ADMIN.value,
        generator=password_generator,
    )
    if result.status in (
        ConfigItemValidationStatus.INVALID,
        ConfigItemValidationStatus.FORBIDDEN_DEFAULT,
    ):
        result.fix_hint = f"Update {prefix}.{field} to a valid password."

    if result.status == ConfigItemValidationStatus.MISSING:
        result.fix_hint = f"Set {prefix}.{field} to a valid password."

    return result


def _validate_config_value(
    config: dict,
    field: str,
    prefix: str = None,
    default_value: Any = None,
    validator: Callable[[Any], Tuple[bool, str]] = None,
    generator: Callable[[], Any] = None,
) -> ConfigItemValidationResult:
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
            message = (
                f'{display_field} can not be set to default value "{default_value}"'
            )

    if validator and field_value:
        valid, message = validator(field_value)
        status = (
            ConfigItemValidationStatus.VALID
            if valid
            else ConfigItemValidationStatus.INVALID
        )

    result = ConfigItemValidationResult(
        status=status,
        field=field,
        display_field=display_field,
        message=message,
        generator=generator,
        value=field_value,
    )

    return result


def _environment_validator(environment: str) -> Tuple[bool, Union[str, None]]:
    try:
        ApplicationEnvironment(environment)
        return True, None
    except ValueError:
        return False, f'Invalid environment "{environment}"'


def _validate_url(url: str) -> Tuple[bool, Union[str, None]]:
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"[A-Za-z0-9_-]*|"  # single word with hyphen/underscore for docker
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )  # path

    if re.match(regex, url):
        return True, None
    else:
        return False, f'Malformed url "{url}"'


def _validate_domain(domain: str) -> Tuple[bool, Union[str, None]]:
    regex = re.compile(r"([^.]+)\.([^.]+.)+")  # domain and all subdomains

    if re.match(regex, domain):
        return True, None
    else:
        return False, f'Malformed domain "{domain}"'


def _validate_int(value: Any) -> Tuple[bool, Union[str, None]]:
    try:
        int(value)
        return True, None
    except Exception as e:
        return False, f'Invalid integer "{value}" \n {e}'


def _validate_file_path(path: Any) -> Tuple[bool, Union[str, None]]:
    if os.path.isfile(path):
        return True, None
    elif not os.access(path, os.R_OK):
        return False, f'"{path}" is not readable'
    else:
        return False, f'"{path}" does not exist'


def _validate_private_key(key_path: str) -> Tuple[bool, Union[str, None]]:
    if not os.path.isfile(key_path):
        return False, f'Private key file "{key_path}" does not exist'
    if not os.access(key_path, os.R_OK):
        return False, f'Private key file "{key_path}" is not readable'
    # todo validate loading private key
    return True, None


def _validate_fernet_key(key: str) -> Tuple[bool, Union[str, None]]:
    try:
        Fernet(key)
        return True, None
    except Exception as e:
        return False, f'Invalid fernet key "{key}" \n {e}'
