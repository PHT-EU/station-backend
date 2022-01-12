import pytest
from dotenv import load_dotenv, find_dotenv
from unittest.mock import patch
import os

from station.app.config import Settings
from station.app.config import StationEnvironmentVariables


def test_settings_init_env_vars():
    # Test runtime environment variables
    with patch.dict(os.environ,
                    {
                        'ENVIRONMENT': 'production',
                        StationEnvironmentVariables.AUTH_SERVER_HOST.value: 'http://auth.example.com',
                        StationEnvironmentVariables.AUTH_SERVER_PORT.value: '3010',
                        StationEnvironmentVariables.AUTH_ROBOT_ID.value: 'robot',
                        StationEnvironmentVariables.AUTH_ROBOT_SECRET.value: 'robot_secret',
                    }):
        settings = Settings()
        settings.setup()
        assert settings.config.environment == 'production'
        assert settings.config.auth.host == 'http://auth.example.com'
        assert settings.config.auth.port == 3010
        assert settings.config.auth.robot_id == 'robot'

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

    with pytest.raises(ValueError):
        with patch.dict(os.environ,
                        {
                            'ENVIRONMENT': 'production',
                            StationEnvironmentVariables.AUTH_SERVER_HOST.value: '',
                            StationEnvironmentVariables.AUTH_SERVER_PORT.value: '',
                            StationEnvironmentVariables.AUTH_ROBOT_ID.value: '',
                            StationEnvironmentVariables.AUTH_ROBOT_SECRET.value: '',
                        }):
            settings = Settings()
            settings.setup()
    with patch.dict(os.environ,
                    {
                        'ENVIRONMENT': 'development',
                        StationEnvironmentVariables.AUTH_SERVER_HOST.value: '',
                        StationEnvironmentVariables.AUTH_SERVER_PORT.value: '',
                        StationEnvironmentVariables.AUTH_ROBOT_ID.value: '',
                        StationEnvironmentVariables.AUTH_ROBOT_SECRET.value: '',
                    }):
        settings = Settings()
        settings.setup()
        assert settings.config.environment == 'development'
        assert settings.config.auth is None

    with patch.dict(os.environ,
                    {
                        'ENVIRONMENT': 'development',
                        StationEnvironmentVariables.REGISTRY_URL.value: 'http://registry.example.com',
                        StationEnvironmentVariables.REGISTRY_USER.value: 'test',
                        StationEnvironmentVariables.REGISTRY_PW.value: 'test',
                    }):
        settings = Settings()
        settings.setup()
        assert settings.config.environment == 'development'
        assert settings.config.registry.address == 'http://registry.example.com'
        assert settings.config.registry.user == 'test'
        assert settings.config.registry.password.get_secret_value() == 'test'
