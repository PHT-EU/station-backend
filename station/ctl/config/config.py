from pydantic import BaseSettings, BaseModel, AnyHttpUrl

from typing import Optional, Union, List

from station.ctl.config.validators import ApplicationEnvironment


class CentralSettings(BaseSettings):
    api_url: AnyHttpUrl
    robot_id: str
    robot_secret: str
    private_key: str
    private_key_password: Optional[str] = None


class HttpSettings(BaseSettings):
    port: Optional[Union[int, str]] = 80


class Cert(BaseModel):
    cert: str
    key: str


class HttpsSettings(BaseSettings):
    port: Optional[Union[int, str]] = 443
    domain: str
    certs: Optional[List[Cert]] = None


class TraefikDashboardSettings(BaseSettings):
    port: Optional[Union[int, str]] = 8081
    disable: Optional[bool] = False


class TraefikSettings(BaseSettings):
    dashboard: TraefikDashboardSettings


class RegistrySettings(BaseSettings):
    address: str
    user: str
    password: str
    project: str


class ServiceSettings(BaseSettings):
    admin_user: str
    admin_password: str


class ExtendedServiceSettings(ServiceSettings):
    host: Optional[str] = None
    port: Optional[int] = None


class DBSettings(ExtendedServiceSettings):
    database: Optional[str] = "pht_station"


class AirflowSettings(ExtendedServiceSettings):
    pass


class MinioSettings(ServiceSettings):
    pass


class AuthSettings(ExtendedServiceSettings):
    robot_id: str
    robot_secret: str


class StationConfig(BaseSettings):
    station_id: str
    environment: ApplicationEnvironment
    station_data_dir: str
    version: str
    central: CentralSettings
    http: HttpSettings
    https: HttpsSettings
    traefik: TraefikSettings
    registry: RegistrySettings
    db: DBSettings
    airflow: AirflowSettings
    minio: MinioSettings
    auth: AuthSettings
