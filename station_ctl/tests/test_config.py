import pytest
from station_ctl.config import validate_config, StationConfig
from rich.console import Console


def test_validate_config():
    config = {
        'station_id': 'test_station',
        'version': 'latest',
        "environment": "test",
    }

    table = validate_config(config)
    console = Console()
    console.print(table)