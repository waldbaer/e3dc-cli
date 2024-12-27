"""Argument / Configuration parsing."""

# ---- Imports ----
from typing import Any, Dict, List, Optional

from jsonargparse import ArgumentParser, DefaultHelpFormatter
from pydantic import SecretStr
from rich_argparse import RawTextRichHelpFormatter

from .connection import ConnectionType
from .query import QueryType

# ---- Constants & Types -----------------------------------------------------------------------------------------------


# ---- CommandLine parser ----------------------------------------------------------------------------------------------


class E3DCCliHelpFormatter(DefaultHelpFormatter, RawTextRichHelpFormatter):
    """Custom CLI help formatter: Combined DefaultHelpFormatter and RichHelpFormatter."""


def parse_config(prog: str, version: str, copy_right: str, author: str, arg_list: list[str] | None = None) -> Dict:
    """Parse the configuration from CLI and/or configuration JSON file.

    Arguments:
        prog: Program name.
        version: Program version.
        copy_right: Copyright info.
        author: Author info.
        arg_list: Optional command line arguments list.

    Returns:
        Dict: Parsed configuration options.
    """
    argparser = ArgumentParser(
        prog=prog,
        description=f"Query E3/DC solar inverter systems | Version {version} | {copy_right}",
        version=f"| Version {version}\n{copy_right} {author}",
        default_config_files=["./config.json"],
        print_config=None,
        env_prefix="E3DC_CLI",
        default_env=False,
        formatter_class=E3DCCliHelpFormatter,
    )

    # JSON config file
    argparser.add_argument(
        "-c",
        "--config",
        action="config",
        help="""Path to JSON configuration file.

All command line arguments can also be provided via an JSON configuration file (default: config.json).
A combination of both methods is also supported.

The JSON hierarchy can be derived from the shown command line arguments document in this help text.
The nested JSON hierarchies are defined by the "." dot notation.

Example:
    The following list of cli parameters:
    --connection.type,
    --connection.address,
    --connection.user
    --connection.password
    --connection.rscp_password

    is equivalent to the following JSON config file content:

    {
        "connection" : {
            "type" : "local",
            "address": "<IP or DNS address to the local E3/DC system>",
            "user": "<username>",
            "password": "<password>",
            "rscp_password": "<RSCP password>",
        },
        ...
    }

""",
    )

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
        help="""Connection type used for communication with the E3/DC system

local  Use local RSCP connection (recommended)
web    Use web connection
""",
        default=ConnectionType.local,
    )
    argparser.add_argument(
        "--connection.address",
        type=Optional[str],
        help="""IP or DNS address of the E3/DC system.
Only relevant for connection type 'local'.
""",
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
        help="""RSCP password. Set on the device via Main Page -> Personalize -> User profile -> RSCP password.
Only relevant for connection type 'local',
""",
    )
    argparser.add_argument(
        "--connection.serial_number",
        type=Optional[SecretStr],
        help="""Serial number of the system (see 'SN' in E3/DC portal).
Only relevant for connection type 'web'.
""",
    )

    # ---- Queries ----
    argparser.add_argument(
        "-q",
        "--query",
        type=QueryType,
        nargs="*",
        help="""Perform one or multiple live status or history queries:

Static System Infos:
- static_system             Static system info (Model, Sofware Version, Installed PeakPower / BatteryCapacity, ...)

Real-Time Status Queries:
- live                      Condensed status information (consumption, production, SoC, autarky, ...)
- live_system               General system status and power settings
- live_powermeter           Power meter status (power, energy and voltage of L1-L3, ...)
- live_battery              Battery status (SoC, temperatures, capacity, charge cycles, ...)
- live_inverter             Solar inverter status (input strings status, output phases, temperatures)
- live_wallbox              EV Wallbox status (SoC, consumption, max. charge current, ...)

Accumulated Historic Values (including production, consumption, battery in/out power, grid in/out power, autarky):
- history_today             Today
- history_yesterday         Yesterday
- history_week              Current Week (first day of week: Monday)
- history_previous_week     Previous Week (first day of week: Monday)
- history_month             Current Month
- history_previous_month    Previous Month
- history_year              Current Year (starting 01.Jan)
- history_previous_year     Previous Year
- history_total             Since 1970-01-01
""",
    )

    # ---- Setter ----
    argparser.add_argument(
        "--set.power_limits.enable",
        type=Optional[bool],
        metavar="{true,false}",
        help="""true: enable manual SmartPower limits. false: Use automatic mode.
Automatically set to 'true' if not explicitely set and any other manual limit
(max_charge, max_discharge or discharge_start) is set.
""",
    )
    argparser.add_argument(
        "--set.power_limits.max_charge",
        type=Optional[int],
        help="""SmartPower maximum charging power. Unit: Watt.
Automatically set to the systems max. battery charge power limit if not explicitely set.
Only relevant if set.power_limits.enable is 'true' or not explicitely configured.
""",
    )
    argparser.add_argument(
        "--set.power_limits.max_discharge",
        type=Optional[int],
        help="""SmartPower maximum discharging power. Unit: Watt.
Automatically set to the systems max. battery discharge power limit if not explicitely set.
Only relevant if set.power_limits.enable is 'true' or not explicitely configured.
""",
    )
    argparser.add_argument(
        "--set.power_limits.discharge_start",
        type=Optional[int],
        help="""SmartPower lower charge / discharge threshold. Unit: Watt.
Automatically set to the systems discharge default threshold if not explicitely set.
Only relevant if set.power_limits.enable is 'true' or not explicitely configured.
""",
    )

    argparser.add_argument(
        "--set.powersave",
        type=Optional[bool],
        metavar="{true,false}",
        help="Enable / Disable PowerSave of the inverter (inverter switches to standby mode when not in use).",
    )
    argparser.add_argument(
        "--set.weather_regulated_charge",
        type=Optional[bool],
        metavar="{true,false}",
        help="Enabled / Disable optimized charging based on the weather forecast.",
    )

    # ---- Advanced config of devices enumeration etc. ---
    argparser.add_argument(
        "--extended_config.powermeters",
        metavar="{ EXTENDED POWERMETERS CONFIG HIERARCHY }",
        type=List[Dict[str, Any]],
        help="""Extended power meters configuration.
For details see https://python-e3dc.readthedocs.io/en/latest/#configuration""",
    )
    argparser.add_argument(
        "--extended_config.pvis",
        metavar="{ EXTENDED SOLAR INVERTERS CONFIG HIERARCHY }",
        type=List[Dict[str, Any]],
        help="""Extended solar inverters configuration.
For details see https://python-e3dc.readthedocs.io/en/latest/#configuration""",
    )
    argparser.add_argument(
        "--extended_config.batteries",
        metavar="{ EXTENDED BATTERIES CONFIG HIERARCHY }",
        type=List[Dict[str, Any]],
        help="""Extended batteries configuration.
For details see https://python-e3dc.readthedocs.io/en/latest/#configuration""",
    )

    # ---- Finally parse the inputs  ----
    args = argparser.parse_args(args=arg_list)

    # ---- Argument Linking ----
    link_arguments(args)

    # ---- Post-parse validation ----
    validate_config(args)

    return args


def link_arguments(args: Dict) -> None:
    """Link Arguments.

    Arguments:
        args: Parsed configuration options.
    """
    # PowerLimits: Enable automatically if any custom charge attribute is set
    power_limits = args.set.power_limits
    if (power_limits.enable is None) and (
        (power_limits.max_charge is not None)
        or (power_limits.max_discharge is not None)
        or (power_limits.discharge_start is not None)
    ):
        power_limits.enable = True


def validate_config(args: Dict) -> None:
    """Validate the configuration.

    Arguments:
        args: Parsed configuration options.

    Raises:
        SystemError: If any validation issue was found.
    """
    found_config_issues = []
    if args.connection.type == ConnectionType.local:
        if not args.connection.address:
            found_config_issues.append("Connection address config is missing. Required for connection type 'local'.")
        if not args.connection.rscp_password:
            found_config_issues.append(
                "Connection RSCP password config is missing. Required for connection type 'local'."
            )
    if args.connection.type == ConnectionType.web:
        if not args.connection.serial_number:
            found_config_issues.append(
                "Connection serial number config is missing. Required for connection type 'web'."
            )

    if found_config_issues:
        raise SystemError("\n".join(found_config_issues))
