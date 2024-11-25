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

current_timezone = get_localzone()

class QueryType(Enum):
    live = 'live',
    live_system = 'live_system'
    live_battery = 'live_battery'
    live_inverter = 'live_inverter'
    history_day = 'history_day'
    history_yesterday = 'history_yesterday'
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
                           # History queries
                           QueryType.history_day.name, QueryType.history_yesterday.name,
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

  # ---- History Queries ----
  elif query == QueryType.history_day.name:
    e3dc_data = RunHistoryQueryDay(e3dc, days=0)
  elif query == QueryType.history_yesterday.name:
    e3dc_data = RunHistoryQueryDay(e3dc, days=1)

  elif query == QueryType.history_month.name:
    e3dc_data = RunHistoryQueryMonth(e3dc, months=0)
  elif query == QueryType.history_previous_month.name:
    e3dc_data = RunHistoryQueryMonth(e3dc, months=1)

  elif query == QueryType.history_year.name:
    e3dc_data = RunHistoryQueryYear(e3dc, years=0)
  elif query == QueryType.history_previous_year.name:
    e3dc_data = RunHistoryQueryYear(e3dc, years=1)

  elif query == QueryType.history_all.name:
    e3dc_data = RunHistoryQueryAll(e3dc)

  else:
    print("Error: Unknown/unsupported query type '" + query + "'")

  return e3dc_data

# ---- History Queries -------------------------------------------------------------------------------------------------
def RunHistoryQueryDay(e3dc, days=0):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    requestDate -= datetime.timedelta(days=days)

    # Workaround for https://github.com/fsantini/python-e3dc/issues/67
    # Due to unknown reason the E3DC portal provide the summarized values shifted by 15min.
    # Example: Day history is summarizing all 15min slots starting 23:45 the day before until current day 23:45 (Similar as CSV export data)
    requestDate -= datetime.timedelta(minutes=15)

    startTimestamp = int(time.mktime(requestDate.timetuple()))
    # Due to unknown reasons the timestamp must be shifted by the delta of the current and UTC a mix-up of UTC and the actual timezone
    startTimestamp += int(requestDate.utcoffset().total_seconds()) # Offset between current and UTC timezone
    timespanSeconds = HoursToSeconds(24)
    return e3dc.get_db_data_timestamp(startTimestamp=startTimestamp, timespanSeconds=timespanSeconds, keepAlive=True)

def RunHistoryQueryMonth(e3dc, months=0):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    requestDate -= relativedelta(months=(months + 1))

    # Attention: 15min time-shift issue seems to be not present of month-wise query!
    # https://github.com/fsantini/python-e3dc/issues/67

    startTimestamp = int(time.mktime(requestDate.timetuple()))
    # Due to unknown reasons the timestamp must be shifted by the delta of the current and UTC a mix-up of UTC and the actual timezone
    startTimestamp += int(requestDate.utcoffset().total_seconds()) # Offset between current and UTC timezone

    num_days = monthrange(requestDate.year, requestDate.month)[1]
    timespanSeconds = HoursToSeconds(num_days * 24) # days of month -> sec
    return e3dc.get_db_data_timestamp(startTimestamp=startTimestamp, timespanSeconds=timespanSeconds, keepAlive=True)

def RunHistoryQueryYear(e3dc, years=0):
    requestDate = datetime.datetime.now(tz=current_timezone).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    requestDate -= relativedelta(years=years)

    # Attention: 15min time-shift issue seems to be not present of year-wise query!
    # https://github.com/fsantini/python-e3dc/issues/67

    startTimestamp = int(time.mktime(requestDate.timetuple()))
    # Due to unknown reasons the timestamp must be shifted by the delta of the current and UTC a mix-up of UTC and the actual timezone
    startTimestamp += int(requestDate.utcoffset().total_seconds()) # Offset between current and UTC timezone

    timespanSeconds = HoursToSeconds(365 * 24) # 365 days -> sec
    return e3dc.get_db_data_timestamp(startTimestamp=startTimestamp, timespanSeconds=timespanSeconds, keepAlive=True)

def RunHistoryQueryAll(e3dc):
    # Start query from 1970-01-02, avoid issues with timezones near to epoch 0.
    requestDate = datetime.datetime.now(tz=current_timezone).replace(year=1970, month=1, day=2, hour=0, minute=0, second=1, microsecond=0)

    startTimestamp = int(time.mktime(requestDate.timetuple()))
    # Due to unknown reasons the timestamp must be shifted by the delta of the current and UTC a mix-up of UTC and the actual timezone
    startTimestamp += int(requestDate.utcoffset().total_seconds()) # Offset between current and UTC timezone

    now = datetime.datetime.now(tz=current_timezone)
    timeDeltaSinceRequestData = now - requestDate
    timespanSeconds = int(timeDeltaSinceRequestData.total_seconds())
    e3dc_data = e3dc.get_db_data_timestamp(startTimestamp=startTimestamp, timespanSeconds=timespanSeconds, keepAlive=True)


# ---- Utilities -------------------------------------------------------------------------------------------------------
def HoursToSeconds(hours):
  return hours * 60 * 60;

# ---- Entrypoint ------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  try:
    main()
  except SystemExit:
    sys.exit(1)
  except BaseException:
    print("ERROR: Any error has occured! Traceback:\r\n" + traceback.format_exc())
    sys.exit(1)
  sys.exit(0)
