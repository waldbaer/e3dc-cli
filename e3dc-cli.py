#!/usr/bin/env python3

# ---- Imports ----
from enum import Enum
from typing import Any, Optional, List, Dict
from pydantic import SecretStr

import sys
import traceback

from jsonargparse import ArgumentParser

# https://github.com/fsantini/python-e3dc
from e3dc import E3DC
import json
from lib.connection import ConnectionType, SetupConnectionToE3DC
from lib.query import QueryType, RunMultiQuery
from lib.setter import (
    SetPowerLimits,
    SetPowerSave,
    SetWeatherRegulatedCharge,
)

# ---- Constants & Types -------------------------------------------------------------------------------------------------------
__author__ = "Sebastian Waldvogel"
__copyright__ = "Copyright 2022-2024, Sebastian Waldvogel"
__license__ = "MIT"
__version__ = "1.0.0"


# ---- Main Logic ------------------------------------------------------------------------------------------------------


def Main():
    args = ParseConfig()
    e3dc = SetupConnectionToE3DC(args.connection, args.extended_config)

    output = {}

    if args.query != None:
        RunMultiQuery(e3dc, args.query, output)
    RunSetCommands(e3dc, args, output)

    e3dc.disconnect()

    if args.output != None:
        OutputJsonFile(args.output, output)
    else:
        OutputJsonStdout(output)


def RunSetCommands(e3dc, args, output):
    collected_results = {}

    if args.set_power_limits.enable != None:
        collected_results["power_limits"] = SetPowerLimits(e3dc, args.set_power_limits)
    if args.set_powersave != None:
        collected_results["powersave"] = SetPowerSave(e3dc, args.set_powersave)
    if args.set_weather_regulated_charge != None:
        collected_results["weather_regulated_charge"] = SetWeatherRegulatedCharge(
            e3dc, args.set_weather_regulated_charge
        )

    if collected_results.keys():
        output["set"] = collected_results


# ---- CommandLine parser ----------------------------------------------------------------------------------------------


def ParseConfig():
    argparser = ArgumentParser(
        prog="e3dc-cli.py",
        description=f"Query E3/DC systems | Version {
          __version__} | {__copyright__}",
        env_prefix="E3DC_CLI",
        default_env=False,
        default_config_files=["./config.json"],
        version=__version__,
    )

    # JSON config file
    argparser.add_argument("-c", "--config", action="config", help="Configuration File")

    # JSON output file
    argparser.add_argument(
        "-o",
        "--output",
        type=Optional[str],
        help="Path of JSON output file. If not set JSON output is written to console / stdout",
    )

    # Connection config
    argparser.add_argument(
        "--connection.type",
        type=ConnectionType,
        help="Connection type used for communication with the E3/DC system",
        default=ConnectionType.local,
    )
    argparser.add_argument(
        "--connection.address",
        type=Optional[str],
        help="IP or DNS address of the E3/DC system. Only relevant for connection type 'local'.",
    )
    argparser.add_argument(
        "--connection.user",
        type=SecretStr,
        help="Username (similar to the E3/DC portal)",
    )
    argparser.add_argument(
        "--connection.password",
        type=SecretStr,
        help="Password (similar to the E3/DC portal)",
    )
    argparser.add_argument(
        "--connection.rscp_password",
        type=Optional[SecretStr],
        help=f"RSCP password (set on the device via Main Page -> Personalize -> User profile -> RSCP password). Only relevant for connection type 'local'.",
    )
    argparser.add_argument(
        "--connection.serial_number",
        type=Optional[SecretStr],
        help="Serial number of the system (see 'SN' in E3/DC portal). Only relevant for connection type 'web'.",
    )

    # ---- Queries ----
    argparser.add_argument(
        "-q",
        "--query",
        type=QueryType,
        nargs="*",
        help="Perform one or multiple status / history queries of the solar inverter system.",
    )

    # ---- Setter ----
    argparser.add_argument(
        "--set_power_limits.enable",
        type=Optional[bool],
        help="True: enable manual SmartPower limits. False: Use automatic mode.",
    )
    argparser.add_argument(
        "--set_power_limits.max_charge",
        type=Optional[int],
        help="SmartPower maximum charging power [watt]. Only relevant if manual SmartPower limits are enabled.",
    )
    argparser.add_argument(
        "--set_power_limits.max_discharge",
        type=Optional[int],
        help="SmartPower maximum discharging power [watt]. Only relevant if manual SmartPower limits are enabled.",
    )
    argparser.add_argument(
        "--set_power_limits.discharge_start",
        type=Optional[int],
        help="SmartPower lower charge / discharge threshold [watts]. Only relevant if manual SmartPower limits are enabled.",
    )

    argparser.add_argument(
        "--set_powersave",
        type=Optional[bool],
        help="Enable / Disable PowerSave of the inverter (inverter switches to standby mode when not in use).",
    )
    argparser.add_argument(
        "--set_weather_regulated_charge",
        type=Optional[bool],
        help="Enabled / Disable optimized charging based on the weather forecast.",
    )

    # ---- Advanced config of devices enumeration etc. ---
    argparser.add_argument("--extended_config.powermeters", type=List[Dict[str, Any]])
    argparser.add_argument("--extended_config.pvis", type=List[Dict[str, Any]])
    argparser.add_argument("--extended_config.batteries", type=List[Dict[str, Any]])

    # ---- Finally parse the inputs  ----
    args = argparser.parse_args()

    # Custom consistency check
    found_config_issues = []
    if args.connection.type == ConnectionType.local:
        if not args.connection.address:
            found_config_issues.append(
                f"Connection address config is missing. Required for connection type 'local'."
            )
        if not args.connection.rscp_password:
            found_config_issues.append(
                f"Connection RSCP password config is missing. Required for connection type 'local'."
            )
    if args.connection.type == ConnectionType.web:
        if not args.connection.serial_number:
            found_config_issues.append(
                f"Connection serial number config is missing. Required for connection type 'web'."
            )

    if found_config_issues:
        raise SystemError("\n".join(found_config_issues))

    return args


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
