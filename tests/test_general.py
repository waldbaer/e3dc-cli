"""Test of general commands."""

import importlib
import os
import re

import pytest

from e3dc_cli.__main__ import __dist_name__, __prog__
from tests.util_runner import DefaultConfigJsonTemporaryRename, run_cli

# ---- Testcases -------------------------------------------------------------------------------------------------------


def test_ct_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the --help option.

    Arguments:
        capsys: System capture
    """
    args = "--help"

    cli_result = run_cli(args, capsys)
    assert cli_result.exit_code == os.EX_OK
    assert cli_result.stdout.startswith(f"Usage: {__prog__}")


def test_ct_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the --version option.

    Arguments:
        capsys: System capture
    """
    args = "--version"

    cli_result = run_cli(args, capsys)
    assert cli_result.exit_code == os.EX_OK
    assert importlib.metadata.version(__dist_name__) in cli_result.stdout
    assert importlib.metadata.version(__prog__) in cli_result.stdout


@pytest.mark.parametrize(
    "cli_args,expected_output",
    [
        (
            "--connection.type local --connection.rscp_password dummy_password",
            "Connection address config is missing",
        ),
        (
            "--connection.type local --connection.address 1.2.3.4",
            "Connection RSCP password config is missing",
        ),
        ("--connection.type web", "Connection serial number config is missing"),
    ],
)
def test_ct_invalid_connection_config(cli_args: str, expected_output: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Test with invalid connection configurations.

    Arguments:
        cli_args: Tested command line arguments
        expected_output: Expected output (RegEx)
        capsys: System capture
    """
    with DefaultConfigJsonTemporaryRename("config.json", "config.json.tmp"):
        cli_result = run_cli(cli_args, capsys)
        assert cli_result.exit_code != os.EX_OK
        assert expected_output in cli_result.stderr


@pytest.mark.parametrize(
    "cli_args,expected_output",
    [
        (
            "--connection.type xyz",
            r"Expected a member of.*enum.*ConnectionType.*Got value: xyz",
        ),
        (
            "-q UNKNOWN_QUERY",
            r"Expected a member of.*enum.*QueryType.*Got value: UNKNOWN_QUERY",
        ),
        (
            "--set.powersave 123",
            r"Does not validate against any of the Union subtypes",
        ),
    ],
)
def test_ct_invalid_arguments(cli_args: str, expected_output: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that invalid cli arguments are detected.

    Arguments:
        cli_args: Tested command line arguments
        expected_output: Expected output (RegEx)
        capsys: System capture
    """
    cli_result = run_cli(cli_args, capsys)
    assert cli_result.exit_code != os.EX_OK
    assert re.search(expected_output, cli_result.stderr)
