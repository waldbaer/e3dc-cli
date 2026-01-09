"""Commandline interface entry point."""

# ---- Imports ----
import importlib.metadata
import os

from .argparse import parse_config
from .connection import close_connection, setup_connection, wait_until_commands_applied
from .output import output_json_file, output_json_stdout
from .query import run_queries
from .setter import run_set_commands

# ---- Module Meta-Data ------------------------------------------------------------------------------------------------
__prog__ = "e3dc-cli"
__dist_name__ = "e3dc_cli"
__copyright__ = "Copyright 2022-2026"
__author__ = "Sebastian Waldvogel"
__dist_metadata__ = importlib.metadata.metadata("e3dc_cli")


# ---- Main Logic ------------------------------------------------------------------------------------------------------


def cli(arg_list: list[str] | None = None) -> None:
    """Main command line handling entry point.

    Arguments:
        arg_list: Optional list of command line arguments. Only needed for testing.
                  Productive __main__ will call the API without any argument.
    """
    try:
        config = parse_config(
            prog=__prog__,
            version=importlib.metadata.version(__dist_name__),
            copy_right=__copyright__,
            author=__author__,
            arg_list=arg_list,
        )
        return _main_logic(config)

    except SystemExit as e:
        return e.code

    except BaseException as e:  # pylint: disable=broad-exception-caught;reason=Explicitly capture all exceptions thrown during execution.
        print(
            f"ERROR: Any error has occurred!{os.linesep}{os.linesep}Exception: {str(e)}"
            # f"Detailed Traceback: {traceback.format_exc()}"
        )
        return 1


def _main_logic(config: dict) -> int:
    """Main program logic.

    Arguments:
        config: Configuration hierarchy

    Returns:
        Numeric exit code
    """
    e3dc = setup_connection(config.connection, config.extended_config)

    output = {}

    # ---- Main Set & Query Handling
    any_set_command_executed = run_set_commands(e3dc, config.set, output)

    if config.query is not None:
        if any_set_command_executed:
            wait_until_commands_applied(config.connection)
        run_queries(e3dc, config.query, output)

    # ---- Close Connection & Output Results ----
    close_connection(e3dc)

    if config.output is not None:
        output_json_file(config.output, output)
    else:
        output_json_stdout(output)

    return os.EX_OK
