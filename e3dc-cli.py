#!/usr/bin/env python3

# ---- Imports ----
import sys
import traceback
from typing import Any, Optional, List, Dict


from docstring_parser import DocstringStyle
from jsonargparse import set_docstring_parse_options
from jsonargparse import ArgumentParser

from pydantic import SecretStr
from enum import Enum

# https://github.com/fsantini/python-e3dc
from e3dc import E3DC
import json
from lib.connection import ConnectionType, SetupConnectionToE3DC
from lib.query import QueryType, RunMultiQuery
from lib.setter import (
    SetPowerLimitsConfig,
    SetPowerLimits,
    SetPowerSave,
    SetWeatherRegulatedCharge,
)

# , RunMultiSet

# ---- Constants & Types -------------------------------------------------------------------------------------------------------
__author__ = "Sebastian Waldvogel"
__copyright__ = "Copyright 2022-2024, Sebastian Waldvogel"
__license__ = "MIT"
__version__ = "1.0.0"


# ---- Main Logic ------------------------------------------------------------------------------------------------------


def Main():
    args = ParseConfig()
    e3dc = SetupConnectionToE3DC(args.connection, args.e3dc_config)

    output = {}

    if args.query != None:
        RunMultiQuery(e3dc, args.query, output)
    RunSetCommands(e3dc, args, output)

    OutputJson(output)


def RunSetCommands(e3dc, args, output):
    collected_results = {}

    if args.set_power_limits != None:
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
    set_docstring_parse_options(style=DocstringStyle.REST)
    set_docstring_parse_options(attribute_docstrings=True)
    argparser = ArgumentParser(
        prog="e3dc-cli.py",
        description=f"Query E3/DC systems | Version {
          __version__} | {__copyright__}",
        env_prefix="E3DC_CLI",
        default_config_files=["./config.json"],
        version=__version__,
    )

    # JSON config file
    argparser.add_argument("-c", "--config", action="config", help="Configuration File")

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

    # Advanced config of devices enumeration etc.
    argparser.add_argument("--e3dc_config.powermeters", type=List[Dict[str, Any]])
    argparser.add_argument("--e3dc_config.pvis", type=List[Dict[str, Any]])
    argparser.add_argument("--e3dc_config.batteries", type=List[Dict[str, Any]])

    # Queries
    argparser.add_argument(
        "-q",
        "--query",
        type=QueryType,
        nargs="*",
    )

    # Setter
    argparser.add_argument("--set_power_limits", type=Optional[SetPowerLimitsConfig])
    argparser.add_argument("--set_powersave", type=Optional[bool])
    argparser.add_argument("--set_weather_regulated_charge", type=Optional[bool])

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


def OutputJson(collected_data: Dict):
    print(json.dumps(collected_data, indent=2, default=str, sort_keys=True))


# ---- Utilities -------------------------------------------------------------------------------------------------------


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
