[![MIT License](https://img.shields.io/github/license/waldbaer/e3dc-cli?style=flat-square)](https://opensource.org/licenses/MIT)
[![GitHub issues open](https://img.shields.io/github/issues/waldbaer/e3dc-cli?style=flat-square)](https://github.com/waldbaer/e3dc-cli/issues)


# Command-line tool to query E3/DC systems

Query live and history data from E3/DC systems (solar inverter)
using the famous [python-e3dc](https://github.com/fsantini/python-e3dc) library.

## Requirements ##

 - [Python 3.8](https://www.python.org/)
 - [virtualenv](https://virtualenv.readthedocs.org)
 - [pip (package manager)](https://pip.pypa.io/)
 - [pye3dc](https://github.com/fsantini/python-e3dc)
 - [tzlocal](https://github.com/regebro/tzlocal)
 - [jsonargparse](https://github.com/omni-us/jsonargparse/)
 - [pydantic](https://github.com/pydantic/pydantic)

All dependencies are defined and installed via [requirements.txt](requirements.txt).


## Setup
```
# Setup python virtualenv
python3 -m venv venv
source ./venv/bin/activate
# or
./setup-venv.h
source ./venv/bin/activate
```

## Key features ##
- Query live status (system, batteries, inverter, ...)
- Query historical data (day, month, ...)
- Multiple queries
- Machine-readble JSON output

## Usage

For details about the command line arguments please refer to the online help.

```
./e3dc-cli.py --help
```

### Example output
```
$> ./e3dc-cli.py --query live history_day
{
  "live": {
    "autarky": 0.0,
    "consumption": {
      "battery": 0,
      "house": 729,
      "wallbox": 0
    },
    "production": {
      "solar": 0,
      "add": 0,
      "grid": 729
    },
    "selfConsumption": 99.99994659423828,
    "stateOfCharge": 0,
    "time": "2024-11-25 19:14:14.000460+00:00"
  },
  "history_day": {
    "autarky": 44.49199295043945,
    "bat_power_in": 4990.0,
    "bat_power_out": 4710.5,
    "consumed_production": 95.58944702148438,
    "consumption": 14370.0,
    "grid_power_in": 295.0,
    "grid_power_out": 7976.5,
    "startTimestamp": 1732491900,
    "stateOfCharge": 5.519999980926514,
    "solarProduction": 7800.0,
    "timespanSeconds": 86400
  }
}
```
