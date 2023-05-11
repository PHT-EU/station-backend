import os
from typing import Optional, Union

import yaml
from pydantic import AnyHttpUrl, BaseSettings, SecretStr, validator
from pydantic.env_settings import SettingsSourceCallable
from rich.pretty import pprint

from station.common.config.fix import ConfigItemFix
from station.common.config.validators import (
    admin_validator,
    dir_validator,
    file_readable_validator,
    validate_fernet_key,
    validate_file_readable,
)
from station.common.constants import ApplicationEnvironment


class StationSettingsConfig:
    """Shared configuration for station settings"""

    use_enum_values = True
    env_prefix: str

    @classmethod
    def with_prefix(cls, prefix: str):
        """Returns a new class with the given prefix"""
        return type(cls.__name__, (cls,), {"env_prefix": prefix})

    @classmethod
    def customise_sources(
        cls,
        init_settings: SettingsSourceCallable,
        env_settings: SettingsSourceCallable,
        file_secret_settings: SettingsSourceCallable,
    ) -> tuple[SettingsSourceCallable, ...]:
        return env_settings, init_settings, file_secret_settings


class StationSettings(BaseSettings):
    """Base Settings with recursive construct method"""

    _fixable_fields: list[str] = []

    @classmethod
    def construct(cls, _fields_set=None, **values):
        """Construct a new model object from the function arguments. Recursively construct nested models.
        If an environment variable is available for a field, it will override the value passed in the function
        arguments.

        Args:
            _fields_set: Optional set of fields for hte model
            **values: The values to set for the model

        Returns:
            A new model object
        """
        m = cls.__new__(cls)
        fields_values = {}

        config = cls.__config__

        for name, field in cls.__fields__.items():
            key = field.alias
            if (
                key not in values and config.allow_population_by_field_name
            ):  # Added this to allow population by field name
                key = name

            if key in values:
                if (
                    values[key] is None and not field.required
                ):  # Moved this check since None value can be passed for Optional nested field
                    fields_values[name] = field.get_default()
                else:
                    # check for union type
                    if type(field.type_) == type(Union):
                        print("Found union type")

                    if issubclass(field.type_, BaseSettings):
                        # check if the field is a list of models
                        if field.shape == 2:
                            fields_values[name] = [
                                field.type_.construct(**e) for e in values[key]
                            ]
                        else:
                            fields_values[name] = field.outer_type_.construct(
                                **values[key]
                            )
                    else:
                        fields_values[name] = values[key]
            elif not field.required:
                fields_values[name] = field.get_default()

        # override with env variables
        # read the environment variables specs of the models
        # override the fields only if they are not of object type
        for name, field in m.__fields__.items():
            if issubclass(field.type_, BaseSettings):
                pass
            else:
                env_name = f"{config.env_prefix}{name.upper()}"
                env = os.getenv(env_name)
                if env:
                    # try to convert the value to the type of the field
                    if field.type_ == bool:
                        env = env.lower() == "true"
                    elif field.type_ == int:
                        env = int(env)
                    elif field.type_ == float:
                        env = float(env)
                    # set the value
                    fields_values[name] = env

        object.__setattr__(m, "__dict__", fields_values)
        if _fields_set is None:
            _fields_set = set(values.keys())
        object.__setattr__(m, "__fields_set__", _fields_set)

        m._init_private_attributes()
        return m

    def get_fix(self, field: str) -> ConfigItemFix:
        """Returns a fix for the field.
        Returns:
            ConfigItemFix: A fix for the field or None.
        """

        if field not in self.__class__.__fields__:
            raise ValueError(
                f"Field {field} does not exist in model {self.__class__.__name__}"
            )

        # if not hasattr(self, field):
        #     raise ValueError(
        #         f"Field {field} does not exist in model {self.__class__.__name__}"
        #     )


class ServiceSettings(StationSettings):
    """Model that contains common settings for configuring the connection to a service
    as admin user.
    """

    admin_user: str
    admin_password: SecretStr
    host: str
    port: Optional[int] = None
    # validator for admin password
    _admin_password = admin_validator()

    _fixable_fields = ["admin_password"]

    def get_fix(self, field: str) -> ConfigItemFix | None:
        """Returns a dict with the settings that can be used to fix the service.
        Returns:
            dict: dict with the settings that can be used to fix the service.
        """
        super().get_fix(field)
        match field:
            case "admin_password":
                if hasattr(self, "admin_password"):
                    if isinstance(self.admin_password, SecretStr):
                        val = self.admin_password.get_secret_value()
                    else:
                        val = self.admin_password
                else:
                    val = None
                return ConfigItemFix.admin_password(value=val)

            case _:
                return None


class CentralSettings(StationSettings):
    """Model that contains settings for configuring the connection to the central API as robot user."""

    url: AnyHttpUrl
    robot_id: str
    robot_secret: SecretStr
    private_key: str
    private_key_password: Optional[SecretStr] = None

    _private_key_validator = file_readable_validator("private_key")

    Config = StationSettingsConfig.with_prefix("STATION_CENTRAL_")

    def get_fix(self, field: str) -> ConfigItemFix | None:
        """Returns a dict with the settings that can be used to fix the service.
        Returns:
            dict: dict with the settings that can be used to fix the service.
        """
        super().get_fix(field)
        match field:
            case "private_key":
                val = None
                if hasattr(self, "private_key"):
                    val = self.private_key
                return ConfigItemFix.private_key(value=val)

            case _:
                return None


class HttpSettings(StationSettings):
    """General HTTP settings for the station."""

    port: Optional[int] = 80

    Config = StationSettingsConfig.with_prefix("STATION_HTTP_")


class Certificate(StationSettings):
    """Model that contains settings for configuring the HTTPS certificates."""

    cert: str
    key: str

    _cert_validator = file_readable_validator("cert")
    _key_validator = file_readable_validator("key")

    Config = StationSettingsConfig.with_prefix("STATION_HTTPS_CERTIFICATES_")


class HttpsSettings(StationSettings):
    """MOdel that contains the stations HTTPS settings."""

    port: Optional[int] = 443
    domain: str
    certificate: Optional[Certificate] = None

    Config = StationSettingsConfig.with_prefix("STATION_HTTPS_")


class TraefikSettings(StationSettings):
    """Configuration options for the Stations Traefik instance."""

    dashboard: Optional[bool] = False
    dashboard_port: Optional[int] = 8081

    Config = StationSettingsConfig.with_prefix("STATION_TRAEFIK_")


class RegistrySettings(StationSettings):
    """Model that contains settings for configuring the connection to the central container registry."""

    address: str
    user: str
    password: SecretStr
    project: str

    _password = admin_validator("password")

    Config = StationSettingsConfig.with_prefix("STATION_REGISTRY_")


class DBSettings(ServiceSettings):
    """Model that contains settings for configuring the connection to the database."""

    Config = StationSettingsConfig.with_prefix("STATION_DB_")


class AirflowSettings(ServiceSettings):
    """Model that contains settings for configuring the connection to the airflow instance.
    With the option of provididing a custom config and extra DAGs directory.
    """

    config_path: str | None = None
    extra_dags_dir: str | None = None

    @validator("config_path")
    def validate_config_path(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_file_readable(value)

    @validator("extra_dags_dir")
    def validate_extra_dags_dir(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if os.path.isdir(value):
            return value

    Config = StationSettingsConfig.with_prefix("STATION_AIRFLOW_")


class MinioSettings(ServiceSettings):
    """Model that contains settings for configuring the stations minio instance."""

    Config = StationSettingsConfig.with_prefix("STATION_MINIO_")


class AuthSettings(StationSettings):
    """Model that contains settings for configuring the stations authup instance."""

    host: str
    port: Optional[int] = 3001
    admin_user: Optional[str] = "admin"
    robot_id: Optional[str]
    robot_secret: Optional[SecretStr]

    Config = StationSettingsConfig.with_prefix("STATION_AUTH_")


class APISettings(StationSettings):
    """Model that contains settings for configuring the station API."""

    port: Optional[int] = 8000
    fernet_key: SecretStr
    database: Optional[str] = "pht_station"

    Config = StationSettingsConfig.with_prefix("STATION_API_")

    # todo validate fernet key

    @validator("fernet_key")
    def validate_fernet_key(cls, value: SecretStr) -> SecretStr:
        return validate_fernet_key(value)

    def get_fix(self, field: str) -> ConfigItemFix | None:
        """Returns a dict with the settings that can be used to fix the service.
        Returns:
            dict: dict with the settings that can be used to fix the service.
        """
        super().get_fix(field)
        match field:
            case "fernet_key":
                return ConfigItemFix.fernet_key(value=self.fernet_key)
            case _:
                return None


class RedisSettings(StationSettings):
    """Model that contains settings for configuring the stations redis instance."""

    host: str
    port: Optional[int] = 6379
    admin_password: Optional[SecretStr] = None
    database: Optional[int] = 0

    _admin_password = admin_validator()

    Config = StationSettingsConfig.with_prefix("STATION_REDIS_")

    def get_fix(self, field: str) -> ConfigItemFix:
        super().get_fix(field)

        match field:
            case "admin_password":
                return ConfigItemFix.admin_password(value=self.admin_password)
            case _:
                return None


class StationConfig(StationSettings):
    """Unified model that contains all settings for configuring the station."""

    id: str
    environment: ApplicationEnvironment
    admin_password: SecretStr
    data_dir: str
    version: str
    central: CentralSettings
    http: HttpSettings
    https: HttpsSettings
    traefik: TraefikSettings
    registry: RegistrySettings
    api: APISettings
    db: DBSettings
    airflow: AirflowSettings
    minio: MinioSettings
    auth: AuthSettings
    redis: RedisSettings

    _admin_password = admin_validator()
    _data_dir = dir_validator("data_dir")

    def display(self):
        pprint(self, expand_all=True)

    @classmethod
    def from_file(cls, path: str) -> "StationConfig":
        with open(path, "r") as f:
            # load yaml as dict
            return cls.parse_obj(yaml.safe_load(f))

    def get_fix(self, field: str) -> ConfigItemFix | None:
        """Returns a dict with the settings that can be used to fix the service.
        Returns:
            dict: dict with the settings that can be used to fix the service.
        """
        super().get_fix(field)
        match field:
            case "admin_password":
                val = None
                if hasattr(self, "admin_password"):
                    val = self.admin_password

                return ConfigItemFix.admin_password(value=val)

            case "data_dir":
                return ConfigItemFix.no_fix(
                    value=self.data_dir,
                    suggestion="Check that the path is correct and that the user has access to it.",
                )

            case "id":
                return ConfigItemFix.no_fix(
                    value=self.id,
                    suggestion="Enter the station id that is displayed in the central PHT user interface.",
                )

            case _:
                print(f"no fix for {field}")
                return None

    Config = StationSettingsConfig.with_prefix("STATION_")
