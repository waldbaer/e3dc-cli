"""Test of query commands."""

import os
import re
from typing import Optional

import pytest
from pytest_mock.plugin import MockerFixture

from e3dc_cli.connection import ConnectionType
from e3dc_cli.query import QueryType, run_query
from tests.util_runner import run_cli, run_cli_json

# ---- Constants -------------------------------------------------------------------------------------------------------
JSON_KEY_QUERY = "query"
JSON_KEYS_HISTORY_QUERY = [
    "autarky",
    "bat_power_in",
    "bat_power_out",
    "consumed_production",
    "consumption",
    "grid_power_in",
    "grid_power_out",
    "pm0Production",
    "pm1Production",
    "solarProduction",
    "startTimestamp",
    "stateOfCharge",
    "timespanSeconds",
]

# ---- Component Tests -------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query_type,expected_json_keys",
    [
        # --- Static Queries ----
        (
            QueryType.static_system,
            [
                "deratePercent",
                "deratePower",
                "externalSourceAvailable",
                "installedBatteryCapacity",
                "installedPeakPower",
                "macAddress",
                "maxAcPower",
                "maxBatChargePower",
                "maxBatDischargePower",
                "model",
                "release",
                "serial",
            ],
        ),
        # --- Live Queries ----
        (QueryType.live, ["autarky", "consumption", "production", "selfConsumption", "stateOfCharge", "time"]),
        (
            QueryType.live_system,
            [
                "acModeBlocked",
                "batteryModuleAlive",
                "chargeIdlePeriodActive",
                "dcdcAlive",
                "dischargeIdlePeriodActive",
                "dischargeStartPower",
                "emergencyPowerOverride",
                "emergencyPowerStarted",
                "emergencyReserveReached",
                "emsAlive",
                "maxChargePower",
                "maxDischargePower",
                "powerLimitsUsed",
                "powerMeterAlive",
                "powerSaveEnabled",
                "pvDerated",
                "pvInverterInited",
                "pvModuleAlive",
                "rescueBatteryEnabled",
                "serverConnectionAlive",
                "socSyncRequested",
                "sysConfChecked",
                "waitForWeatherBreakthrough",
                "wallBoxAlive",
                "weatherForecastMode",
                "weatherRegulatedChargeEnabled",
            ],
        ),
        (
            QueryType.live_powermeter,
            [
                "activePhases",
                "energy",
                "index",
                "maxPhasePower",
                "mode",
                "power",
                "type",
                "voltage",
            ],
        ),
        (
            QueryType.live_battery,
            [
                "asoc",
                "chargeCycles",
                "current",
                "dcbCount",
                "dcbs",
                "designCapacity",
                "deviceConnected",
                "deviceInService",
                "deviceName",
                "deviceWorking",
                "eodVoltage",
                "errorCode",
                "fcc",
                "index",
                "maxBatVoltage",
                "maxChargeCurrent",
                "maxDcbCellTemp",
                "maxDischargeCurrent",
                "minDcbCellTemp",
                "moduleVoltage",
                "rc",
                "readyForShutdown",
                "rsoc",
                "rsocReal",
                "statusCode",
                "terminalVoltage",
                "totalDischargeTime",
                "totalUseTime",
                "trainingMode",
                "usuableCapacity",
                "usuableRemainingCapacity",
            ],
        ),
        (
            QueryType.live_inverter,
            [
                "acMaxApparentPower",
                "cosPhi",
                "deviceState",
                "frequency",
                "index",
                "lastError",
                "maxPhaseCount",
                "maxStringCount",
                "onGrid",
                "phases",
                "powerMode",
                "serialNumber",
                "state",
                "strings",
                "systemMode",
                "temperature",
                "type",
                "version",
                "voltageMonitoring",
            ],
        ),
        (
            QueryType.live_wallbox,
            [
                "appSoftware",
                "batteryToCar",
                "chargingActive",
                "chargingCanceled",
                "consumptionNet",
                "consumptionSun",
                "energyAll",
                "energyNet",
                "energySun",
                "index",
                "keyState",
                "maxChargeCurrent",
                "phases",
                "plugLocked",
                "plugged",
                "schukoOn",
                "soc",
                "sunModeOn",
            ],
        ),
        # ---- History Queries ----
        (QueryType.history_today, JSON_KEYS_HISTORY_QUERY),
        (QueryType.history_yesterday, JSON_KEYS_HISTORY_QUERY),
        (QueryType.history_week, JSON_KEYS_HISTORY_QUERY),
        (QueryType.history_previous_week, JSON_KEYS_HISTORY_QUERY),
        (QueryType.history_month, JSON_KEYS_HISTORY_QUERY),
        (QueryType.history_previous_month, JSON_KEYS_HISTORY_QUERY),
        (QueryType.history_year, JSON_KEYS_HISTORY_QUERY),
        (QueryType.history_previous_year, JSON_KEYS_HISTORY_QUERY),
        (QueryType.history_total, JSON_KEYS_HISTORY_QUERY),
    ],
)
def test_ct_query_single(
    query_type: QueryType,
    expected_json_keys: list,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the --query option for a single query type.

    Arguments:
        query_type: Concrete single query type
        expected_json_keys: The list of expected query-specific JSON keys.
        capsys: System capture
    """
    query_type = str(query_type)
    json_output = run_cli_json(f"--query {query_type}", capsys).stdout_as_json

    assert JSON_KEY_QUERY in json_output
    json_query = json_output[JSON_KEY_QUERY]

    assert query_type in json_query
    json_query_type = json_query[query_type]

    for expected_json_key in expected_json_keys:
        assert expected_json_key in json_query_type
    assert len(expected_json_keys) == len(json_query_type)


@pytest.mark.parametrize("connection_type", [ConnectionType.local, ConnectionType.web])
@pytest.mark.parametrize("output_file", [None, "e3dc_cli_test.json"])
def test_ct_query_multi(
    connection_type: ConnectionType, output_file: Optional[str], tmp_path: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test the --query option for multiple queries.

    Arguments:
        connection_type: Used connection type.
        output_file: JSON output file name. If not set JSON output is written to console / stdout.
        tmp_path: Temporary unique file path provided by built-in fixture.
        capsys: System capture
    """
    all_query_types = [str(query_type) for query_type in QueryType]
    connection_type = str(connection_type)

    cli_args = f"--connection.type {connection_type} --query {' '.join(all_query_types)}"

    if output_file is None:
        json_output = run_cli_json(cli_args, capsys).stdout_as_json
    else:
        output_file = f"{tmp_path}/{output_file}"
        cli_args += f" --output {output_file}"
        json_output = run_cli_json(cli_args, capsys, output_file).fileout_as_json

    assert JSON_KEY_QUERY in json_output
    json_query = json_output[JSON_KEY_QUERY]

    for query_type in QueryType:
        assert str(query_type) in json_query


# ---- Unit Tests ------------------------------------------------------------------------------------------------------


def test_ut_query_type_unknown() -> None:
    """Test query with unknown query type."""

    class InvalidQueryConfig:
        """Test query config object with invalid query type."""

        name = "UNKNOWN_QUERY"

    with pytest.raises(ValueError) as exception_info:
        run_query(None, InvalidQueryConfig)

    assert f"Unknown/unsupported query type '{InvalidQueryConfig.name}'" in str(exception_info.value)


def test_ct_query_merge_dictionaries_conflict(mocker: MockerFixture, capsys: pytest.CaptureFixture[str]) -> None:
    """Test merging of dictionaries with conflicting keys (different values) in 'live_system' query.

    Arguments:
        mocker: Pytest mocker fixture.
        capsys: System capture
    """
    get_system_status_mock = mocker.patch("e3dc.E3DC.get_system_status")
    get_system_status_mock.return_value = {"noconflict": 23, "conflict": True}

    get_power_settings_mock = mocker.patch("e3dc.E3DC.get_power_settings")
    get_power_settings_mock.return_value = {"noconflict": 23, "conflict": False}

    cli_result = run_cli("--query live_system", capsys)
    assert cli_result.exit_code != os.EX_OK
    assert re.search(r".*Failed to merge dictionaries.*duplicate key 'conflict'", cli_result.stdout)
