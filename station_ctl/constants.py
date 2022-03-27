from enum import Enum


class ServiceImages(Enum):
    API = "ghcr.io/pht-medic/station-api"
    UI = "ghcr.io/pht-medic/station-ui"
    AUTH = "ghcr.io/pht-medic/station-ui"
    AIRFLOW = "ghcr.io/pht-medic/station-airflow"
    MINIO = "minio/minio:latest"
    POSTGRES = "postgres:13"
    REDIS = "redislabs/rejson:latest"


class DefaultValues(Enum):
    # Default values for the station
    FERNET_KEY = "your_fernet_key"


class PHTDirectories(Enum):
    SERVICE_DATA_DIR = "/service_data"
    SERVICE_LOG_DIR = "/logs"
    CONFIG_DIR = "/configs"
    CERTS_DIR = "/certs"
    STATION_DATA_DIR = "/data"


class Icons(Enum):
    CHECKMARK = "✓"
    CROSS = "✗"
