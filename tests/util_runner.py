"""Utility for tool runner."""

import json
import os
import shlex
from ast import Dict

import pytest

from e3dc_cli.__main__ import cli

# ---- Utilities -------------------------------------------------------------------------------------------------------


def run_cli_stdout(cli_args: str, capsys: pytest.CaptureFixture) -> Dict:
    """Run the command line util with the passed arguments and capture the outputs from stdout.

    Arguments:
        cli_args: The command line arguments string passed.
        capsys: System capture

    Returns:
        Dict: Parsed JSON output from stdout.
    """
    output = run_cli(cli_args, capsys)
    parsed_json = json.loads(output)

    return parsed_json


def run_cli_json(cli_args: str, output_path: str, capsys: pytest.CaptureFixture) -> Dict:
    """Run the command line util with the passed arguments and capture the outputs from a JSON file.

    Arguments:
        cli_args: The command line arguments string passed.
        output_path: JSON output path
        capsys: System capture

    Returns:
        Dict: Parsed JSON output from stdout.
    """
    run_cli(cli_args, capsys)
    with open(file=output_path, encoding="UTF-8") as output_file:
        parsed_json = json.load(output_file)
    return parsed_json


def run_cli(cli_args: str, capsys: pytest.CaptureFixture) -> str:
    """Run the command line util with the passed arguments.

    Arguments:
        cli_args: The command line arguments string passed.
        capsys: System capture

    Returns:
        str: Captured stdout
    """
    cli(shlex.split(cli_args))
    return capsys.readouterr().out.rstrip()


class DefaultConfigJsonTemporaryRename:
    """Temporarily renaming the default config.json."""

    def __init__(self, file_path: str = "config.json", temporary_file_path: str = "config.json.tmp") -> None:
        """Initialize attributes.

        Arguments:
            file_path: Path of the default config.json
            temporary_file_path: Temporary path of the default config.json
        """
        self.file_path = file_path
        self.temporary_file_path = temporary_file_path

    def __enter__(self) -> None:
        """Rename file temporarily."""
        os.rename(self.file_path, self.temporary_file_path)
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:  # noqa: ANN001
        """Revert file renaming."""
        os.rename(self.temporary_file_path, self.file_path)
