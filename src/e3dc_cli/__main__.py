"""Commandline interface entry point."""

# ---- Imports ----
import importlib.metadata
from typing import Dict

from e3dc import E3DC

from .argparse import parse_config
from .connection import close_connection, setup_connection, wait_until_commands_applied
from .output import output_json_file, output_json_stdout
from .query import run_queries
from .setter import set_power_limits, set_power_save, set_weather_regulated_charge

# ---- Module Meta-Data ------------------------------------------------------------------------------------------------
__prog__ = "e3dc-cli"
__dist_name__ = "e3dc_cli"
__copyright__ = "Copyright 2022-2025"
__author__ = "Sebastian Waldvogel"
__dist_metadata__ = importlib.metadata.metadata("e3dc_cli")


# ---- Main Logic ------------------------------------------------------------------------------------------------------


def cli(arg_list: list[str] | None = None) -> None:
    """Main command line handling entry point.

    Arguments:
        arg_list: Optional list of command line arguments. Only needed for testing.
                  Productive __main__ will call the API without any argument.
    """
    args = parse_config(
        prog=__prog__,
        version=importlib.metadata.version(__dist_name__),
        copy_right=__copyright__,
        author=__author__,
        arg_list=arg_list,
    )
    e3dc = setup_connection(args.connection, args.extended_config)

    output = {}

    # ---- Main Set & Query Handling
    any_set_command_executed = run_set_commands(e3dc, args.set, output)

    if args.query is not None:
        if any_set_command_executed:
            wait_until_commands_applied(args.connection)
        run_queries(e3dc, args.query, output)

    # ---- Close Connection & Output Results ----
    close_connection(e3dc)

    if args.output is not None:
        output_json_file(args.output, output)
    else:
        output_json_stdout(output)


def run_set_commands(e3dc: E3DC, set_config: Dict, output: Dict) -> bool:
    """Run all configured setter commands.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        set_config: The configuration of the setter commands.
        output: The output dictionary filled with the setter command results.

    Returns:
        bool: True if any setter command was executed. Otherwise False.
    """
    any_setcommand_executed = False
    collected_results = {}

    if set_config.power_limits.enable is not None:
        collected_results["power_limits"] = set_power_limits(e3dc, set_config.power_limits)
    if set_config.powersave is not None:
        collected_results["powersave"] = set_power_save(e3dc, set_config.powersave)
    if set_config.weather_regulated_charge is not None:
        collected_results["weather_regulated_charge"] = set_weather_regulated_charge(
            e3dc, set_config.weather_regulated_charge
        )

    if collected_results.keys():
        output["set"] = collected_results
        any_setcommand_executed = True

    return any_setcommand_executed
