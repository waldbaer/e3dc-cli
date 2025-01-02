"""Test for __main__.

Docs: https://pythontest.com/testing-argparse-apps/
"""

import importlib

import pytest

from e3dc_cli.__main__ import __dist_name__, __prog__
from tests.util_runner import run_cli

# ---- Testcases -------------------------------------------------------------------------------------------------------


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
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


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
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
