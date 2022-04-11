import os.path
from typing import List, Any

import click

from station_ctl.config.validate import ConfigItemValidationResult, ConfigItemValidationStatus
from station_ctl.config.generators import generate_private_key


def fix_config(config: dict, results: List[ConfigItemValidationResult]) -> dict:
    """
    Allows for interactive fixes of issues in the station configuration
    Args:
        config: initial dictionary containing the config in the config yaml file
        results: validation results of the given dictionary

    Returns:

    """
    strict = config["environment"] != "development"
    fixed_config = config.copy()
    for result in results:
        if result.status != ConfigItemValidationStatus.VALID:
            if result.display_field == "central.private_key":
                fixed_config["central"]["private_key"] = _fix_private_key()

            else:
                default = ""
                if result.generator:
                    default = result.generator()

                value = click.prompt(f'{result.display_field} is missing. {result.fix_hint}', default=default)
                if value:
                    _set_config_values(fixed_config, result.display_field, value)
                else:
                    _set_config_values(fixed_config, result.display_field, None)
    return fixed_config


def _fix_private_key() -> str:
    path = click.prompt("Private key is missing enter the path to the private key "
                        "file or press enter to generate a new one", default="GENERATE")
    if path and path != "GENERATE":
        if not os.path.isfile(path):
            raise click.BadParameter(f"{path} is not a file")
        else:
            return path

    name = click.prompt('Name your private key file')
    passphrase = click.prompt('Enter your passphrase. If given, it will be used to encrypt the private key', default="")
    private_key_path, private_key, public_key = generate_private_key(name, passphrase)
    private_key_abs_path = os.path.abspath(private_key_path)
    if not os.path.exists(private_key_path):
        click.echo(f'Private key file {private_key_abs_path} was not created. Please check the permissions.')
        return None
    else:
        click.echo(f'New private key created: {private_key_abs_path}')

    return private_key_abs_path


def _set_config_values(config: dict, field: str, value: Any) -> dict:
    nested_fields = field.split(".")
    if len(nested_fields) == 1:
        config[field] = value
    else:
        sub_config = None
        for field in nested_fields[:-1]:
            sub_config = config.get(field, {})
        sub_config[nested_fields[-1]] = value
