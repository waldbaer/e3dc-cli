"""Test of general commands."""

import importlib
import json

import pytest

from e3dc_cli.__main__ import __dist_name__, __prog__
from tests.util_runner import run_cli, run_cli_stdout

# ---- Testcases -------------------------------------------------------------------------------------------------------


def test_ct_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the --help option.

    Arguments:
        capsys: System capture
    """
    args = "--help"

    with pytest.raises(SystemExit) as sys_exit_info:
        run_cli(args, capsys)

    output = capsys.readouterr().out.rstrip()
    assert output.startswith(f"Usage: {__prog__}")
    assert sys_exit_info.value.code == 0


def test_ct_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the --version option.

    Arguments:
        capsys: System capture
    """
    args = "--version"

    with pytest.raises(SystemExit) as sys_exit_info:
        run_cli(args, capsys)

    output = capsys.readouterr().out.rstrip()
    assert importlib.metadata.version(__dist_name__) in output
    assert importlib.metadata.version(__prog__) in output
    assert sys_exit_info.value.code == 0


def test_ct_invalid_connection_config(capsys: pytest.CaptureFixture[str]) -> None:
    """Test with invalid connection configurations.

    Arguments:
        capsys: System capture
    """
    with pytest.raises(ValueError) as value_error:
        run_cli("--connection.type local --connection.address null", capsys)
    assert "Connection address config is missing" in str(value_error.value)

    with pytest.raises(ValueError) as value_error:
        run_cli("--connection.type local --connection.address 192.168.0.1 --connection.rscp_password null", capsys)
    assert "Connection RSCP password config is missing" in str(value_error.value)

    with pytest.raises(ValueError) as value_error:
        run_cli("--connection.type web --connection.serial_number null", capsys)
    assert "Connection serial number config is missing" in str(value_error.value)
