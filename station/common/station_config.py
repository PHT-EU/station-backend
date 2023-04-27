from typing import Optional, Union

import yaml
from pydantic import AnyHttpUrl, BaseSettings
from pydantic.env_settings import SettingsSourceCallable
from rich.pretty import pprint

from station.ctl.config.validators import ApplicationEnvironment


class CentralSettings(BaseSettings):
    api_url: AnyHttpUrl
    robot_id: str
    robot_secret: str
    private_key: str
    private_key_password: Optional[str] = None

    class Config:
        env_prefix = "STATION_CENTRAL_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class HttpSettings(BaseSettings):
    port: Optional[Union[int, str]] = 80

    class Config:
        env_prefix = "STATION_HTTP_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class Certificate(BaseSettings):
    cert: str
    key: str

    class Config:
        env_prefix = "STATION_HTTPS_CERTIFICATES_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class HttpsSettings(BaseSettings):
    port: Optional[Union[int, str]] = 443
    domain: str
    certificate: Optional[Certificate] = None

    class Config:
        env_prefix = "STATION_HTTPS_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class TraefikSettings(BaseSettings):
    dashboard: Optional[bool] = False
    dashboard_port: Optional[Union[int, str]] = 8081

    class Config:
        env_prefix = "STATION_TRAEFIK_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class RegistrySettings(BaseSettings):
    address: str
    user: str
    password: str
    project: str

    class Config:
        env_prefix = "STATION_REGISTRY_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class ServiceSettings(BaseSettings):
    admin_user: str
    admin_password: str


class ExtendedServiceSettings(ServiceSettings):
    host: str
    port: Optional[int] = None


class DBSettings(ExtendedServiceSettings):
    class Config:
        env_prefix = "STATION_DB_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class AirflowSettings(ExtendedServiceSettings):
    config_path: Optional[str] = None
    extra_dags_dir: Optional[str] = None

    class Config:
        env_prefix = "STATION_AIRFLOW_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class MinioSettings(ExtendedServiceSettings):
    class Config:
        env_prefix = "STATION_MINIO_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class AuthSettings(BaseSettings):
    host: str
    port: Optional[int] = 3001
    admin_user: Optional[str] = "admin"
    robot_id: Optional[str]
    robot_secret: Optional[str]

    class Config:
        env_prefix = "STATION_AUTH_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class APISettings(BaseSettings):
    port: Optional[int] = 8000
    fernet_key: str
    database: Optional[str] = "pht_station"

    class Config:
        env_prefix = "STATION_API_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class RedisSettings(BaseSettings):
    host: str
    port: Optional[int] = 6379
    admin_password: Optional[str] = None
    database: Optional[int] = 0

    class Config:
        env_prefix = "STATION_REDIS_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings


class StationConfig(BaseSettings):
    id: str
    environment: ApplicationEnvironment
    admin_password: str
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

    def display(self):
        pprint(self)

    @classmethod
    def from_file(cls, path: str) -> "StationConfig":
        with open(path, "r") as f:
            # load yaml as dict
            return cls.parse_obj(yaml.safe_load(f))

    class Config:
        env_prefix = "STATION_"
        use_enum_values = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings
