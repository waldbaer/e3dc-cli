#!/usr/bin/env python3

# ---- Imports ----
from enum import Enum
from typing import Any, Dict, Optional

from lib.connection import E3DC

# ---- Constants & Types -----------------------------------------------------------------------------------------------

KEEP_ALIVE = True


# ---- Setter Logic -----------------------------------------------------------------------------------------------------


def SetPowerLimits(e3dc: E3DC, power_limits: Dict):
    e3dc_result = e3dc.set_power_limits(
        enable=power_limits.enable,
        max_charge=power_limits.max_charge,
        max_discharge=power_limits.max_discharge,
        discharge_start=power_limits.discharge_start,
        keepAlive=KEEP_ALIVE,
    )
    return BuildResultDict(ObjectToDictionary(power_limits), e3dc_result)


def SetPowerSave(e3dc: E3DC, powersave: bool):
    e3dc_result = e3dc.set_powersave(
        enable=powersave,
        keepAlive=KEEP_ALIVE,
    )
    return BuildResultDict({"enable": powersave}, e3dc_result)


def SetWeatherRegulatedCharge(e3dc: E3DC, weather_regulated_charge: bool):
    e3dc_result = e3dc.set_weather_regulated_charge(
        enable=weather_regulated_charge,
        keepAlive=KEEP_ALIVE,
    )
    return BuildResultDict({"enable": weather_regulated_charge}, e3dc_result)


# ---- Utilities -------------------------------------------------------------------------------------------------------


def ToHumanResult(result_code: int):
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


def ObjectToDictionary(obj: Any):
    # Convert object to dictionary representation
    obj_dictionary = vars(obj)
    # Filter non attributes
    result = {k: v for k, v in obj_dictionary.items() if v is not None}
    return result


def BuildResultDict(input_arguments: Dict, result_code):
    return {
        "input_parameters": input_arguments,
        "result": ToHumanResult(result_code),
        "result_code": result_code,
    }
