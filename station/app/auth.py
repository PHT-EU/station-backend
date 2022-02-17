from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from loguru import logger
from fastapi import Depends, HTTPException
from requests import HTTPError
from enum import Enum

from station.app.config import settings
from station.app.schemas.users import User
from station.app.cache import redis_cache


class TokenCacheKeys(str, Enum):
    robot_token = "robot-token"
    user_token_prefix = "user-token-"


def get_robot_token(robot_id: str = None, robot_secret: str = None, token_url: str = None) -> str:
    """
    Get robot token from auth server.
    """
    # todo token caching

    if not token_url:
        token_url = settings.config.auth.token_url
    if not robot_id:
        robot_id = settings.config.auth.robot_id
    if not robot_secret:
        robot_secret = settings.config.auth.robot_secret.get_secret_value()

    # try to read the token from cache and return it if it exists
    cached_token = redis_cache.get(TokenCacheKeys.robot_token.value)
    if cached_token:
        logger.debug(f"Found cached robot token")
        return cached_token
    else:
        # get a new token from the auth server
        logger.debug(f"Requesting new robot token from {token_url}")
        data = {
            "id": robot_id,
            "secret": robot_secret,
            "grant_type": "robot_credentials"
        }

        response = requests.post(token_url, data=data).json()

        # parse values from response and set cache
        token = response.get("access_token")
        ttl = response.get("expires_in")
        redis_cache.set(TokenCacheKeys.robot_token.value, token, ttl)

        return token


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
    print(headers)
    print(r.text)
    r.raise_for_status()
    response = r.json()
    if response.get("target").get("kind") == "user":
        user = User(**response.get("target").get("entity"),
                    permissions=response.get("target").get("permissions"))
        return user
    else:
        raise NotImplementedError("Only user entities are supported.")


def get_current_user(token: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
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

    logger.debug(f"Validating user token {token.credentials}")
    if token_url is None:
        token_url = settings.config.auth.token_url
    try:
        user = validate_user_token(token=token.credentials, robot_token=robot_token, token_url=token_url)
        return user
    except HTTPError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid token")
        elif e.response.status_code == 400:
            # attempt refresh robot token
            try:
                robot_token = get_robot_token(robot_id=settings.config.auth.robot_id,
                                              robot_secret=settings.config.auth.robot_secret.get_secret_value(),
                                              token_url=token_url)

                user = validate_user_token(token=token.credentials, robot_token=robot_token, token_url=token_url)
                return user
            except HTTPError:
                raise HTTPException(status_code=401, detail="Invalid token")
