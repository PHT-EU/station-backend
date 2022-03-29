import pytest
from station_ctl.config import validate_config, StationConfig
from rich.console import Console


def test_validate_config():
    config = {
        'station_id': '',
        'version': 'latest',
        "environment": "test",
        "central": {
            "api_url": "https://api.test.com",
            "robot_id": "123456789",
            "robot_secret": "123456789",
        },
    }

    results, table = validate_config(config)
    console = Console()
    console.print(table)
