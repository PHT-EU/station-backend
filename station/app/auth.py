from enum import Enum
from typing import List

import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from requests import HTTPError

from station.app.cache import redis_cache
from station.app.config import settings
from station.app.schemas.users import User, UserPermission


class TokenCacheKeys(str, Enum):
    robot_token = "robot-token"
    user_token_prefix = "user-token-"


def get_robot_token(
    robot_id: str = None, robot_secret: str = None, token_url: str = None
) -> str:
    """
    Get robot token from auth server.
    """
    # todo token caching

    logger.debug("Getting robot token")

    if not token_url:
        token_url = settings.config.auth.token_url
    if not robot_id:
        robot_id = settings.config.auth.robot_id
    if not robot_secret:
        robot_secret = settings.config.auth.robot_secret.get_secret_value()

    # try to read the token from cache and return it if it exists
    cached_token = redis_cache.get(TokenCacheKeys.robot_token.value)
    if cached_token:
        logger.debug("Found cached robot token")
        return cached_token
    else:
        # get a new token from the auth server
        logger.debug(f"Requesting new robot token from {token_url}")
        data = {
            "id": robot_id,
            "secret": robot_secret,
            "grant_type": "robot_credentials",
        }

        response = requests.post(token_url, data=data).json()

        # parse values from response and set cache
        token = response.get("access_token")
        ttl = response.get("expires_in")

        redis_cache.set(TokenCacheKeys.robot_token.value, token, ttl)

        return token


def validate_user_token(token: str, user_url: str = None) -> User:
    """
    Validate a user token against the auth server and parse a user object from the response.
    Args:
        token: token to validate
        user_url: user url of the auth server

    Returns:
        User object parsed from the auth server response
    """
    # todo token caching
    if user_url is None:
        user_url = settings.config.auth.user_url
    url = f"{user_url}/@me"
    logger.debug(f"Validating user token against {url}")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    user = User(**r.json())
    return user


def get_current_user(token: str, token_url: str = None) -> User:
    """
    Validate a user token against the auth server and parse a user object from the response.
    Args:
        token: token to validate
        robot_token: the robot token to request token validation
        token_url: token url of the auth server

    Returns:
        User object parsed from the auth server response
    """

    logger.debug("Validating bearer token")
    if not settings.is_initialized:
        logger.error("Found uninitialized setting.... Initializing settings")
        settings.setup()
    if token_url is None:
        token_url = settings.config.auth.token_url
    try:
        user = validate_user_token(token=token)

        return user
    except HTTPError as e:
        logger.error(f"Error validating user token: {e}")
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid token")
        elif e.response.status_code == 400:
            # attempt refresh robot token
            try:

                get_robot_token(
                    robot_id=settings.config.auth.robot_id,
                    robot_secret=settings.config.auth.robot_secret.get_secret_value(),
                    token_url=token_url,
                )

                user = validate_user_token(token=token)
                return user
            except HTTPError:
                raise HTTPException(status_code=401, detail="Invalid token")


def get_user_permissions(user: User, token_url: str = None) -> List[UserPermission]:
    # todo token caching
    logger.debug(f"Getting user permissions for {user.name}")
    if token_url is None:
        token_url = settings.config.auth.token_url
    url = f"{token_url}/introspect"
    headers = {"Authorization": f"Bearer {user.token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    permissions = [UserPermission(**p) for p in r.json().get("permissions")]
    return permissions


# def authorized_user(token: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
#                     permissions: List[UserPermission] = None) -> User:
def authorized_user(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """
    Authorize a user by checking if they are in the allowed users list.
    Args:
        token: Bearer token from http header
        permissions: list of permissions to check

    Returns:
        User object if authorized

    """
    logger.debug("Authorizing user")
    user = get_current_user(token=token.credentials)
    # if permissions:
    #     user.permissions = get_user_permissions(user)
    #     # todo validate permissions

    return user
