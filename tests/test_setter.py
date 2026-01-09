"""Test of setter commands."""

import pytest

from e3dc_cli import setter
from e3dc_cli.connection import ConnectionType
from e3dc_cli.query import QueryType
from tests.util_runner import run_cli_json

# ---- Constants & Utils -----------------------------------------------------------------------------------------------
JSON_KEY_QUERY = "query"
JSON_KEY_SET = "set"
JSON_KEY_SET_INPUT_PARAMS = "input_parameters"
JSON_KEY_SET_RESULT = "result"
JSON_KEY_SET_RESULT_CODE = "result_code"

RESULT_SUCCESS = "success"
RESULT_CODE_SUCCESS = 0
RESULT_FAILURE = "fail"
RESULT_CODE_FAILURE = -1


def build_power_limits_args(enable: bool, max_charge: int, max_discharge: int) -> str:
    """Build power_limits cli args.

    Arguments:
        enable: Value for --set.power_limits.enable
        max_charge: --set.power_limits.max_charge
        max_discharge: --set.power_limits.max_discharge

    Returns:
        str: Command line arguments string.
    """
    args = ""
    if enable is not None:
        args += f" --set.power_limits.enable {enable}"
    if max_charge is not None:
        args += f" --set.power_limits.max_charge {max_charge}"
    if max_discharge is not None:
        args += f" --set.power_limits.max_discharge {max_discharge}"
    return args


# ---- Component Tests -------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "setter_type,query_type,json_query_key,result,result_code",
    [
        ("powersave", QueryType.live_system, "powerSaveEnabled", RESULT_SUCCESS, 0),
        (
            "weather_regulated_charge",
            QueryType.live_system,
            "weatherRegulatedChargeEnabled",
            # Failure caused by incorrect handling E3/DC library handling.
            # see https://github.com/fsantini/python-e3dc/issues/73
            # see https://github.com/fsantini/python-e3dc/pull/74
            RESULT_FAILURE,
            -1,
        ),
    ],
)
@pytest.mark.parametrize("connection_type", [ConnectionType.local, ConnectionType.web])
def test_ct_setter_boolean(
    setter_type: str,
    query_type: QueryType,
    json_query_key: str,
    result: str,
    result_code: int,
    connection_type: ConnectionType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the --set.powersave setter command.

    Arguments:
        setter_type: Setter type to be tested (boolean types only!)
        query_type: Query type containing status of modified setter
        json_query_key: Key of the JSON query result reflecting the modified setter.
        result: Expected human-readable result
        result_code: Expected result code
        connection_type: Used connection type.
        capsys: System capture
    """
    # Initial query of state for later revert
    status_query = f"--connection.type {connection_type} --query live_system "
    initial_query = run_cli_json(status_query, capsys).stdout_as_json
    initial_state = initial_query[JSON_KEY_QUERY][str(query_type)][json_query_key]
    assert isinstance(initial_state, bool)

    # Toggle boolean state
    output_set_and_query = run_cli_json(
        f"{status_query} --set.{setter_type} {not initial_state}", capsys
    ).stdout_as_json
    set_result = output_set_and_query[JSON_KEY_SET][setter_type]
    assert set_result[JSON_KEY_SET_INPUT_PARAMS]["enable"] == (not initial_state)
    assert set_result[JSON_KEY_SET_RESULT] == RESULT_SUCCESS
    assert set_result[JSON_KEY_SET_RESULT_CODE] == RESULT_CODE_SUCCESS

    updated_state = output_set_and_query[JSON_KEY_QUERY][str(query_type)][json_query_key]
    assert updated_state is not initial_state

    # Revert back to initial state
    output_revert_and_query = run_cli_json(f"{status_query} --set.{setter_type} {initial_state}", capsys).stdout_as_json
    set_result = output_revert_and_query[JSON_KEY_SET][setter_type]
    assert set_result[JSON_KEY_SET_INPUT_PARAMS]["enable"] == initial_state
    assert set_result[JSON_KEY_SET_RESULT] == result
    assert set_result[JSON_KEY_SET_RESULT_CODE] == result_code

    reverted_state = output_revert_and_query[JSON_KEY_QUERY][str(query_type)][json_query_key]
    assert reverted_state == initial_state


@pytest.mark.parametrize(
    "enable,expected_enable,max_charge,max_discharge",
    [
        (True, True, -100, -200),
        (
            None,  # Test missing enable parameter
            True,  # enable param not set but implicitly enabled as max_charge / max_discharge is set
            -200,
            -300,
        ),
    ],
)
def test_ct_setter_power_limits(
    enable: bool | None,
    expected_enable: bool,
    max_charge: int,
    max_discharge: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the set.power_limits setter command.

    Arguments:
        enable: Optional value for --set.power_limits.enable
        expected_enable: Expected executed enable setting (auto-derived from other params).
        max_charge: --set.power_limits.max_charge
        max_discharge: --set.power_limits.max_discharge
        capsys: System capture
    """
    status_query = "--query live_system "
    status_query_json_key = "live_system"
    status_query_json_key_used = "powerLimitsUsed"
    status_query_json_key_max_charge = "maxChargePower"
    status_query_json_key_max_discharge = "maxDischargePower"

    # Initial query of states for later revert
    initial_state = run_cli_json(status_query, capsys).stdout_as_json[JSON_KEY_QUERY][status_query_json_key]
    assert isinstance(initial_state[status_query_json_key_used], bool)

    new_max_charge = initial_state[status_query_json_key_max_charge] + max_charge
    new_max_discharge = initial_state[status_query_json_key_max_discharge] + max_discharge

    # Modify configured powerlimits
    power_limits_args = build_power_limits_args(enable, new_max_charge, new_max_discharge)

    modified_state = run_cli_json(status_query + power_limits_args, capsys).stdout_as_json
    set_result = modified_state[JSON_KEY_SET]["power_limits"]
    assert set_result[JSON_KEY_SET_INPUT_PARAMS]["enable"] == expected_enable
    assert set_result[JSON_KEY_SET_INPUT_PARAMS]["max_charge"] == new_max_charge
    assert set_result[JSON_KEY_SET_INPUT_PARAMS]["max_discharge"] == new_max_discharge
    assert set_result[JSON_KEY_SET_RESULT] == RESULT_SUCCESS
    assert set_result[JSON_KEY_SET_RESULT_CODE] == RESULT_CODE_SUCCESS

    modified_state_query = modified_state[JSON_KEY_QUERY][status_query_json_key]
    assert modified_state_query[status_query_json_key_used] == expected_enable
    assert modified_state_query[status_query_json_key_max_charge] == new_max_charge
    assert modified_state_query[status_query_json_key_max_discharge] == new_max_discharge

    # Revert back to initial powerlimits setting
    power_limits_args = build_power_limits_args(
        initial_state[status_query_json_key_used],
        initial_state[status_query_json_key_max_charge],
        initial_state[status_query_json_key_max_discharge],
    )

    modified_state = run_cli_json(status_query + power_limits_args, capsys).stdout_as_json[JSON_KEY_QUERY][
        status_query_json_key
    ]
    assert modified_state[status_query_json_key_used] == initial_state[status_query_json_key_used]
    assert modified_state[status_query_json_key_max_charge] == initial_state[status_query_json_key_max_charge]
    assert modified_state[status_query_json_key_max_discharge] == initial_state[status_query_json_key_max_discharge]


# ---- Unit Tests ------------------------------------------------------------------------------------------------------
def test_ut_setter_to_human_result() -> None:
    """Test to_human_result() API."""
    assert setter._to_human_result(0) == "success"
    assert setter._to_human_result(1) == "one value is nonoptimal"
    assert setter._to_human_result(-1) == "fail"
    assert setter._to_human_result(2) == "unknown"
    assert setter._to_human_result(255) == "unknown"
