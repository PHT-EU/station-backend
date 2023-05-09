from typing import Any, Callable

from pydantic import BaseModel

from station.common.config.generators import (
    generate_fernet_key,
    generate_private_key,
    password_generator,
)


class ConfigItemFix(BaseModel):
    issue: str
    value: Any | None = None
    suggestion: str
    fix: Any | None = None
    generator_function: Callable | None = None
    generator_args: tuple | None = None

    @classmethod
    def no_fix(
        cls, loc: tuple, value: str | None = None, message: str | None = None
    ) -> "ConfigItemFix":
        return cls(
            value=value,
            issue=message if message else "",
            fix=None,
            suggestion="Please contact a PHT-meDIC team member for help",
        )

    @classmethod
    def admin_password(cls, value: str) -> "ConfigItemFix":
        suggested_password = password_generator()
        return cls(
            issue=f"Invalid admin password [{value}]",
            value=value,
            suggestion=f'Use suggested password: "{suggested_password}"',
            fix=suggested_password,
        )

    @classmethod
    def private_key(cls, value: str) -> "ConfigItemFix":
        """
        Fix that allow for the generation of a new private key
        """
        return cls(
            issue="Invalid private key",
            value=value,
            suggestion="Either generate a new private key yourself or enter GENERATE to generate a new one",
            fix="GENERATE",
            generator_function=generate_private_key,
        )

    @classmethod
    def fernet_key(cls, value: str) -> "ConfigItemFix":
        return cls(
            issue="Invalid fernet key",
            value=value,
            suggestion="Enter a valid fernet key or GENERATE to generate a new one",
            fix="GENERATE",
            generator_function=generate_fernet_key,
        )
