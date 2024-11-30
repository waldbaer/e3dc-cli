#!/usr/bin/env python3

# ---- Imports ----
from enum import Enum
from typing import Dict

# https://github.com/fsantini/python-e3dc
from e3dc import E3DC

# ---- Constants & Types -------------------------------------------------------------------------------------------------------


class ConnectionType(Enum):
    local = "local"
    web = "web"

    def __str__(self):
        return self.value


# ---- Connection with E3/DC system -----------------------------------------------------------------------------------


def SetupConnectionToE3DC(connection_config: Dict, e3dc_config: Dict):
    params = {
        "username": connection_config.user.get_secret_value(),
        "password": connection_config.password.get_secret_value(),
        # Extended E3/DC configuration
        "configuration": e3dc_config,
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
