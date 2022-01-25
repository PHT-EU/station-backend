from pprint import pprint

import pytest
import os

from dotenv import load_dotenv, find_dotenv
import requests

from station.app.auth import get_robot_token, validate_user_token


@pytest.fixture
def auth_values():
    load_dotenv(find_dotenv())
    url = f"http://{os.getenv('AUTH_SERVER_HOST')}:{os.getenv('AUTH_SERVER_PORT')}/token"
    robot_id = os.getenv('AUTH_ROBOT_ID')
    robot_secret = os.getenv('AUTH_ROBOT_SECRET')
    return url, robot_id, robot_secret


def test_get_robot_token(auth_values):
    url, robot_id, robot_secret = auth_values
    if os.getenv("ENVIRONMENT") in ["development", "testing"]:
        token = get_robot_token(token_url=url, robot_id=robot_id, robot_secret=robot_secret)

        assert token


def test_validate_user_token(auth_values):
    if os.getenv("ENVIRONMENT") in ["development", "testing"]:
        url, robot_id, robot_secret = auth_values
        token = get_robot_token(token_url=url, robot_id=robot_id, robot_secret=robot_secret)

        # get user token
        data = {"username": "admin", "password": "start123"}
        response = requests.post(url, json=data)
        user_token = response.json()["access_token"]

        response = validate_user_token(token_url=url, token=user_token, robot_token=token)
        assert response.name == "admin"


