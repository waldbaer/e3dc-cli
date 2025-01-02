"""Test for __main__.

Docs: https://pythontest.com/testing-argparse-apps/
"""

import pytest

from e3dc_cli.connection import ConnectionType
from e3dc_cli.query import QueryType, merge_dictionaries, run_query
from tests.util_runner import run_cli, run_cli_stdout

# ---- Fixtures --------------------------------------------------------------------------------------------------------
JSON_KEY_QUERY = "query"


# ---- Component Tests -------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query_type,number_of_expected_json_keys",
    [
        # --- Static Queries ----
        (QueryType.static_system, 12),
        # --- Live Queries ----
        (QueryType.live, 6),
        (QueryType.live_system, 26),
        (QueryType.live_powermeter, 8),
        (QueryType.live_battery, 31),
        (QueryType.live_inverter, 19),
        (QueryType.live_wallbox, 18),
        # ---- History Queries ----
        (QueryType.history_today, 11),
        (QueryType.history_yesterday, 11),
        (QueryType.history_week, 11),
        (QueryType.history_previous_week, 11),
        (QueryType.history_month, 11),
        (QueryType.history_previous_month, 11),
        (QueryType.history_year, 11),
        (QueryType.history_previous_year, 11),
        (QueryType.history_total, 11),
    ],
)
def test_ct_single_query(
    query_type: QueryType,
    number_of_expected_json_keys: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the --query option for a single query type.

    Arguments:
        query_type: Concrete single query type
        number_of_expected_json_keys: Number of JSON keys expected for the query type.
        capsys: System capture
    """
    query_type = str(query_type)
    json_output = run_cli_stdout(f"--query {query_type}", capsys)

    assert JSON_KEY_QUERY in json_output
    json_query = json_output[JSON_KEY_QUERY]

    assert query_type in json_query
    json_query_type = json_query[query_type]

    assert len(json_query_type) == number_of_expected_json_keys


@pytest.mark.parametrize("connection_type", [ConnectionType.local, ConnectionType.web])
def test_ct_multi_query(connection_type: ConnectionType, capsys: pytest.CaptureFixture[str]) -> None:
    """Test the --query option for multiple queries.

    Arguments:
        connection_type: Used connection type.
        capsys: System capture
    """
    all_query_types = [str(query_type) for query_type in QueryType]
    connection_type = str(connection_type)

    json_output = run_cli_stdout(f"--connection.type {connection_type} --query {' '.join(all_query_types)}", capsys)

    assert JSON_KEY_QUERY in json_output
    json_query = json_output[JSON_KEY_QUERY]

    for query_type in QueryType:
        assert str(query_type) in json_query


def test_ct_unknown_query(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the --query option with an unknown query type.

    Arguments:
        capsys: System capture
    """
    query_type = "UNKNOWN_QUERY_TYPE"

    with pytest.raises(SystemExit) as sys_exit_info:
        run_cli(f"--query {query_type}", capsys)

    output = capsys.readouterr().out.rstrip()
    assert output == ""
    assert sys_exit_info.value.code > 0


# ---- Unit Tests ------------------------------------------------------------------------------------------------------


def test_ut_unknown_query_type() -> None:
    """Test query with unknown query type."""

    class InvalidQueryConfig:
        """Test query config object with invalid query type."""

        name = "UNKNOWN_QUERY"

    with pytest.raises(SystemError) as exception_info:
        run_query(None, InvalidQueryConfig)

    assert f"Unknown/unsupported query type '{InvalidQueryConfig.name}'" in str(exception_info.value)


def test_ut_merging_dicts() -> None:
    """Test merging of dictionaries with conflicting keys (different values)."""
    dict1 = {"noconflict": 23, "conflict": True}
    dict2 = {"noconflict": 23, "conflict": False}

    with pytest.raises(ValueError) as exception_info:
        merge_dictionaries(dict1, dict2)

    assert "Detected duplicate key 'conflict'" in str(exception_info.value)
