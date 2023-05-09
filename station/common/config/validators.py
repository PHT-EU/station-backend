import os

from cryptography.fernet import Fernet
from pydantic import SecretStr, validator

from station.common.constants import DefaultValues


def is_default(value: str, default: DefaultValues) -> bool:
    """Validate that the given value is not the default value

    Args:
        value: the value to check
        default: the default value to check against

    Returns:
        True if the value is the default value, False otherwise
    """
    return value == default.value


def validate_fernet_key(value: SecretStr):
    """Validation function for fernet key

    Args:
        value: the fernet key to validate

    Raises:
        ValueError: If the key is empty
        AssertionError: If the key is less than 32 characters or is the default key or is invalid
    Returns:
        the validated key
    """
    if not value:
        raise ValueError("Fernet key must not be empty")
    if len(value.get_secret_value()) < 32:
        raise AssertionError("Fernet key must be at least 32 characters")
    if is_default(value.get_secret_value(), DefaultValues.FERNET_KEY):
        raise AssertionError(
            f"Fernet key must not be the default key [{DefaultValues.FERNET_KEY.value}]"
        )

    # try to load the key to make sure it is valid
    try:
        Fernet(value.get_secret_value())
    except Exception as e:
        raise AssertionError(f"Invalid Fernet key: {e}")
    return value


def validate_admin_password(value: str):
    """Validation function for admin password

    Args:
        value: the admin password to validate

    Raises:
        ValueError: If the password is empty
        AssertionError: If the password is less than 8 characters or is the default password
    Returns:
        the validated password
    """
    if not value:
        raise ValueError("Password must not be empty")
    if len(value) < 8:
        raise AssertionError("Password must be at least 8 characters")
    if is_default(value, DefaultValues.ADMIN_PASSWORD):
        raise AssertionError(
            f"Password must not be the default password [{DefaultValues.ADMIN_PASSWORD.value}]"
        )
    return value


def validate_file_readable(value: str):
    """Validation function for a file that should be readable

    Args:
        value: the path to the file to validate

    Raises:
        AssertionError: if the file is not readable

    Returns:
        the file path
    """
    try:
        with open(value, "r"):
            pass
    except Exception as e:
        raise AssertionError(f"Could not read file {value}: {e}")
    return value


def validate_is_dir_and_writable(value: str):
    if os.path.isdir(value):
        if not os.access(value, os.R_OK | os.X_OK):
            raise AssertionError(f"Path {value} is not writable")

    raise AssertionError(f"Path {value} is not a directory")


def file_readable_validator(field_name: str):
    """Reusable pydantic validator function for a file that should be readable"""
    return validator(field_name, allow_reuse=True)(validate_file_readable)


def dir_validator(field_name: str):
    """
    Checks wether a path is a directory and is writable
    """
    return validator(field_name, allow_reuse=True)(validate_is_dir_and_writable)


def admin_validator(field_name: str = "admin_password"):
    """Reusable pydantic validator function for admin password"""
    return validator(field_name, allow_reuse=True)(validate_admin_password)
