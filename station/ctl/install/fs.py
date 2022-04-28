import os
from enum import Enum
import click

from station.ctl.constants import PHTDirectories, ServiceDirectories


def check_create_pht_dirs(path):
    """
    Check that the directory structure exists, if it does prompt the user for update/overwrite, otherwise create it.
    """
    # check that pht directories exist
    pht_dir_check = _check_dirs_from_enum(path, PHTDirectories)
    service_dir_check = _check_dirs_from_enum(
        os.path.join(path, PHTDirectories.SERVICE_DATA_DIR.value),
        ServiceDirectories
    )

    if pht_dir_check and service_dir_check:
        click.confirm('The previous installation found, do you want to overwrite it?', abort=True)
        create_pht_dirs(path)
    else:
        create_pht_dirs(path)


def create_pht_dirs(path):
    """
    Ensure the directory structure exists.
    """
    if not os.path.exists(path):
        os.makedirs(path)

    # check that pht directories ex
    _make_dirs_from_enum(path, PHTDirectories)
    # create subdirectories for storing service data
    service_path = os.path.join(path, PHTDirectories.SERVICE_DATA_DIR.value)
    _make_dirs_from_enum(service_path, ServiceDirectories)


def _make_dirs_from_enum(path, dir_enum: Enum):
    for dir in dir_enum:
        dir_path = os.path.join(path, dir.value)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)


def _check_dirs_from_enum(path, dir_enum: Enum):
    for dir in dir_enum:
        dir_path = os.path.join(path, dir.value)
        if not os.path.isdir(dir_path):
            return False
    return True
