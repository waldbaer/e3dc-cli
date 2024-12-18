"""Commandline interface entry point."""

# ---- Imports ----
import importlib.metadata
from typing import Dict

from e3dc import E3DC

from .argparse import ParseConfig
from .connection import CloseConnectionToE3DC, SetupConnectionToE3DC, WaitUntilCommandsApplied
from .output import OutputJsonFile, OutputJsonStdout
from .query import RunQueries
from .setter import SetPowerLimits, SetPowerSave, SetWeatherRegulatedCharge

# ---- Module Meta-Data ------------------------------------------------------------------------------------------------
__prog__ = "e3dc-cli"
__dist_name__ = "e3dc_cli"
__copyright__ = "Copyright 2022-2024"
__author__ = "Sebastian Waldvogel"
__dist_metadata__ = importlib.metadata.metadata("e3dc_cli")


# ---- Main Logic ------------------------------------------------------------------------------------------------------


def cli() -> None:  # pylint: disable=invalid-name;reason=Required by pdm generated entrypoint script
    """Main command line handling entry point."""
    args = ParseConfig(
        prog=__prog__,
        version=importlib.metadata.version(__dist_name__),
        copy_right=__copyright__,
        author=__author__,
    )
    e3dc = SetupConnectionToE3DC(args.connection, args.extended_config)

    output = {}

    # ---- Main Set & Query Handling
    any_set_command_executed = RunSetCommands(e3dc, args.set, output)

    if args.query is not None:
        if any_set_command_executed:
            WaitUntilCommandsApplied(args.connection)
        RunQueries(e3dc, args.query, output)

    # ---- Close Connection & Output Results ----
    CloseConnectionToE3DC(e3dc)

    if args.output is not None:
        OutputJsonFile(args.output, output)
    else:
        OutputJsonStdout(output)


def RunSetCommands(e3dc: E3DC, set_config: Dict, output: Dict) -> bool:
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
        collected_results["power_limits"] = SetPowerLimits(e3dc, set_config.power_limits)
    if set_config.powersave is not None:
        collected_results["powersave"] = SetPowerSave(e3dc, set_config.powersave)
    if set_config.weather_regulated_charge is not None:
        collected_results["weather_regulated_charge"] = SetWeatherRegulatedCharge(
            e3dc, set_config.weather_regulated_charge
        )

    if collected_results.keys():
        output["set"] = collected_results
        any_setcommand_executed = True

    return any_setcommand_executed
