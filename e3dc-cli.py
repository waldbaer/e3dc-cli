#!/usr/bin/env python3

# ---- Imports ----
import sys
import traceback
from typing import Any, Optional, List, Dict

from jsonargparse import ArgumentParser
from pydantic import SecretStr
from enum import Enum

# https://github.com/fsantini/python-e3dc
from e3dc import E3DC
import json
import datetime
import time
from tzlocal import get_localzone
from calendar import monthrange
from dateutil.relativedelta import relativedelta

# ---- Main ------------------------------------------------------------------------------------------------------------
__author__ = "Sebastian Waldvogel"
__copyright__ = "Copyright 2022-2024, Sebastian Waldvogel"
__license__ = "MIT"
__version__ = "1.0.0"

# Constants
DAYS_IN_A_WEEK = 7
HOURS_IN_A_DAY = 24
DAYS_IN_A_YEAR = 365

RSCP_ATTRIB_POWER_SAVE_ENABLED = "powerSaveEnabled"
KEEP_ALIVE = True

current_timezone = get_localzone()


class QueryType(Enum):
    live = "live"
    live_system = "live_system"
    live_powermeter = "live_powermeter"
    live_battery = "live_battery"
    live_inverter = "live_inverter"
    live_wallbox = "live_wallbox"
    history_today = "history_today"
    history_yesterday = "history_yesterday"
    history_week = "history_week"
    history_previous_week = "history_previous_week"
    history_month = "history_month"
    history_previous_month = "history_previous_month"
    history_year = "history_year"
    history_previous_year = "history_previous_year"
    history_all = "history_all"

    def __str__(self):
        return self.value


class ConnectionType(Enum):
    local = "local"
    web = "web"

    def __str__(self):
        return self.value


# ---- Main Logic ------------------------------------------------------------------------------------------------------


def main():
    args = ParseConfig()
    e3dc = SetupConnectionToE3DC(args.connection, args.e3dc_config)
    collected_data = RunMultiQuery(e3dc, args.query)
    OutputJson(collected_data)


def ParseConfig():
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

    # Getter queries
    argparser.add_argument(
        "-q",
        "--query",
        type=QueryType,
        nargs="+",
        default=[QueryType.live],
    )
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


def SetupConnectionToE3DC(connection_config, e3dc_config):
    params = {
        "username": connection_config.user.get_secret_value(),
        "password": connection_config.password.get_secret_value(),
        # Extended E3/DC configuration
        "configuration": e3dc_config,
        # IP address only needed for local connection
        "ipAddress": connection_config.address,
        # RSCP password only needed for local connection
        "key": (
            connection_config.rscp_password.get_secret_value()
            if connection_config.rscp_password
            else None
        ),
        # Serialnumber only needed for web connection
        "serialNumber": (
            connection_config.serial_number.get_secret_value()
            if connection_config.serial_number
            else None
        ),
    }

    e3dc = E3DC(
        connectType=(
            E3DC.CONNECT_WEB
            if connection_config.type.name == ConnectionType.web.name
            else E3DC.CONNECT_LOCAL
        ),
        **params,
    )
    return e3dc


def RunMultiQuery(e3dc, query_config):
    # Query requested data
    collected_data = {}
    for query in query_config:
        single_query_result = RunSingleQuery(e3dc, query)

        if single_query_result is not None:
            collected_data[query.name] = single_query_result

    return collected_data


def RunSingleQuery(e3dc, query):
    result = None

    # ---- Live Queries ----
    if query.name == QueryType.live.name:
        result = e3dc.poll(keepAlive=KEEP_ALIVE)
    elif query.name == QueryType.live_system.name:
        sys_status = e3dc.get_system_status(keepAlive=KEEP_ALIVE)
        # powerSaveEnabled option exists in both queries
        # Only the value in power_settings reflects the settings of web UI
        # Smart Functions -> Smart Power -> Power Save
        if RSCP_ATTRIB_POWER_SAVE_ENABLED in sys_status:
            del sys_status[RSCP_ATTRIB_POWER_SAVE_ENABLED]
        power_settings = e3dc.get_power_settings(keepAlive=KEEP_ALIVE)
        result = MergeDictionaries(sys_status, power_settings)
    elif query.name == QueryType.live_powermeter.name:
        result = e3dc.get_powermeter_data(keepAlive=KEEP_ALIVE)
    elif query.name == QueryType.live_battery.name:
        result = e3dc.get_battery_data(keepAlive=KEEP_ALIVE)
    elif query.name == QueryType.live_inverter.name:
        result = e3dc.get_pvi_data(keepAlive=KEEP_ALIVE)
    elif query.name == QueryType.live_wallbox.name:
        result = e3dc.get_wallbox_data(keepAlive=KEEP_ALIVE)

    # ---- History Queries ----
    elif query.name == QueryType.history_today.name:
        result = RunHistoryQueryDay(e3dc, past_days_from_now=0)
    elif query.name == QueryType.history_yesterday.name:
        result = RunHistoryQueryDay(e3dc, past_days_from_now=1)

    elif query.name == QueryType.history_week.name:
        result = RunHistoryQueryWeek(e3dc, past_weeks_from_now=0)
    elif query.name == QueryType.history_previous_week.name:
        result = RunHistoryQueryWeek(e3dc, past_weeks_from_now=1)

    elif query.name == QueryType.history_month.name:
        result = RunHistoryQueryMonth(e3dc, past_months_from_now=0)
    elif query.name == QueryType.history_previous_month.name:
        result = RunHistoryQueryMonth(e3dc, past_months_from_now=1)

    elif query.name == QueryType.history_year.name:
        result = RunHistoryQueryYear(e3dc, past_years_from_now=0)
    elif query.name == QueryType.history_previous_year.name:
        result = RunHistoryQueryYear(e3dc, past_years_from_now=1)

    elif query.name == QueryType.history_all.name:
        result = RunHistoryQueryAll(e3dc)

    else:
        raise SystemError(f"Unknown/unsupported query type '{query}'")

    return result


# ---- History Queries -------------------------------------------------------------------------------------------------


def RunHistoryQueryDay(e3dc, past_days_from_now):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    requestDate -= datetime.timedelta(days=past_days_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67
    # Due to unknown reason the E3DC portal provide the summarized values shifted by 15min.
    # This matches the "granularity" of 15min time slots used for accumulation (similar to CSV export data).
    # Example: Day history is summarizing all 15min slots starting 23:45 the day before until current day 23:45.
    requestDate -= datetime.timedelta(minutes=15)

    return QueryHistoryDatabase(
        e3dc,
        startTimestamp=GetStartTimestamp(requestDate),
        timespanSeconds=HoursToSeconds(HOURS_IN_A_DAY),
    )


def RunHistoryQueryWeek(e3dc, past_weeks_from_now):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    requestDate -= datetime.timedelta(
        days=requestDate.weekday()
    )  # subtract number of days since monday
    requestDate -= datetime.timedelta(days=DAYS_IN_A_WEEK * past_weeks_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67
    # Due to unknown reason the E3DC portal provide the summarized values shifted by 1h.
    # This matches the "granularity" of 1h time slots used for accumulation (similar to CSV export data).
    # Example: week history is summarizing all 1h time slots starting 0:00
    # first day of the week until last day of the week 23:00.
    requestDate -= datetime.timedelta(hours=1)

    return QueryHistoryDatabase(
        e3dc,
        startTimestamp=GetStartTimestamp(requestDate),
        timespanSeconds=HoursToSeconds(DAYS_IN_A_WEEK * HOURS_IN_A_DAY),
    )


def RunHistoryQueryMonth(e3dc, past_months_from_now=0):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    requestDate -= relativedelta(months=past_months_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67 is not necessary for month-based query

    days_in_select_month = monthrange(requestDate.year, requestDate.month)[1]
    return QueryHistoryDatabase(
        e3dc,
        startTimestamp=GetStartTimestamp(requestDate),
        timespanSeconds=HoursToSeconds(days_in_select_month * HOURS_IN_A_DAY),
    )


def RunHistoryQueryYear(e3dc, past_years_from_now=0):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    requestDate -= relativedelta(years=past_years_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67 is not necessary for year-based query
    return QueryHistoryDatabase(
        e3dc,
        startTimestamp=GetStartTimestamp(requestDate),
        timespanSeconds=HoursToSeconds(DAYS_IN_A_YEAR * HOURS_IN_A_DAY),
    )


def RunHistoryQueryAll(e3dc):
    now = datetime.datetime.now(tz=current_timezone)
    # Start query from 1970-01-02, avoid issues with timezones near to epoch 0.
    requestDate = now.replace(
        year=1970, month=1, day=2, hour=0, minute=0, second=1, microsecond=0
    )

    timeDeltaSinceRequestData = now - requestDate
    timespanSeconds = int(timeDeltaSinceRequestData.total_seconds())

    return QueryHistoryDatabase(
        e3dc,
        startTimestamp=GetStartTimestamp(requestDate),
        timespanSeconds=timespanSeconds,
    )


# ---- Outputs ---------------------------------------------------------------------------------------------------------


def OutputJson(collected_data):
    print(json.dumps(collected_data, indent=2, default=str, sort_keys=True))


# ---- Utilities -------------------------------------------------------------------------------------------------------


def QueryHistoryDatabase(e3dc, startTimestamp, timespanSeconds):
    return e3dc.get_db_data_timestamp(
        startTimestamp=startTimestamp,
        timespanSeconds=timespanSeconds,
        keepAlive=KEEP_ALIVE,
    )


def GetStartTimestamp(datetime):
    startTimestamp = int(time.mktime(datetime.timetuple()))
    # Due to unknown reasons the timestamp must be shifted by the delta of the
    # current and UTC a mix-up of UTC and the actual timezone
    startTimestamp += int(
        datetime.utcoffset().total_seconds()
    )  # Offset between current and UTC timezone
    return startTimestamp


def MergeDictionaries(*dicts):
    merged = {}
    for d in dicts:
        for key, value in d.items():
            if key in merged:
                value_of_merged = merged[key]
                if value != value_of_merged:
                    raise ValueError(
                        f"Failed to merge dictionaries."
                        f"Detected duplicate key '{key}' with different values: {
                  value} <-> {value_of_merged}"
                    )
            merged[key] = value
    return merged


def HoursToSeconds(hours):
    return hours * 60 * 60


# ---- Entrypoint ------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
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
