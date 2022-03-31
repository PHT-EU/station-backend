from typing import List

from station_ctl.config.validate import ConfigItemValidationResult, ConfigItemValidationStatus


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
            pass
    return config
