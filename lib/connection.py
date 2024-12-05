#!/usr/bin/env python3

# ---- Imports ----
from enum import Enum
from typing import Dict

# https://github.com/fsantini/python-e3dc
from e3dc import E3DC

import time


# ---- Constants & Types -------------------------------------------------------------------------------------------------------


class ConnectionType(Enum):
    local = "local"
    web = "web"

    def __str__(self):
        return self.value


# ---- Connection with E3/DC system -----------------------------------------------------------------------------------


def SetupConnectionToE3DC(connection_config: Dict, extended_config: Dict):
    params = {
        "username": connection_config.user.get_secret_value(),
        "password": connection_config.password.get_secret_value(),
        # Extended E3/DC configuration
        "configuration": extended_config,
        # IP address only needed for local connection
        "ipAddress": connection_config.address,
        # RSCP password only needed for local connection
        "key": (
            connection_config.rscp_password.get_secret_value()
            if connection_config.rscp_password
            else None
        ),
        # Serialnumber only needed for web connection
        "serialNumber": (
            connection_config.serial_number.get_secret_value()
            if connection_config.serial_number
            else None
        ),
    }

    e3dc = E3DC(
        connectType=(
            E3DC.CONNECT_WEB
            if connection_config.type.name == ConnectionType.web.name
            else E3DC.CONNECT_LOCAL
        ),
        **params,
    )
    return e3dc


def CloseConnectionToE3DC(e3dc: E3DC):
    e3dc.disconnect()


def WaitUntilCommandsApplied(e3dc: E3DC, connection_config: Dict):
    """
    In case of local connections the execution of a set command might take some time on the E3/DC system to be applied.
    The immediate execution of a query command after a set command might not return the just modified system status.

    Therefore an artifical delay is introduced to ensure proper query results executed immediately after any set command.
    """
    if connection_config.type.name == ConnectionType.local.name:
        time.sleep(0.5)  # 500ms
