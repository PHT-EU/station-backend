import copy
import os.path
import sys
from typing import TYPE_CHECKING, Any, List

import click
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from station.common.clients.central.central_client import CentralApiClient
from station.common.config.fix import ConfigItemFix, GeneratorArg
from station.common.config.generators import GeneratorResult, generate_private_key
from station.common.config.station_config import StationConfig, StationSettings
from station.common.constants import Icons, PHTDirectories
from station.ctl.install.certs import generate_certificates

if TYPE_CHECKING:
    from station.ctl.config.validate import ValidationResult


def get_fixes_from_errors(config_dict: dict, errors: list[dict]) -> list[ConfigItemFix]:
    """Takes a list of validation errors resulting from initializing the station config pydantic model and
    returns a list of fixes that can be applied to the config to fix the errors.

    Args:
        errors: list of pydantic validation error dicts

    Returns:
        list of fixes that can be applied to the config to fix the errors
    """
    if len(errors) == 0:
        return []

    fixes = []

    # construct the config
    fixed_config = copy.deepcopy(config_dict)
    config = StationConfig.construct(**fixed_config)
    for error in errors:
        fix = get_fix_by_loc(
            config,
            error["loc"],
        )

        if fix:
            fixes.append(fix)
        else:
            unknown_fix = ConfigItemFix.no_fix(
                suggestion="Unable to fix error automatically or find suggestions. Please enter manually or "
                "contact the PHT team for help."
            )
            unknown_fix.issue = error["msg"]
            fixes.append(unknown_fix)
    return fixes


def get_fix_by_loc(config: StationConfig, loc: tuple) -> ConfigItemFix | None:
    """
    Returns the fix for the given location
    """

    level = len(loc)

    # get config attribute based on loc
    if level == 1:
        return config.get_fix(loc[0])
    # if it is a nested config item get the fix from the submodel
    else:
        sub_settings = _get_settings_for_loc(config, loc=loc)
        fix = sub_settings.get_fix(loc[-1])
        return fix


def _get_settings_for_loc(settings: StationSettings, loc: tuple) -> StationSettings:
    """
    Return the subsettings of the station settings for the given location
    """
    name = loc[0]

    if len(loc) == 1:
        return settings
    # get the model for the name
    model = getattr(settings, name)
    # get the sub model for the rest of the loc
    return _get_settings_for_loc(model, loc[1:])


def fix_config(ctx: dict, config: dict, results: List["ValidationResult"]) -> dict:
    """
    Allows for interactive fixes of issues in the station configuration
    Args:
        config: initial dictionary containing the config in the config yaml file
        results: validation results of the given dictionary

    Returns:
        updated config dictionary
    """
    fixed_config = copy.deepcopy(config)
    for result in results:
        # if the fix is a generator function, run it and set the value(s) in the config based on the results
        if result.fix.generator_function:
            prompt_text = "Manually enter a value or enter GENERATE to interactively generate a value"
            prompt_result = click.prompt(prompt_text, default="GENERATE")
            if prompt_result == "GENERATE":
                run_fix_generator(
                    fixed_config,
                    result.fix.generator_function,
                    result.fix.generator_args,
                )
            else:
                _set_config_value(fixed_config, ".".join(result.loc), prompt_result)

        else:
            fixed_value = click.prompt(
                result.fix.suggestion,
                default=result.fix.fix if result.fix.fix else None,
            )
            _set_config_value(fixed_config, ".".join(result.loc), fixed_value)

    return fixed_config


def run_fix_generator(
    config: dict, generator: callable, args: list[GeneratorArg] | None
) -> Any:
    """
    Runs a generator function and the configured arguments in an interactive prompt
    """

    if args is None:
        args = []

    arg_dict = {}
    # iterate over the arguments and prompt the user for the values
    for arg in args:
        value = click.prompt(arg.prompt, default="" if not arg.required else None)
        # prompt again if the value is required and not given
        if not value and arg.required:
            click.echo(
                f"{Icons.FAIL.value} {arg.arg} is a required argument for the generator function."
            )
            value = click.prompt(
                arg.prompt,
            )
            if not value:
                click.echo(
                    f"{Icons.FAIL.value} {arg.arg} is a required argument for the generator function. Exiting..."
                )
                sys.exit(1)
        arg_dict[arg.arg] = value

    # Get the result from the generator function
    result: list[GeneratorResult] | GeneratorResult = generator(**arg_dict)

    # Apply the result to the config
    if isinstance(result, list):
        for item in result:
            _set_config_value(config, ".".join(item.loc), item.value)
    else:
        _set_config_value(config, ".".join(result.loc), result.value)

    return


def _fix_certs(config: dict, strict: bool, install_dir: str):
    if strict:
        click.echo(
            "Valid certificates are required when not in development mode", err=True
        )
        sys.exit(1)

    domain = config["https"]["domain"]
    click.echo(f"Generating certificates for domain {domain}...")

    cert_dir = os.path.join(install_dir, PHTDirectories.CERTS_DIR.value)

    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")
    generate_certificates(domain, cert_path=str(cert_path), key_path=str(key_path))
    click.echo(f"Certificates generated at {cert_dir}")

    cert_list = config["https"].get("certs", [])
    if not cert_list:
        cert_list = []

    host_path = config.get("host_path", None)
    if host_path:
        cert_dir = os.path.join(host_path, PHTDirectories.CERTS_DIR.value)
        cert_path = os.path.join(cert_dir, "cert.pem")
        key_path = os.path.join(cert_dir, "key.pem")
    cert_paths = {"cert": str(cert_path), "key": str(key_path)}
    cert_list.append(cert_paths)
    config["https"]["certs"] = cert_list


def _fix_certs_path(config: dict, index: int, strict: bool = False):
    cert_path = config["https"]["certs"][index]["cert"]
    key_path = config["https"]["certs"][index]["key"]

    print(cert_path, key_path)
    if not cert_path and not key_path:
        _fix_certs(config, strict, config.get("install_dir", os.getcwd()))
        return
    if not os.path.isfile(cert_path):
        cert_path = click.prompt(
            f"Certificate at {cert_path} does not exist. "
            f"Please enter the correct path to the certificate file"
        )
        if not os.path.isfile(cert_path):
            click.echo("Certificate path is invalid", err=True)
        cert_path = str(os.path.abspath(cert_path))
    if not os.path.isfile(key_path):
        key_path = click.prompt(
            f"Key at {key_path} does not exist. "
            f"Please enter the correct path to the key file"
        )
        if not os.path.isfile(key_path):
            click.echo("Key path is invalid", err=True)
        key_path = str(os.path.abspath(key_path))

    config["https"]["certs"][index]["cert"] = cert_path
    config["https"]["certs"][index]["key"] = key_path


def _fix_private_key(config: dict) -> str:
    path = click.prompt(
        "Private key is missing enter the path to the private key "
        "file or press enter to generate a new one",
        default="GENERATE",
    )
    if path and path != "GENERATE":
        if not os.path.isfile(path):
            raise click.BadParameter(f"{path} is not a file")
        else:
            return path
    name = click.prompt("Name your private key file")
    passphrase = click.prompt(
        "Enter your passphrase. If given, it will be used to encrypt the private key",
        default="",
    )
    private_key_path, private_key, public_key = generate_private_key(
        name, config.get("install_dir"), passphrase
    )
    if passphrase:
        config["central"]["private_key_password"] = passphrase

    # if a host path is given append the name of the private key to this path
    host_path = config.get("host_path", None)
    if host_path:
        private_key_path = os.path.join(host_path, private_key_path)
        click.echo(
            f"Private key will be saved at: {private_key_path} on the host machine"
        )
    else:
        private_key_path = os.path.abspath(private_key_path)
        click.echo(f"New private key created: {private_key_path}")

    click.echo("Submitting public key to central API...", nl=False)
    # submit public key to central API
    _submit_public_key(config, public_key)
    click.echo(Icons.CHECKMARK.value)

    return private_key_path


def _set_config_value(config: dict, field: str, value: Any):
    nested_fields = field.split(".")
    if len(nested_fields) == 1:
        config[field] = value
    else:
        sub_config = None
        for field in nested_fields[:-1]:
            sub_config = config.get(field, {})
        sub_config[nested_fields[-1]] = value


def _submit_public_key(config: dict, public_key: rsa.RSAPublicKey):
    client = CentralApiClient(
        config["central"]["api_url"],
        robot_id=config["central"]["robot_id"],
        robot_secret=config["central"]["robot_secret"],
    )

    hex_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).hex()
    client.update_public_key(config["station_id"], hex_key)
