from typing import Any, Callable

from pydantic import BaseModel

from station.common.config.generators import (
    generate_fernet_key,
    generate_private_key,
    password_generator,
)


class GeneratorArg(BaseModel):
    prompt: str
    arg: str
    required: bool = True
    value: Any | None = None


class ConfigItemFix(BaseModel):
    issue: str
    value: Any | None = None
    suggestion: str
    fix: Any | None = None
    generator_function: Callable | None = None
    generator_args: list[GeneratorArg] | None = None

    @classmethod
    def no_fix(
        cls,
        suggestion: str,
        value: str | None = None,
    ) -> "ConfigItemFix":
        return cls(
            value=value,
            issue="",
            fix=None,
            suggestion=suggestion,
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

        # Generator arguments to generate a new private key
        args = [
            GeneratorArg(
                prompt="Enter the directory in which to save the private key",
                arg="path",
            ),
            GeneratorArg(
                prompt="Enter the name of the private key file",
                arg="name",
            ),
            GeneratorArg(
                prompt="Optionally Enter a passphrase to encrypt the private key",
                arg="password",
                required=False,
            ),
        ]
        return cls(
            issue="Invalid private key",
            value=value,
            suggestion="Either generate a new private key yourself or enter GENERATE to generate a new one",
            fix="GENERATE",
            generator_function=generate_private_key,
            generator_args=args,
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
