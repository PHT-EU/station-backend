from pydantic import validator

from station.common.constants import DefaultValues


def is_default(value: str, default: DefaultValues) -> bool:
    return value == default.value


def validate_admin_password(value: str):
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
    try:
        with open(value, "r"):
            pass
    except Exception as e:
        raise AssertionError(f"Could not read file {value}: {e}")
    return value


def file_readable_validator(field_name: str):
    return validator(field_name, allow_reuse=True)(validate_file_readable)


def admin_validator(field_name: str = "admin_password"):
    return validator(field_name, allow_reuse=True)(validate_admin_password)
