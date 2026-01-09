[![PyPI version](https://badge.fury.io/py/e3dc-cli.svg)](https://badge.fury.io/py/e3dc-cli)
[![MIT License](https://img.shields.io/github/license/waldbaer/e3dc-cli?style=flat-square)](https://opensource.org/licenses/MIT)
[![GitHub issues open](https://img.shields.io/github/issues/waldbaer/e3dc-cli?style=flat-square)](https://github.com/waldbaer/e3dc-cli/issues)
[![GitHub Actions](https://github.com/waldbaer/e3dc-cli/actions/workflows/python-pdm.yml/badge.svg?branch=master)](https://github.com/waldbaer/e3dc-cli/actions/workflows/python-pdm.yml)


# Command line tool for querying E3/DC solar inverter systems

## Introduction
This command-line tool allows users to query live and historical data from E3/DC solar inverters and perform
configuration changes. It leverages the excellent [python-e3dc](https://github.com/fsantini/python-e3dc) library for
seamless integration with E3/DC systems.

Leveraging the powerful [jsonargparse](https://jsonargparse.readthedocs.io/) library, this tool supports configuration
and control via command-line parameters or a JSON configuration file.

## Features

* Live Data Queries
  * **Consumption and Production Data**: Retrieve real-time metrics on energy consumption and solar production.
  * **System Status**: Access overall system health and status information.
  * **Inverter Status**: Monitor the operational status of the solar inverter.
  * **Battery Status**: View current battery state, including charge level, temperatures, currents and further performance metrics.
  * **Wallbox Status**: Check the status of connected EV wallbox chargers.
* Historical Data Queries
  * Consumption and Production Data
  * Supported Time Ranges
    * **Day**: Current day and previous day
    * **Week**: Current week and previous week
    * **Month**: Current month and previous month
    * **Year**: Current year and previous year
    * **Total**: All-time historical data
* Modify Configuration
  * **Power Limits**: Set max. charge / discharge and lower charge / discharge limits
  * **Power Save**: Enable / Disable PowerSave mode of the inverter
  * **Weather Regulated Charge**: Enable / Disable usage of location-based weather forecast to improve usage of produced energy.

## Changelog
Changes can be followed at [CHANGELOG.md](https://github.com/waldbaer/e3dc-cli/blob/master/CHANGELOG.md).

## Requirements ##

 - [Python 3.10](https://www.python.org/)
 - [pip](https://pip.pypa.io/) or [pipx](https://pipx.pypa.io/stable/)

 For development:
 - [python-pdm (package dependency manager)](https://pdm-project.org/)

## Setup

### With pip / pipx
```
pip install e3dc-cli
pipx install e3dc-cli
```

### Setup directly from github repo / clone
```
git clone https://github.com/waldbaer/e3dc-cli.git
cd e3dc-cli

python -m venv .venv
source ./.venv/bin/activate
pip install .
```

## Usage

All parameters can be provided either as command-line arguments or through a JSON configuration file
(default: `config.json`). A combination of both methods is also supported.

A common approach is to define all credentials in the JSON configuration file, while specifying specific queries or set
operations as command-line arguments.
Alternatively, you can define all credentials via command-line parameters or include the executed queries and set
operations directly in the JSON configuration file.

The results of all executed queries and configuration modifications are returned as JSON output.
This output can be displayed directly in the terminal or saved to a JSON file.
It includes structured JSON hierarchies for each executed query and configuration modification.

The machine-readable JSON output format is designed for seamless integration with automation platforms, such as
[Node-RED](https://nodered.org/), which typically execute the `e3dc-cli` tool.

### Examples

#### Example 1: Pass Credentials via config.json, use local connection

Store all connection and credential parameters in JSON configuration file called `config.json`:
```
{
    "connection" : {
        "type" : "local",
        "address": "<IP or DNS address to the local E3/DC system>",
        "user": "<username>",
        "password": "<password>",
        "rscp_password": "<RSCP password>",
    }
}
```

Run some concrete queries and modify the PowerSave system configuration:
```
$> e3dc-cli --query live history_today --set_powersave true
{
  "query": {
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
      "pm0Production": 0.0,
      "pm1Production": 0.0,
      "startTimestamp": 1732491900,
      "stateOfCharge": 5.519999980926514,
      "solarProduction": 7800.0,
      "timespanSeconds": 86400
    }
  },
  "set": {
    "powersave": {
      "input_parameters": {
        "enable": true
      },
      "result": "success",
      "result_code": 0
    }
  }
}
```

#### Example 2: Pass all parameters via config.json, use web connection

Create `config.json` containing all parameters:
```
{
    "connection" : {
        "type" : "web",
        "user": "<username>",
        "password": "<password>",
        "serial_number": "<E3/DC system serial number>"
    },
    "query": ["live", "history_today"],
    "set": {
      "power_limits":{
        "enable": true,
        "max_charge": 3500,
        "max_discharge": 4500
      },
      "powersave": true
    }
}
```

Run tool without any further command line argument:
```
$> e3dc-cli
{
  "query": {
    "history_today": {
      "autarky": 38.567501068115234,
      "bat_power_in": 11955.5,
      "bat_power_out": 1715.0,
      "consumed_production": 67.32454681396484,
      "consumption": 17822.0,
      "grid_power_in": 3336.0,
      "grid_power_out": 10948.5,
      "pm0Production": 0.0,
      "pm1Production": 0.0,
      "solarProduction": 21632.0,
      "startTimestamp": 1733010300,
      "stateOfCharge": 99.18399810791016,
      "timespanSeconds": 86400
    },
    "live": {
      "autarky": 99.99994659423828,
      "consumption": {
        "battery": 0,
        "house": 241,
        "wallbox": 0
      },
      "production": {
        "add": 0,
        "grid": -154,
        "solar": 395
      },
      "selfConsumption": 61.367130279541016,
      "stateOfCharge": 100,
      "time": "2024-12-01 14:59:37.000891+00:00"
    }
  },
  "set": {
    "power_limits": {
      "input_parameters": {
        "discharge_start": null,
        "enable": true,
        "max_charge": 3500,
        "max_discharge": 4500
      },
      "result": "success",
      "result_code": 0
    },
    "powersave": {
      "input_parameters": {
        "enable": true
      },
      "result": "success",
      "result_code": 0
    }
  }
}
```


### Extended E3/DC configuration

Extended configuration settings (see [chapter 'configuration' of python-e3dc](https://github.com/fsantini/python-e3dc?tab=readme-ov-file#configuration)) can be passed via the `extended_config` parameters

```
{
    "connection" : { ... },
    "extended_config": {
      "pvis": [
        {
          "index": 0,
          "strings": 2,
          "phases": 3
        }
      ],
      "powermeters": [
        {
          "index": 6
        }
      ],
      "batteries": [
        {
          "index": 0,
          "dcbs": 2
        }
      ]
    },
    "query": [ ... ]
}
```

### All Available Parameters and Configuration Options
Details about all available options:
```
Usage: e3dc-cli [-h] [--version] [-c CONFIG] [-o OUTPUT] [--connection.type {local,web}] [--connection.address ADDRESS] [--connection.user USER]
                [--connection.password PASSWORD] [--connection.rscp_password RSCP_PASSWORD] [--connection.serial_number SERIAL_NUMBER]
                [-q [{static_system,live,live_system,live_powermeter,live_battery,live_inverter,live_wallbox,history_today,history_yesterday,history_week,history_previous_week,history_month,history_previous_month,history_year,history_previous_year,history_total} ...]]
                [--set.power_limits.enable {true,false}] [--set.power_limits.max_charge MAX_CHARGE]
                [--set.power_limits.max_discharge MAX_DISCHARGE] [--set.power_limits.discharge_start DISCHARGE_START]
                [--set.powersave {true,false}] [--set.weather_regulated_charge {true,false}]
                [--extended_config.powermeters { EXTENDED POWERMETERS CONFIG HIERARCHY }]
                [--extended_config.pvis { EXTENDED SOLAR INVERTERS CONFIG HIERARCHY }]
                [--extended_config.batteries { EXTENDED BATTERIES CONFIG HIERARCHY }]

Query E3/DC solar inverter systems | Version 1.0.5 | Copyright 2022-2026

Default Config File Locations:
  ['./config.json'], Note: default values below are the ones overridden by the contents of: ./config.json

Options:
  -h, --help            Show this help message and exit.
  --version             Print version and exit.
  -c, --config CONFIG   Path to JSON configuration file.

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

  -o, --output OUTPUT   Path of JSON output file. If not set JSON output is written to console / stdout (type: None, default: None)
  --connection.type {local,web}
                        Connection type used for communication with the E3/DC system

                        local  Use local RSCP connection (recommended)
                        web    Use web connection
                         (type: None, default: local)
  --connection.address ADDRESS
                        IP or DNS address of the E3/DC system.
                        Only relevant for connection type 'local'.
                         (type: None, default: None)
  --connection.user USER
                        Username (similar to the E3/DC portal) (type: None, default: None)
  --connection.password PASSWORD
                        Password (similar to the E3/DC portal) (type: None, default: None)
  --connection.rscp_password RSCP_PASSWORD
                        RSCP password. Set on the device via Main Page -> Personalize -> User profile -> RSCP password.
                        Only relevant for connection type 'local',
                         (type: None, default: None)
  --connection.serial_number SERIAL_NUMBER
                        Serial number of the system (see 'SN' in E3/DC portal).
                        Only relevant for connection type 'web'.
                         (type: None, default: None)
  -q, --query [{static_system,live,live_system,live_powermeter,live_battery,live_inverter,live_wallbox,history_today,history_yesterday,history_week,history_previous_week,history_month,history_previous_month,history_year,history_previous_year,history_total} ...]
                        Perform one or multiple live status or history queries:

                        Static System Infos:
                        - static_system             Static system info (Model, Software Version, Installed PeakPower / BatteryCapacity, ...)

                        Real-Time Status Queries:
                        - live                      Condensed status information (consumption, production, SoC, autarky, ...)
                        - live_system               General system status and power settings
                        - live_powermeter           Power meter status (power, energy and voltage of L1-L3, ...)
                        - live_battery              Battery status (SoC, temperatures, capacity, charge cycles, ...)
                        - live_inverter             Solar inverter status (input strings status, output phases, temperatures)
                        - live_wallbox              EV wallbox status (SoC, consumption, max. charge current, ...)

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
                         (type: None, default: None)
  --set.power_limits.enable {true,false}
                        true: enable manual SmartPower limits. false: Use automatic mode.
                        Automatically set to 'true' if not explicitly set and any other manual limit
                        (max_charge, max_discharge or discharge_start) is set.
                         (type: None, default: None)
  --set.power_limits.max_charge MAX_CHARGE
                        SmartPower maximum charging power. Unit: Watt.
                        Automatically set to the systems max. battery charge power limit if not explicitly set.
                        Only relevant if set.power_limits.enable is 'true' or not explicitly configured.
                         (type: None, default: None)
  --set.power_limits.max_discharge MAX_DISCHARGE
                        SmartPower maximum discharging power. Unit: Watt.
                        Automatically set to the systems max. battery discharge power limit if not explicitly set.
                        Only relevant if set.power_limits.enable is 'true' or not explicitly configured.
                         (type: None, default: None)
  --set.power_limits.discharge_start DISCHARGE_START
                        SmartPower lower charge / discharge threshold. Unit: Watt.
                        Automatically set to the systems discharge default threshold if not explicitly set.
                        Only relevant if set.power_limits.enable is 'true' or not explicitly configured.
                         (type: None, default: None)
  --set.powersave {true,false}
                        Enable / Disable PowerSave of the inverter (inverter switches to standby mode when not in use). (type: None, default: None)
  --set.weather_regulated_charge {true,false}
                        Enabled / Disable optimized charging based on the weather forecast. (type: None, default: None)
  --extended_config.powermeters, --extended_config.powermeters+ { EXTENDED POWERMETERS CONFIG HIERARCHY }
                        Extended power meters configuration.
                        For details see https://python-e3dc.readthedocs.io/en/latest/#configuration (type: None, default: None)
  --extended_config.pvis, --extended_config.pvis+ { EXTENDED SOLAR INVERTERS CONFIG HIERARCHY }
                        Extended solar inverters configuration.
                        For details see https://python-e3dc.readthedocs.io/en/latest/#configuration (type: None, default: None)
  --extended_config.batteries, --extended_config.batteries+ { EXTENDED BATTERIES CONFIG HIERARCHY }
                        Extended batteries configuration.
                        For details see https://python-e3dc.readthedocs.io/en/latest/#configuration (type: None, default: None)
```

## Development

### Setup environment

```
pdm install --dev
```

### Update dependencies to latest versions

```
pdm update --unconstrained --save-exact --no-sync
```


### Format / Linter / Tests

```
# Check code style
pdm run format

# Check linter
pdm run lint

# Run tests
pdm run tests
```

### Publish

```
# API token will be requested interactively as password
pdm publish -u __token__

# or to test.pypi.org
pdm publish --repository testpypi -u __token__
```

## Acknowledgments
Special thanks to [python-e3dc](https://github.com/fsantini/python-e3dc) for providing the core library that powers this tool.
