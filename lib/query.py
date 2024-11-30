#!/usr/bin/env python3

# ---- Imports ----
from enum import Enum
from typing import Dict

# https://github.com/fsantini/python-e3dc
import datetime
import time
from tzlocal import get_localzone
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from lib.connection import E3DC

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


# ---- Query Logic -----------------------------------------------------------------------------------------------------


def RunMultiQuery(e3dc: E3DC, query_config: Dict, output: Dict):
    # Query requested data
    collected_data = {}
    for query in query_config:
        single_query_result = RunSingleQuery(e3dc, query)

        if single_query_result is not None:
            collected_data[query.name] = single_query_result

    if collected_data.keys():
        output["query"] = collected_data


def RunSingleQuery(e3dc: E3DC, query):
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


def RunHistoryQueryDay(e3dc: E3DC, past_days_from_now):
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


def RunHistoryQueryWeek(e3dc: E3DC, past_weeks_from_now):
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


def RunHistoryQueryMonth(e3dc: E3DC, past_months_from_now=0):
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


def RunHistoryQueryYear(e3dc: E3DC, past_years_from_now=0):
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


# ---- Utilities -------------------------------------------------------------------------------------------------------


def QueryHistoryDatabase(e3dc: E3DC, startTimestamp, timespanSeconds):
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
