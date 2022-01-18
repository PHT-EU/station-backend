from typing import Tuple
from fastapi.security import OAuth2AuthorizationCodeBearer, HTTPBearer
import requests
from loguru import logger
from fastapi import Depends

from station.app.config import settings
from station.app.models.users import User, UserResponse


def get_robot_token(robot_id: str, robot_secret: str, token_url: str = None) -> str:
    """
    Get robot token from auth server.
    """
    # todo token caching

    if not token_url:
        token_url = settings.config.auth.token_url

    data = {
        "id": robot_id,
        "secret": robot_secret,
        "grant_type": "robot_credentials"
    }

    response = requests.post(token_url, data=data).json()
    return response["access_token"]


def validate_user_token(token: str, robot_token: str, token_url: str = None) -> User:
    """
    Validate a user token against the auth server and parse a user object from the response.
    Args:
        token: token to validate
        robot_token: the robot token to request token validation
        token_url: token url of the auth server

    Returns:
        User object parsed from the auth server response
    """
    # todo token caching
    if token_url is None:
        token_url = settings.config.auth.token_url
    url = f"{token_url}/{token}"
    headers = {"Authorization": f"Bearer {robot_token}"}
    r = requests.get(url, headers=headers)

    r.raise_for_status()
    response = r.json()
    if response.get("entity").get("type") == "user":
        user = User(**response.get("entity").get("data"))
        return user
    else:
        raise NotImplemented("Only user entities are supported.")


def get_current_user(token: str = Depends(HTTPBearer()),
                     robot_token: str = Depends(get_robot_token),
                     token_url: str = None) -> User:
    """
    Validate a user token against the auth server and parse a user object from the response.
    Args:
        token: token to validate
        robot_token: the robot token to request token validation
        token_url: token url of the auth server

    Returns:
        User object parsed from the auth server response
    """

    print(token)
    print(robot_token)
    if token_url is None:
        token_url = settings.config.auth.token_url

    user = validate_user_token(token=token, robot_token=robot_token, token_url=token_url)

    return user
