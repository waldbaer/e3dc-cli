"""Test for __main__.

Docs: https://pythontest.com/testing-argparse-apps/
"""

import importlib
import shlex

from pytest import CaptureFixture

from e3dc_cli.__main__ import cli
from e3dc_cli.__main__ import __dist_name__, __prog__

# ---- Testcases -------------------------------------------------------------------------------------------------------


def test_help(capsys: CaptureFixture[str]) -> None:
    """Test the --help option.

    Arguments:
        capsys: System capture
    """
    args = "--help"
    sys_exit = None
    try:
        cli(shlex.split(args))
    except SystemExit as e:
        sys_exit = e
    output = capsys.readouterr().out.rstrip()

    assert output.startswith(f"Usage: {__prog__}")
    assert sys_exit.code == 0


def test_version(capsys: CaptureFixture[str]) -> None:
    """Test the --version option.

    Arguments:
        capsys: System capture
    """
    args = "--version"
    sys_exit = None
    try:
        cli(shlex.split(args))
    except SystemExit as e:
        sys_exit = e
    output = capsys.readouterr().out.rstrip()

    assert importlib.metadata.version(__dist_name__) in output
    assert importlib.metadata.version(__prog__) in output
    assert sys_exit.code == 0
