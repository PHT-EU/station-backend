from typing import Any, Optional, Union

import yaml
from pydantic import AnyHttpUrl, BaseModel, BaseSettings
from rich.pretty import pprint

from station.ctl.config.validators import ApplicationEnvironment


def parse_station_env_var_for_value(
    field_name: str, raw_val: str, prefix: str | None = None
) -> Any:
    """
    Parses a station environment variable and returns the value
    """
    pass


class CentralSettings(BaseSettings):
    api_url: AnyHttpUrl
    robot_id: str
    robot_secret: str
    private_key: str
    private_key_password: Optional[str] = None

    class Config:
        env_prefix = "STATION_CENTRAL_"


class HttpSettings(BaseSettings):
    port: Optional[Union[int, str]] = 80

    class Config:
        env_prefix = "STATION_HTTP_"


class Certificate(BaseModel):
    cert: str
    key: str

    class Config:
        env_prefix = "STATION_HTTPS_CERTIFICATE_"


class HttpsSettings(BaseSettings):
    port: Optional[Union[int, str]] = 443
    domain: str
    certificate: Optional[Certificate] = None

    class Config:
        env_prefix = "STATION_HTTPS_"


class TraefikDashboardSettings(BaseSettings):
    port: Optional[Union[int, str]] = 8081
    disable: Optional[bool] = False


class TraefikSettings(BaseSettings):
    dashboard: TraefikDashboardSettings

    class Config:
        env_prefix = "STATION_TRAEFIK_"


class RegistrySettings(BaseSettings):
    address: str
    user: str
    password: str
    project: str

    class Config:
        env_prefix = "STATION_REGISTRY_"


class ServiceSettings(BaseSettings):
    admin_user: str
    admin_password: str


class ExtendedServiceSettings(ServiceSettings):
    host: str
    port: Optional[int] = None


class DBSettings(ExtendedServiceSettings):
    class Config:
        env_prefix = "STATION_DB_"


class AirflowSettings(ExtendedServiceSettings):
    config_path: Optional[str] = None
    extra_dags_dir: Optional[str] = None

    class Config:
        env_prefix = "STATION_AIRFLOW_"


class MinioSettings(ExtendedServiceSettings):
    class Config:
        env_prefix = "STATION_MINIO_"


class AuthSettings(BaseSettings):
    host: str
    port: Optional[int] = 3001
    admin_user: Optional[str] = "admin"
    robot_id: Optional[str]
    robot_secret: Optional[str]

    class Config:
        env_prefix = "STATION_AUTH_"


class APISettings(BaseSettings):
    port: Optional[int] = 8000
    fernet_key: str
    database: Optional[str] = "pht_station"

    class Config:
        env_prefix = "STATION_API_"


class RedisSettings(BaseSettings):
    host: str
    port: Optional[int] = 6379
    admin_password: Optional[str] = None
    database: Optional[int] = 0

    class Config:
        env_prefix = "STATION_REDIS_"


class StationConfig(BaseSettings):
    station_id: str
    environment: ApplicationEnvironment
    admin_password: str
    station_data_dir: str
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
