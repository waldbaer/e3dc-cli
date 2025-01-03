"""Query command implementation."""

# ---- Imports ----
import datetime
import time
from calendar import monthrange
from enum import Enum
from sqlite3.dbapi2 import Timestamp
from typing import Dict

from dateutil.relativedelta import relativedelta
from tzlocal import get_localzone

from .connection import E3DC

# ---- Constants & Types -----------------------------------------------------------------------------------------------

DAYS_IN_A_WEEK = 7
HOURS_IN_A_DAY = 24
DAYS_IN_A_YEAR = 365

RSCP_ATTRIB_POWER_SAVE_ENABLED = "powerSaveEnabled"
KEEP_ALIVE = True

current_timezone = get_localzone()


class QueryType(Enum):
    """All possible pre-defined query types."""

    static_system = "static_system"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    live = "live"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    live_system = "live_system"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    live_powermeter = "live_powermeter"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    live_battery = "live_battery"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    live_inverter = "live_inverter"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    live_wallbox = "live_wallbox"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_today = "history_today"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_yesterday = "history_yesterday"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_week = "history_week"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_previous_week = "history_previous_week"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_month = "history_month"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_previous_month = "history_previous_month"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_year = "history_year"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_previous_year = "history_previous_year"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    history_total = "history_total"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param

    def __str__(self) -> str:
        """Convert enum into string representation.

        Returns:
            Str: String representation of the enum value.
        """
        return self.value


# ---- Query Logic -----------------------------------------------------------------------------------------------------


def run_queries(e3dc: E3DC, query_config: Dict, output: Dict) -> None:
    """Execute all configured queries.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        query_config: The configurations of all queries.
        output: The output dictionary filled with the query results.
    """
    collected_data = {}
    for query in query_config:
        single_query_result = run_query(e3dc, query)

        if single_query_result is not None:
            collected_data[query.name] = single_query_result

    if collected_data.keys():
        output["query"] = collected_data


def run_query(e3dc: E3DC, query: Dict) -> Dict:
    """Execute a single query.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        query: Single query configuration.

    Returns:
        Dict: Dictionary with the query results.

    Raises:
        ValueError: If an unknown/unsupported query is requested.
    """
    result = None

    # ---- Static Queries ----
    if query.name == QueryType.static_system.name:
        result = e3dc.get_system_info(keepAlive=KEEP_ALIVE)
    # ---- Live Queries ----
    elif query.name == QueryType.live.name:
        result = e3dc.poll(keepAlive=KEEP_ALIVE)
    elif query.name == QueryType.live_system.name:
        sys_status = e3dc.get_system_status(keepAlive=KEEP_ALIVE)
        # powerSaveEnabled option exists in both queries
        # Only the value in power_settings reflects the settings of web UI
        # Smart Functions -> Smart Power -> Power Save
        if RSCP_ATTRIB_POWER_SAVE_ENABLED in sys_status:
            del sys_status[RSCP_ATTRIB_POWER_SAVE_ENABLED]
        power_settings = e3dc.get_power_settings(keepAlive=KEEP_ALIVE)
        result = merge_dictionaries(sys_status, power_settings)
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
        result = run_history_query_day(e3dc, past_days_from_now=0)
    elif query.name == QueryType.history_yesterday.name:
        result = run_history_query_day(e3dc, past_days_from_now=1)

    elif query.name == QueryType.history_week.name:
        result = run_history_query_week(e3dc, past_weeks_from_now=0)
    elif query.name == QueryType.history_previous_week.name:
        result = run_history_query_week(e3dc, past_weeks_from_now=1)

    elif query.name == QueryType.history_month.name:
        result = run_history_query_month(e3dc, past_months_from_now=0)
    elif query.name == QueryType.history_previous_month.name:
        result = run_history_query_month(e3dc, past_months_from_now=1)

    elif query.name == QueryType.history_year.name:
        result = run_history_query_year(e3dc, past_years_from_now=0)
    elif query.name == QueryType.history_previous_year.name:
        result = run_history_query_year(e3dc, past_years_from_now=1)

    elif query.name == QueryType.history_total.name:
        result = run_history_query_total(e3dc)

    else:
        raise ValueError(f"Unknown/unsupported query type '{query.name}'")

    return result


# ---- History Queries -------------------------------------------------------------------------------------------------


def run_history_query_day(e3dc: E3DC, past_days_from_now: int) -> Dict:
    """Query historic data from the database for the time range 'day'.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        past_days_from_now: Number of past days from now.

    Returns:
        Dict: Dictionary with the query result.
    """
    request_date = datetime.datetime.now(tz=current_timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    request_date -= datetime.timedelta(days=past_days_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67
    # Due to unknown reason the E3DC portal provide the summarized values shifted by 15min.
    # This matches the "granularity" of 15min time slots used for accumulation (similar to CSV export data).
    # Example: Day history is summarizing all 15min slots starting 23:45 the day before until current day 23:45.
    request_date -= datetime.timedelta(minutes=15)

    return query_history_database(
        e3dc,
        start_timestamp=get_start_timestamp(request_date),
        timespan_seconds=hours_to_seconds(HOURS_IN_A_DAY),
    )


def run_history_query_week(e3dc: E3DC, past_weeks_from_now: int) -> Dict:
    """Query historic data from the database for the time range 'week'.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        past_weeks_from_now: Number of past weeks from now.

    Returns:
        Dict: Dictionary with the query result.
    """
    request_date = datetime.datetime.now(tz=current_timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    request_date -= datetime.timedelta(days=request_date.weekday())  # subtract number of days since monday
    request_date -= datetime.timedelta(days=DAYS_IN_A_WEEK * past_weeks_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67
    # Due to unknown reason the E3DC portal provide the summarized values shifted by 1h.
    # This matches the "granularity" of 1h time slots used for accumulation (similar to CSV export data).
    # Example: week history is summarizing all 1h time slots starting 0:00
    # first day of the week until last day of the week 23:00.
    request_date -= datetime.timedelta(hours=1)

    return query_history_database(
        e3dc,
        start_timestamp=get_start_timestamp(request_date),
        timespan_seconds=hours_to_seconds(DAYS_IN_A_WEEK * HOURS_IN_A_DAY),
    )


def run_history_query_month(e3dc: E3DC, past_months_from_now: int = 0) -> Dict:
    """Query historic data from the database for the time range 'month'.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        past_months_from_now: Number of past months from now.

    Returns:
        Dict: Dictionary with the query result.
    """
    request_date = datetime.datetime.now(tz=current_timezone).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    request_date -= relativedelta(months=past_months_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67 is not necessary for month-based query

    days_in_select_month = monthrange(request_date.year, request_date.month)[1]
    return query_history_database(
        e3dc,
        start_timestamp=get_start_timestamp(request_date),
        timespan_seconds=hours_to_seconds(days_in_select_month * HOURS_IN_A_DAY),
    )


def run_history_query_year(e3dc: E3DC, past_years_from_now: int = 0) -> Dict:
    """Query historic data from the database for the time range 'year'.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        past_years_from_now: Number of past years from now.

    Returns:
        Dict: Dictionary with the query result.
    """
    request_date = datetime.datetime.now(tz=current_timezone).replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    request_date -= relativedelta(years=past_years_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67 is not necessary for year-based query
    return query_history_database(
        e3dc,
        start_timestamp=get_start_timestamp(request_date),
        timespan_seconds=hours_to_seconds(DAYS_IN_A_YEAR * HOURS_IN_A_DAY),
    )


def run_history_query_total(e3dc: E3DC) -> Dict:
    """Query historic data from the database for the time range 'total'.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.

    Returns:
        Dict: Dictionary with the query result.
    """
    now = datetime.datetime.now(tz=current_timezone)
    # Start query from 1970-01-02, avoid issues with timezones near to epoch 0.
    request_date = now.replace(year=1970, month=1, day=2, hour=0, minute=0, second=1, microsecond=0)

    time_delta_since_request_data = now - request_date
    timespan_seconds = int(time_delta_since_request_data.total_seconds())

    return query_history_database(
        e3dc,
        start_timestamp=get_start_timestamp(request_date),
        timespan_seconds=timespan_seconds,
    )


# ---- Utilities -------------------------------------------------------------------------------------------------------


def query_history_database(e3dc: E3DC, start_timestamp: Timestamp, timespan_seconds: int) -> Dict:
    """Query historic data from the database.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        start_timestamp: UNIX timestamp from where the database data should be collected
        timespan_seconds: number of seconds for which the data should be collected

    Returns:
        Dict: Dictionary with the query result.
    """
    return e3dc.get_db_data_timestamp(
        startTimestamp=start_timestamp,
        timespanSeconds=timespan_seconds,
        keepAlive=KEEP_ALIVE,
    )


def get_start_timestamp(date_time: datetime) -> int:
    """Get a start timestamp (seconds) from a datetime object.

    Arguments:
        date_time: Datetime object to be converted

    Returns:
        int: UNIX timestamp in seconds.
    """
    start_timestamp = int(time.mktime(date_time.timetuple()))
    # Due to unknown reasons the timestamp must be shifted by the delta of the
    # current and UTC a mix-up of UTC and the actual timezone
    start_timestamp += int(date_time.utcoffset().total_seconds())  # Offset between current and UTC timezone
    return start_timestamp


def merge_dictionaries(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries into a single.

    Arguments:
        dicts: Dictionaries to be merged.

    Returns:
        Dict: Merged dictionary.

    Raises:
        ValueError: If duplicate keys with difference values are tried to be merged.
    """
    merged = {}
    for d in dicts:
        for key, value in d.items():
            if key in merged:
                value_of_merged = merged[key]
                if value != value_of_merged:
                    raise ValueError(
                        f"Failed to merge dictionaries. "
                        f"Detected duplicate key '{key}' with different values: {
                  value} <-> {value_of_merged}"
                    )
            merged[key] = value
    return merged


def hours_to_seconds(hours: int) -> int:
    """Convert hours into seconds.

    Arguments:
        hours: Number of hours to be converted.

    Returns:
        int: Total seconds of the hours.
    """
    return hours * 60 * 60
