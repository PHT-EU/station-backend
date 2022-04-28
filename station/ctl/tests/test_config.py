from rich.console import Console
import re

from station.ctl.config import validate_config
from station.ctl.constants import CERTS_REGEX


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



def test_match_cert_index():
    field_0 = "https.certs[0]"
    field_1 = "https.certs[12]"
    field_2 = "htps.certs[0]"
    field_3 = "https.certs[a]"

    assert re.match(CERTS_REGEX, field_0)
    assert re.match(CERTS_REGEX, field_0).group(1) == "0"
    assert re.match(CERTS_REGEX, field_1)
    assert re.match(CERTS_REGEX, field_2) is None
    assert re.match(CERTS_REGEX, field_3) is None
