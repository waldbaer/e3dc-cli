"""Interaction with E3/DC system."""

# ---- Imports ----
import time
from enum import Enum
from typing import Dict

# https://github.com/fsantini/python-e3dc
from e3dc import E3DC

# ---- Constants & Types -----------------------------------------------------------------------------------------------


class ConnectionType(Enum):
    """All possible connection types."""

    local = "local"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param
    web = "web"  # pylint: disable=invalid-name;reason=camel_case style wanted for cli param

    def __str__(self) -> str:
        """Convert enum into string representation.

        Returns:
            Str: String representation of the enum value.
        """
        return self.value


# ---- Connection with E3/DC system -----------------------------------------------------------------------------------


def setup_connection(connection_config: Dict, extended_config: Dict) -> E3DC:
    """Setup connection to the E3/DC system.

    Arguments:
        connection_config: Connection configuration parameters.
        extended_config: Extended connection configuration parameters.

    Returns:
        The created E3/DC library instance for interaction with the E3/DC system
    """
    params = {
        "username": connection_config.user.get_secret_value(),
        "password": connection_config.password.get_secret_value(),
        # Extended E3/DC configuration
        "configuration": extended_config,
        # IP address only needed for local connection
        "ipAddress": connection_config.address,
        # RSCP password only needed for local connection
        "key": (connection_config.rscp_password.get_secret_value() if connection_config.rscp_password else None),
        # Serialnumber only needed for web connection
        "serialNumber": (
            connection_config.serial_number.get_secret_value() if connection_config.serial_number else None
        ),
    }

    e3dc = E3DC(
        connectType=(
            E3DC.CONNECT_WEB if connection_config.type.name == ConnectionType.web.name else E3DC.CONNECT_LOCAL
        ),
        **params,
    )
    return e3dc


def close_connection(e3dc: E3DC) -> None:
    """Close connection to the E3/DC system.

    Arguments:
        e3dc: The E3/DC library instance for communication with the system.
    """
    e3dc.disconnect()


def wait_until_commands_applied(connection_config: Dict) -> None:
    """Wait until a command is applied on the E3/DC system.

    In case of local connections the execution of a set command might take some time on the E3/DC system to be applied.
    The immediate execution of a query command after a set command might not return the just modified system status.

    Therefore an artifical delay is introduced to ensure proper query results executed immediately after any set
    command.

    Arguments:
        connection_config: Connection configuration parameters.
    """
    if connection_config.type.name == ConnectionType.local.name:
        time.sleep(0.5)  # 500ms
