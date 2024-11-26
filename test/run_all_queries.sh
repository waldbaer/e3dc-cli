#!/bin/bash
set -e

# -- Execute --
echo "---- Query online help ---------------------------------------------------------------------"
./e3dc-cli.py --help
echo "---- Query online help ---------------------------------------------------------------------"

echo "---- Query live data -----------------------------------------------------------------------"
./e3dc-cli.py --query live live_system live_battery live_inverter
echo "--------------------------------------------------------------------------------------------"

echo "---- Query history data --------------------------------------------------------------------"
./e3dc-cli.py -q history_today history_yesterday history_week history_previous_week history_month history_previous_month history_year history_previous_year history_all
echo "---- Query history data --------------------------------------------------------------------"
