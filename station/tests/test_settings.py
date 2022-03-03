import pytest
from dotenv import load_dotenv, find_dotenv
from unittest.mock import patch
import os
from yaml import safe_load, safe_dump

from pydantic import SecretStr

from station.app.config import Settings, AuthConfig, RegistrySettings, MinioSettings, CentralUISettings, StationConfig
from station.app.config import StationEnvironmentVariables


def test_settings_init_env_vars():
    load_dotenv(find_dotenv())
    # Test runtime environment variables
    with patch.dict(os.environ,
                    {
                        'ENVIRONMENT': 'production',
                        StationEnvironmentVariables.AUTH_SERVER_HOST.value: 'http://auth.example.com',
                        StationEnvironmentVariables.AUTH_SERVER_PORT.value: '3010',
                        StationEnvironmentVariables.AUTH_ROBOT_ID.value: 'robot',
                        StationEnvironmentVariables.AUTH_ROBOT_SECRET.value: 'robot_secret',
                        StationEnvironmentVariables.MINIO_HOST.value: 'http://minio.example.com',
                        StationEnvironmentVariables.MINIO_ACCESS_KEY.value: 'minio_user',
                        StationEnvironmentVariables.MINIO_SECRET_KEY.value: 'minio_secret',
                        StationEnvironmentVariables.STATION_DB.value: "postgres://db"
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

    with patch.dict(os.environ,
                    {
                        'ENVIRONMENT': 'development',
                        StationEnvironmentVariables.MINIO_HOST.value: 'http://registry.example.com',
                        StationEnvironmentVariables.MINIO_ACCESS_KEY.value: 'test',
                        StationEnvironmentVariables.MINIO_SECRET_KEY.value: 'test',
                    }):
        settings = Settings()
        settings.setup()
        assert settings.config.environment == 'development'
        assert settings.config.minio.host == 'http://registry.example.com'
        assert settings.config.minio.secret_key.get_secret_value() == 'test'
        assert settings.config.minio.access_key == 'test'


def test_config_file():
    load_dotenv(find_dotenv())
    settings = Settings()
    config = settings.setup()
    # write a working config
    config.station_id = "your_station_id"
    config.environment = "production"
    config.fernet_key = "your_fernet_key"
    config.host = "127.0.0.1"
    config.port = 8001
    config.auth = AuthConfig(
        host="127.0.0.1",
        port=3010,
        robot_id="your_robot_id",
        robot_secret="your_robot_secret",
    )
    config.registry = RegistrySettings(
        address="http://registry.example.com",
        user="test",
        password="test",
    )
    config.minio = MinioSettings(
        host="minio",
        port=9000,
        access_key="minio_access_key",
        secret_key="minio_secret_key",
    )
    config.central_ui = CentralUISettings(
        api_url="http://central-ui.example.com",
        client_id="central_ui_client_id",
        client_secret="central_ui_client_secret",

    )
    config = StationConfig(**settings.config.dict())

    config.to_file("station_config.yml")

    file_config = StationConfig.from_file("station_config.yml")
    assert file_config.station_id == "your_station_id"
    assert file_config.registry.user == "test"

# def test_settings():
#     settings = Settings(config_path="station_config.yml")
#     settings.setup()
#     assert settings.config
#     os.remove("station_config.yml")
