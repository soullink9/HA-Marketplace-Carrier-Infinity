"""Diagnostics: the "Download diagnostics" file Home Assistant offers on the integration's page.

It holds the config entry and everything Carrier reports for each system, for attaching to a bug report. The
account's username (also the entry's title and unique id), its password and any token are replaced by REDACTED.
"""

from __future__ import annotations

from typing import Any

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from .coordinator import CarrierConfigEntry

# async_redact_data replaces the value of these keys at any depth, in dicts and in lists of dicts.
TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    "title",  # the entry's title is the username
    "unique_id",  # so is its unique id
    "access_token",
    "refresh_token",
    "id_token",
    "token",
}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: CarrierConfigEntry) -> dict[str, Any]:
    """The config entry and each system's data from Carrier, with the account details and secrets taken out."""
    coordinator = entry.runtime_data
    return async_redact_data(
        {
            "entry": entry.as_dict(),
            "last_update_success": coordinator.last_update_success,
            "systems": [system.as_dict() for system in (coordinator.data or {}).values()],
        },
        TO_REDACT,
    )
