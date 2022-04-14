import click
from rich.table import Table
from rich.style import Style

from station_ctl.config.validators import *

YELLOW = Style(color="yellow")
RED = Style(color="red")


def validate_config(config: dict) -> Tuple[List[ConfigItemValidationResult], Table]:
    """
    Validates a config file and returns a table containing the validation results
    """

    strict = config["environment"] != "development"
    validation_results = []
    # validate top level config items station_id, environment etc.
    top_level_results = validate_top_level_config(config)
    validation_results.extend(top_level_results)

    # validate configuration for central services
    central_results = validate_central_config(config.get("central"))
    validation_results.extend(central_results)

    # validate http/https config
    web_results = validate_web_config(config, strict=strict)
    validation_results.extend(web_results)

    # validate db config
    db_results = validate_db_config(config.get("db"))
    validation_results.extend(db_results)

    # validate airflow config
    airflow_results = validate_airflow_config(config.get("airflow"))
    validation_results.extend(airflow_results)

    # validate minio config
    minio_results = validate_minio_config(config.get("minio"))
    validation_results.extend(minio_results)

    # validate api config
    api_results = validate_api_config(config.get("api"))
    validation_results.extend(api_results)

    table = _generate_results_table(validation_results)
    return validation_results, table


def _generate_results_table(results: List[ConfigItemValidationResult]) -> Table:
    table = Table(title="Station config validation", show_lines=True, header_style="bold")
    table.add_column("Level", justify="center")
    table.add_column("Field", justify="center")
    table.add_column("Issue", justify="center")
    table.add_column("Fix", justify="center")

    for result in results:
        if result.status != ConfigItemValidationStatus.VALID:
            level_val = result.level.value
            # level = YELLOW.render(level_val) if result.level == ConfigIssueLevel.WARN else RED.render(level_val)
            table.add_row(level_val, result.display_field, result.message, result.fix_hint)

    return table
