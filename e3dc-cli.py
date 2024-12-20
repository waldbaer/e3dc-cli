#!/usr/bin/env python3

# ---- Imports ----
from enum import Enum
from typing import Dict

import sys
import traceback
import json

from lib.argparse import ParseConfig
from lib.connection import (
    SetupConnectionToE3DC,
    CloseConnectionToE3DC,
    WaitUntilCommandsApplied,
)
from lib.query import RunQueries
from lib.setter import (
    SetPowerLimits,
    SetPowerSave,
    SetWeatherRegulatedCharge,
)

# ---- Constants & Types -------------------------------------------------------------------------------------------------------
__author__ = "Sebastian Waldvogel"
__copyright__ = "Copyright 2022-2024, Sebastian Waldvogel"
__license__ = "MIT"
__version__ = "0.9.0"


# ---- Main Logic ------------------------------------------------------------------------------------------------------


def Main():
    args = ParseConfig(copyright=__copyright__, version=__version__)
    e3dc = SetupConnectionToE3DC(args.connection, args.extended_config)

    output = {}

    # ---- Main Set & Query Handling
    any_set_command_executed = RunSetCommands(e3dc, args.set, output)

    if args.query != None:
        if any_set_command_executed:
            WaitUntilCommandsApplied(e3dc, args.connection)
        RunQueries(e3dc, args.query, output)

    # ---- Close Connection & Output Results ----
    CloseConnectionToE3DC(e3dc)

    if args.output != None:
        OutputJsonFile(args.output, output)
    else:
        OutputJsonStdout(output)


def RunSetCommands(e3dc, set_config, output):
    any_setcommand_executed = False
    collected_results = {}

    if set_config.power_limits.enable != None:
        collected_results["power_limits"] = SetPowerLimits(
            e3dc, set_config.power_limits
        )
    if set_config.powersave != None:
        collected_results["powersave"] = SetPowerSave(e3dc, set_config.powersave)
    if set_config.weather_regulated_charge != None:
        collected_results["weather_regulated_charge"] = SetWeatherRegulatedCharge(
            e3dc, set_config.weather_regulated_charge
        )

    if collected_results.keys():
        output["set"] = collected_results
        any_setcommand_executed = True

    return any_setcommand_executed


# ---- Outputs ---------------------------------------------------------------------------------------------------------


def OutputJsonStdout(collected_data: Dict):
    print(json.dumps(collected_data, indent=2, default=str, sort_keys=True))


def OutputJsonFile(output_file_path: str, collected_data: Dict):
    with open(output_file_path, "w", encoding="utf-8") as file:
        json.dump(collected_data, fp=file, indent=2, default=str, sort_keys=True)


# ---- Entrypoint ------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        Main()
    except SystemError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except SystemExit as exit:
        sys.exit(exit.code)
    except BaseException:
        print(
            f"ERROR: Any error has occured! Traceback:\r\n{
          traceback.format_exc()}"
        )
        sys.exit(1)
    sys.exit(0)
