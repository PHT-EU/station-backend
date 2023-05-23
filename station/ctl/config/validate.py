from enum import Enum
from typing import List, Tuple

from pydantic import BaseModel, ValidationError
from rich.style import Style
from rich.table import Table

from station.common.config.fix import ConfigItemFix
from station.common.config.station_config import StationConfig
from station.ctl.config.fix import get_fixes_from_errors


class Colors(Enum):
    YELLOW = Style(color="yellow")
    RED = Style(color="red")


class ValidationResult(BaseModel):
    loc: tuple
    fix: ConfigItemFix


def validate_config(
    config: dict, host_path: str = None
) -> Tuple[Table, List[ValidationResult]] | None:
    try:
        StationConfig(**config)
        return None
    except ValidationError as e:
        errors = e.errors()
        fixes = get_fixes_from_errors(config, errors)

        results = []

        for e, fix in zip(errors, fixes):
            fix.issue = e["msg"]
            results.append(
                ValidationResult(
                    loc=e["loc"],
                    fix=fix,
                )
            )

        table = _generate_results_table(results)

        return table, results
    except Exception as e:
        print("Unknown exception while validating config")
        print(e)
        raise e


def _generate_results_table(results: List[ValidationResult]) -> Table:
    table = Table(
        title="Staion config validation results", show_lines=True, header_style="bold"
    )
    table.add_column("Loc", justify="center")
    table.add_column("Issue", justify="center")
    table.add_column("Hint", justify="center")
    table.add_column("Fix", justify="center")

    for result in results:
        table.add_row(
            ".".join(result.loc),
            result.fix.issue,
            result.fix.suggestion,
            result.fix.fix,
        )

    return table
