import pytest
from dotenv import load_dotenv, find_dotenv
from unittest.mock import patch
import os

from station.app.config import Settings


def test_settings_init_env_vars():
    # Test runtime environment variables
    with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
        settings = Settings()
        settings.setup()
        assert settings.config.environment == 'production'

    with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
        settings = Settings()
        settings.setup()
        assert settings.config.environment == 'development'

    with pytest.raises(ValueError):
        with patch.dict(os.environ, {'ENVIRONMENT': 'fails'}):
            settings = Settings()
            settings.setup()

    with patch.dict(os.environ,
                    {
                        'ENVIRONMENT': 'development',
                        "STATION_ID": "test_station_id",
                        "FERNET_KEY": "test_fernet_key",
                        "STATION_API_HOST": "0.0.0.0",
                        "STATION_API_PORT": "8082",
                    }):
        settings = Settings()
        settings.setup()
        assert settings.config.station_id == "test_station_id"
        assert settings.config.environment == 'development'
        assert settings.config.fernet_key == 'test_fernet_key'
        assert settings.config.host == "0.0.0.0"
        assert settings.config.port == 8082

    with patch.dict(os.environ,
                    {
                        'ENVIRONMENT': 'development',
                        "STATION_ID": "test_station_id",
                        "FERNET_KEY": "",
                        "STATION_API_HOST": "0.0.0.0",
                        "STATION_API_PORT": "8082",
                    }):
        settings = Settings()
        settings.setup()
        assert settings.config.station_id == "test_station_id"
        assert settings.config.environment == 'development'
        assert settings.config.fernet_key
        assert settings.config.host == "0.0.0.0"
        assert settings.config.port == 8082

    with pytest.raises(ValueError):
        with patch.dict(os.environ,
                        {
                            'ENVIRONMENT': 'development',
                            "STATION_ID": "",
                            "FERNET_KEY": "",
                            "STATION_API_HOST": "0.0.0.0",
                            "STATION_API_PORT": "8082",
                        }):
            settings = Settings()
            settings.setup()

