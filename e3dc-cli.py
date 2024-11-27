#!/usr/bin/env python3

# ---- Imports ----
import sys
import traceback
from typing import Any, List, Dict

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
__version__ = '1.0.0'

DAYS_IN_A_WEEK = 7
HOURS_IN_A_DAY = 24
DAYS_IN_A_YEAR = 365

current_timezone = get_localzone()

class QueryType(Enum):
    live = 'live',
    live_system = 'live_system'
    live_battery = 'live_battery'
    live_inverter = 'live_inverter'
    live_wallbox = 'live_wallbox'
    history_today = 'history_today'
    history_yesterday = 'history_yesterday'
    history_week = 'history_week'
    history_previous_week = 'history_previous_week'
    history_month = 'history_month'
    history_previous_month = 'history_previous_month'
    history_year = 'history_year'
    history_previous_year = 'history_previous_year'
    history_all = 'history_all'

    def __str__(self):
        return self.value

def main():
  args = ParseConfig()
  e3dc = SetupConnectionToE3DC(args.connection, args.e3dc_config)

  # Query requested data
  collected_data = {}
  for query in args.query:
    e3dc_data = RunSingleQuery(e3dc, query)

    if e3dc_data is not None:
      collected_data[query] = e3dc_data

  # Finaly output as JSON
  print(json.dumps(collected_data, indent = 2, default=str))

def ParseConfig():
  argparser = ArgumentParser(prog="e3dc-cli.py",
                             description=f"Query E3/DC systems | Version {__version__} | {__copyright__}",
                             env_prefix="E3DC_CLI",
                             default_config_files=['./config.json'],
                             version=__version__)

  argparser.add_argument('-c', '--config', action="config", help="Configuration file")
  argparser.add_argument('--connection.address', type=str, help="IP or DNS address of the E3/DC system")
  argparser.add_argument('--connection.user', type=SecretStr, help="Username (similar to the E3/DC portal)")
  argparser.add_argument('--connection.password', type=SecretStr, help="Password (similar to the E3/DC portal)")
  argparser.add_argument('--connection.rscp_password', type=SecretStr, help="RSCP password (set on the device via Main Page -> Personalize -> User profile -> RSCP password")
  argparser.add_argument('--e3dc_config.powermeters', type=List[Dict[str, Any]])
  argparser.add_argument('--e3dc_config.pvis', type=List[Dict[str, Any]])
  argparser.add_argument('--e3dc_config.batteries', type=List[Dict[str, Any]])

  argparser.add_argument('-q', '--query', nargs='+', default=[QueryType.live],
                         choices=[
                           # Live queries
                           QueryType.live.name, QueryType.live_system.name, QueryType.live_battery.name, QueryType.live_inverter.name,
                           QueryType.live_wallbox.name,
                           # History queries
                           QueryType.history_today.name, QueryType.history_yesterday.name,
                           QueryType.history_week.name, QueryType.history_previous_week.name,
                           QueryType.history_month.name, QueryType.history_previous_month.name,
                           QueryType.history_year.name, QueryType.history_previous_year.name,
                           QueryType.history_all.name
                         ])
  args = argparser.parse_args()
  return args

def SetupConnectionToE3DC(connection_config, e3dc_config):
  # CONFIG = {"powermeters": [{"index": 6}]}
  e3dc = E3DC(E3DC.CONNECT_LOCAL,
              ipAddress=connection_config.address,
              username=connection_config.user.get_secret_value(),
              password=connection_config.password.get_secret_value(),
              key=connection_config.rscp_password.get_secret_value(),
              configuration=e3dc_config)
  return e3dc

def RunSingleQuery(e3dc, query):
  e3dc_data = None

  # ---- Live Queries ----
  if query == QueryType.live.name:
    e3dc_data = e3dc.poll(keepAlive=True)
  elif query == QueryType.live_system.name:
    e3dc_data = e3dc.get_system_status(keepAlive=True)
  elif query == QueryType.live_battery.name:
    e3dc_data = e3dc.get_battery_data(keepAlive=True)
  elif query == QueryType.live_inverter.name:
    e3dc_data = e3dc.get_pvi_data(keepAlive=True)
  elif query == QueryType.live_wallbox.name:
    e3dc_data = e3dc.get_wallbox_data(keepAlive=True)

  # ---- History Queries ----
  elif query == QueryType.history_today.name:
    e3dc_data = RunHistoryQueryDay(e3dc, past_days_from_now=0)
  elif query == QueryType.history_yesterday.name:
    e3dc_data = RunHistoryQueryDay(e3dc, past_days_from_now=1)

  elif query == QueryType.history_week.name:
    e3dc_data = RunHistoryQueryWeek(e3dc, past_weeks_from_now=0)
  elif query == QueryType.history_previous_week.name:
    e3dc_data = RunHistoryQueryWeek(e3dc, past_weeks_from_now=1)

  elif query == QueryType.history_month.name:
    e3dc_data = RunHistoryQueryMonth(e3dc, past_months_from_now=0)
  elif query == QueryType.history_previous_month.name:
    e3dc_data = RunHistoryQueryMonth(e3dc, past_months_from_now=1)

  elif query == QueryType.history_year.name:
    e3dc_data = RunHistoryQueryYear(e3dc, past_years_from_now=0)
  elif query == QueryType.history_previous_year.name:
    e3dc_data = RunHistoryQueryYear(e3dc, past_years_from_now=1)

  elif query == QueryType.history_all.name:
    e3dc_data = RunHistoryQueryAll(e3dc)

  else:
    raise SystemExit(f"Unknown/unsupported query type '{query}'")

  return e3dc_data

# ---- History Queries -------------------------------------------------------------------------------------------------

def RunHistoryQueryDay(e3dc, past_days_from_now):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    requestDate -= datetime.timedelta(days=past_days_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67
    # Due to unknown reason the E3DC portal provide the summarized values shifted by 15min.
    # This matches the "granularity" of 15min time slots used for accumulation (similar to CSV export data).
    # Example: Day history is summarizing all 15min slots starting 23:45 the day before until current day 23:45.
    requestDate -= datetime.timedelta(minutes=15)

    return QueryHistoryDatabase(e3dc,
                                startTimestamp=GetStartTimestamp(requestDate),
                                timespanSeconds=HoursToSeconds(HOURS_IN_A_DAY))


def RunHistoryQueryWeek(e3dc, past_weeks_from_now):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    requestDate -= datetime.timedelta(days=requestDate.weekday()) # subtract number of days since monday
    requestDate -= datetime.timedelta(days=DAYS_IN_A_WEEK * past_weeks_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67
    # Due to unknown reason the E3DC portal provide the summarized values shifted by 1h.
    # This matches the "granularity" of 1h time slots used for accumulation (similar to CSV export data).
    # Example: week history is summarizing all 1h time slots starting 0:00 first day of the week until last day of the week 23:00.
    requestDate -= datetime.timedelta(hours=1)

    return QueryHistoryDatabase(e3dc,
                                startTimestamp=GetStartTimestamp(requestDate),
                                timespanSeconds=HoursToSeconds(DAYS_IN_A_WEEK * HOURS_IN_A_DAY))


def RunHistoryQueryMonth(e3dc, past_months_from_now=0):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    requestDate -= relativedelta(months=past_months_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67 is not necessary for month-based query

    days_in_select_month = monthrange(requestDate.year, requestDate.month)[1]
    return QueryHistoryDatabase(e3dc,
                                startTimestamp=GetStartTimestamp(requestDate),
                                timespanSeconds=HoursToSeconds(days_in_select_month * HOURS_IN_A_DAY))


def RunHistoryQueryYear(e3dc, past_years_from_now=0):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    requestDate -= relativedelta(years=past_years_from_now)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67 is not necessary for year-based query
    return QueryHistoryDatabase(e3dc,
                                startTimestamp=GetStartTimestamp(requestDate),
                                timespanSeconds=HoursToSeconds(DAYS_IN_A_YEAR * HOURS_IN_A_DAY))


def RunHistoryQueryAll(e3dc):
    now = datetime.datetime.now(tz=current_timezone)
    # Start query from 1970-01-02, avoid issues with timezones near to epoch 0.
    requestDate = now.replace(year=1970, month=1, day=2, hour=0, minute=0, second=1, microsecond=0)

    timeDeltaSinceRequestData = now - requestDate
    timespanSeconds = int(timeDeltaSinceRequestData.total_seconds())

    return QueryHistoryDatabase(e3dc,
                                startTimestamp=GetStartTimestamp(requestDate),
                                timespanSeconds=timespanSeconds)


# ---- Utilities -------------------------------------------------------------------------------------------------------
def QueryHistoryDatabase(e3dc, startTimestamp, timespanSeconds):
  return e3dc.get_db_data_timestamp(startTimestamp=startTimestamp, timespanSeconds=timespanSeconds, keepAlive=True)

def HoursToSeconds(hours):
  return hours * 60 * 60;

def GetStartTimestamp(datetime):
  startTimestamp = int(time.mktime(datetime.timetuple()))
  # Due to unknown reasons the timestamp must be shifted by the delta of the current and UTC a mix-up of UTC and the actual timezone
  startTimestamp += int(datetime.utcoffset().total_seconds()) # Offset between current and UTC timezone
  return startTimestamp


# ---- Entrypoint ------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  try:
    main()
  except SystemExit as exception:
    if(exception.code != 0):
      print(f"ERROR: {exception}")
    sys.exit(exception.code)
  except BaseException:
    print(f"ERROR: Any error has occured! Traceback:\r\n{traceback.format_exc()}")
    sys.exit(1)
  sys.exit(0)
