import os
from enum import Enum

from station_ctl.constants import PHTDirectories, ServiceDirectories


def ensure_directory_structure(path):
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
