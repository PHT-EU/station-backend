from enum import Enum


class Services(Enum):
    API = "ghcr.io/pht-medic/station-api"
    UI = "ghcr.io/pht-medic/station-ui"
    AIRFLOW = "ghcr.io/pht-medic/station-airflow"
    MINIO = "ghcr.io/pht-medic/station-airflow"


class DefaultValues(Enum):
    # Default values for the station
    FERNET_KEY = "your_fernet_key"


class Icons(Enum):
    CHECKMARK = "✓"
    CROSS = "✗"
