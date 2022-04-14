import pytest
from rich.console import Console

from station_ctl.config import validate_config
from station_ctl.constants import DefaultValues


def test_validate_config():
    config = {
        'station_id': '',
        'version': 'latest',
        "environment": "test",
        "central": {
            "api_url": "https://api.test.com",
            "robot_id": "test-robot",
            "robot_secret": "test-secret",
        },
        "http": {
            "port": 8080,
        },
        "https": {
            "port": 8443,
            "domain": "test.com",
            "certs": [
                {
                    "key": "test-key",
                    "cert": "test-cert",
                },
                {
                    "key": "test-key2"
                }

            ]
        }

    }

    results, table = validate_config(config)
    console = Console()
    print()
    console.print(table)
