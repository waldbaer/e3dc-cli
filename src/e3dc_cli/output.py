"""Handling of different output formats."""

# ---- Imports ----
import json
from typing import Dict

# ---- Outputs ---------------------------------------------------------------------------------------------------------


def OutputJsonStdout(collected_data: Dict) -> None:
    """Output as JSON to stdout stream.

    Arguments:
        collected_data: Dictionary of collected data.
    """
    print(json.dumps(collected_data, indent=2, default=str, sort_keys=True))


def OutputJsonFile(output_file_path: str, collected_data: Dict) -> None:
    """Output as JSON to a file.

    Arguments:
        output_file_path: Path of the output file.
        collected_data: Dictionary of collected data.
    """
    with open(output_file_path, "w", encoding="utf-8") as file:
        json.dump(collected_data, fp=file, indent=2, default=str, sort_keys=True)
