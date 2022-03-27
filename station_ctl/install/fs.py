import os

from station_ctl.constants import PHTDirectories


def ensure_directory_structure(path):
    """
    Ensure the directory structure exists.
    """
    if not os.path.exists(path):
        os.makedirs(path)

    # check that pht directories ex
    for directory in PHTDirectories:
        dir_path = os.path.join(path, directory.value)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
