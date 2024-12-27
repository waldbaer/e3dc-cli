"""Setter command implementation."""

# ---- Imports ----
from typing import Any, Dict

from .connection import E3DC

# ---- Constants & Types -----------------------------------------------------------------------------------------------

KEEP_ALIVE = True


# ---- Setter Logic ----------------------------------------------------------------------------------------------------


def set_power_limits(e3dc: E3DC, power_limits: Dict) -> None:
    """Set power limits.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        power_limits: The power limits to be set.
    """
    e3dc_result = e3dc.set_power_limits(
        enable=power_limits.enable,
        max_charge=power_limits.max_charge,
        max_discharge=power_limits.max_discharge,
        discharge_start=power_limits.discharge_start,
        keepAlive=KEEP_ALIVE,
    )
    return build_result_dict(object_to_dictionary(power_limits), e3dc_result)


def set_power_save(e3dc: E3DC, powersave: bool) -> None:
    """Enable/Disable the powersave option.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        powersave: New state of the powersave configuration.
    """
    e3dc_result = e3dc.set_powersave(
        enable=powersave,
        keepAlive=KEEP_ALIVE,
    )
    return build_result_dict({"enable": powersave}, e3dc_result)


def set_weather_regulated_charge(e3dc: E3DC, weather_regulated_charge: bool) -> None:
    """Enable/Disable weather regulated charging option.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
        weather_regulated_charge: New state of the weather regulated charging option.
    """
    e3dc_result = e3dc.set_weather_regulated_charge(
        enable=weather_regulated_charge,
        keepAlive=KEEP_ALIVE,
    )
    return build_result_dict({"enable": weather_regulated_charge}, e3dc_result)


# ---- Utilities -------------------------------------------------------------------------------------------------------


def to_human_result(result_code: int) -> str:
    """Convert integer result code to human-readable result.

    Arguments:
        result_code: Integer result code from E3/DC library.

    Returns:
        str: Human-readable representation of the result.
    """
    human_result = "n/a"
    if result_code == 0:
        human_result = "success"
    elif result_code == 1:
        human_result = "one value is nonoptimal"
    elif result_code == -1:
        human_result = "fail"
    else:
        human_result = "unknown"
    return human_result


def object_to_dictionary(obj: Any) -> Dict:  # noqa: ANN401
    """Generic conversion of python objects to dictionaries.

    Arguments:
        obj: Python object to be converted.

    Returns:
        Dict: Dictionary representation of the object.
    """
    # Convert object to dictionary representation
    obj_dictionary = vars(obj)
    # Filter non attributes
    result = {k: v for k, v in obj_dictionary.items() if v is not None}
    return result


def build_result_dict(input_arguments: Dict, result_code: int) -> Dict:
    """Assemble a dictionary of a single setter command result.

    Arguments:
        input_arguments: Input arguments used for the setter command.
        result_code: Integer representation of the result.

    Returns:
        Dict: Dictionary with input parameters and result in integer / human-readable representation.#
    """
    return {
        "input_parameters": input_arguments,
        "result": to_human_result(result_code),
        "result_code": result_code,
    }
