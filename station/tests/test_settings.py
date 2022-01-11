import pytest
from dotenv import load_dotenv, find_dotenv
from unittest.mock import patch
import os

from station.app.config import Settings


def test_settings_init_env_vars():
    settings = Settings()

    with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
        settings = Settings()
        assert settings.config.environment == 'production'

    with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
        settings = Settings()
        assert settings.config.environment == 'development'


