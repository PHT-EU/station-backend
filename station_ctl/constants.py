from enum import Enum


class PHTImages(Enum):
    API = "ghcr.io/pht-medic/station-api"
    UI = "ghcr.io/pht-medic/station-ui"
    AUTH = "ghcr.io/pht-medic/station-ui"
    AIRFLOW = "ghcr.io/pht-medic/station-airflow"


class ServiceImages(Enum):
    MINIO = "minio/minio:latest"
    POSTGRES = "postgres:13"
    REDIS = "redislabs/rejson:latest"
    TRAEFIK = "traefik:v2.6"


class DefaultValues(Enum):
    """
    Default values for the station configuration
    """
    FERNET_KEY = "your_fernet_key"
    ADMIN = "admin"
    PRIVATE_KEY = "/path/to/private_key.pem"
    STATION_DOMAIN = "example-station.com"
    CERT = "example-cert.pem"
    KEY = "example-key.pem"
    DOMAIN = "station.localhost"


class PHTDirectories(Enum):
    SERVICE_DATA_DIR = "service_data"
    SERVICE_LOG_DIR = "logs"
    CONFIG_DIR = "configs"
    CERTS_DIR = "certs"
    STATION_DATA_DIR = "data"
    SETUP_SCRIPT_DIR = "setup_scripts"


class ServiceDirectories(Enum):
    AUTH = "auth"
    MINIO = "minio"
    POSTGRES = "postgres"
    REDIS = "redis"


class Icons(Enum):
    CHECKMARK = "✔"
    CROSS = "❌"
    WARNING = "⚠"
