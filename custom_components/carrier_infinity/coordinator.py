"""The coordinator: one per Carrier account. It owns the cloud connection and all the data.

Data flow:
- Every FULL_REFRESH (5 minutes) it loads every system on the account from Carrier's cloud.
- In between, Carrier's websocket pushes changes; carrier_api patches the loaded System objects in
  place and the coordinator tells the entities to redraw.
- When Home Assistant changes a setting, the entity records the value it wrote with `expect()`, and
  `shown()` serves that value for EXPECT_SECONDS, because the cloud keeps replaying the old one for a
  while after a change.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from time import monotonic
from typing import Any

from carrier_api import (
    ApiConnectionGraphql,
    CarrierApiAuthError,
    CarrierApiConnectionError,
    CarrierApiError,
    System,
    WebsocketDataUpdater,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, EXPECT_SECONDS, FULL_REFRESH, RECONNECT_FIRST, RECONNECT_MAX, RETRY_AFTER, RETRY_PAUSE

_LOGGER = logging.getLogger(__name__)

# A config entry whose runtime_data is our coordinator (set in __init__.async_setup_entry).
type CarrierConfigEntry = ConfigEntry[CarrierCoordinator]


# Keys whose values are secrets, wherever they appear in a log line (JSON, a Python dict, a query string).
_SECRET_KEYS = r"password|access_?token|refresh_?token|id_?token|token"
_SECRETS = (
    # "password": "..." in JSON, or 'password': '...' in a printed dict
    re.compile(rf"""(["']?(?:{_SECRET_KEYS})["']?\s*:\s*)("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')""", re.IGNORECASE),
    # ?Token=... in a URL (Carrier's websocket address carries the access token this way)
    re.compile(rf"([?&](?:{_SECRET_KEYS})=)([^&\s\"']+)", re.IGNORECASE),
    # Authorization: Bearer ...
    re.compile(r"(\bBearer\s+)([^\s\"',]+)", re.IGNORECASE),
)
REDACTED = "**REDACTED**"

# The loggers that can carry a secret: gql logs whole request and response bodies (the sign-in request holds the
# password, its reply the tokens), carrier_api logs the variables of each change, and an error from the websocket
# can quote its address, which holds the access token. A filter only sees records logged on its own logger, not
# on child loggers, so each one is listed.
_REDACTED_LOGGERS = (
    "gql.transport.aiohttp",
    "carrier_api.api_connection_graphql",
    "carrier_api.api_websocket",
    "carrier_api.api_websocket_data_updater",
    __name__,
)


def redact(text: str) -> str:
    """Return `text` with the value of every password and token in it replaced by REDACTED."""
    for pattern in _SECRETS:
        text = pattern.sub(lambda m: m[1] + REDACTED, text)
    return text


class _RedactSecrets(logging.Filter):
    """Blank out passwords and tokens in log lines, and keep the rest of the line.

    Works on the finished text (the message with its arguments filled in, and the traceback), so a secret is caught
    whichever argument, nested object or exception carries it.
    """

    carrier_infinity = True  # marks our filter, so it is added once even if this module is loaded again

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact the record in place; never drops it."""
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a broken log call: leave it for logging's own error report
            return True
        clean = redact(message)
        if clean != message:
            record.msg, record.args = clean, None
        if record.exc_info and not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        if record.exc_text:
            record.exc_text = redact(record.exc_text)
        return True


def install_log_redaction() -> None:
    """Add the redacting filter to every logger that can carry a secret, once (setup runs again on each reload)."""
    for name in _REDACTED_LOGGERS:
        logger = logging.getLogger(name)
        if not any(getattr(f, "carrier_infinity", False) for f in logger.filters):
            logger.addFilter(_RedactSecrets())


install_log_redaction()


class CarrierCoordinator(DataUpdateCoordinator[dict[str, System]]):
    """Loads every Carrier system on the account; data is {system serial: carrier_api System}."""

    def __init__(self, hass: HomeAssistant, entry: CarrierConfigEntry) -> None:
        """Create the cloud connection for this account (nothing is sent until the first refresh)."""
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=FULL_REFRESH)
        # Home Assistant's shared web session: carrier_api's requests and websocket use its connection pool, and
        # api.cleanup() leaves it open (Home Assistant closes it at shutdown).
        self.api = ApiConnectionGraphql(
            entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], client_session=async_get_clientsession(hass)
        )
        # Applies websocket messages to the System objects; given the systems after each full load.
        self.updater = WebsocketDataUpdater([])
        # (serial, zone id or None, field) -> (value we wrote, monotonic time it stops overriding).
        self._expected: dict[tuple, tuple[Any, float]] = {}

    # --- values just written by Home Assistant ----------------------------------------------------

    def expect(self, key: tuple, value: Any) -> None:
        """Remember a value Home Assistant just wrote, so it is shown instead of the cloud's stale one."""
        self._expected[key] = (value, monotonic() + EXPECT_SECONDS)

    def shown(self, key: tuple, actual: Any) -> Any:
        """Return the value to display: a recent write if there is one, otherwise what Carrier reports."""
        hit = self._expected.get(key)
        if hit is None or monotonic() > hit[1]:
            self._expected.pop(key, None)  # expired (or never set): the cloud is authoritative again
            return actual
        return hit[0]

    # --- full refresh ------------------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, System]:
        """Load everything from Carrier, riding out one connection blip and one expired session."""
        try:
            try:
                return await self._load()
            except (CarrierApiConnectionError, TimeoutError) as err:
                # Carrier's cloud drops the odd request (a reset connection, a timeout, a 5xx). The
                # query only reads, so wait a moment and ask once more before telling anyone.
                _LOGGER.debug("Carrier connection failed, trying again in %s s: %s", RETRY_PAUSE, err)
                await asyncio.sleep(RETRY_PAUSE)
                return await self._load()
        except CarrierApiAuthError as err:
            # The password itself is wrong now. Stop here (repeated sign-ins could lock the Carrier
            # account) and let Home Assistant ask for the new password (config_flow reauth step).
            raise ConfigEntryAuthFailed("Carrier rejected the saved password") from err
        except (CarrierApiConnectionError, TimeoutError) as err:
            # Still unreachable: entities go unavailable, and the next try comes in RETRY_AFTER seconds
            # rather than a whole FULL_REFRESH, so they are back soon after Carrier is.
            raise UpdateFailed(f"Carrier cloud error: {err}", retry_after=RETRY_AFTER) from err
        except (CarrierApiError, KeyError, ValueError) as err:
            # KeyError/ValueError: Carrier sent data carrier_api could not parse (for example a new
            # preset name). Entities go unavailable until a later refresh parses again.
            raise UpdateFailed(f"Carrier cloud error: {err}") from err

    async def _load(self) -> dict[str, System]:
        """One full load, signing in again with the password (once) if the saved session has expired."""
        if self.api.refresh_token is not None:
            try:
                return await self._fetch()
            except CarrierApiAuthError:
                # The saved session expired or was revoked: sign in again with the password, once.
                self.api.refresh_token = None
        return await self._fetch()

    async def _fetch(self) -> dict[str, System]:
        """One full load of every system (signs in first if needed; carrier_api handles that)."""
        systems = await self.api.load_data()
        self.updater.systems = systems
        return {system.profile.serial: system for system in systems}

    # --- websocket (pushed changes) ----------------------------------------------------------------

    async def _on_message(self, message: str) -> None:
        """Apply one websocket message to the loaded systems, then redraw the entities."""
        try:
            await self.updater.message_handler(message)  # patches the System objects in place
        except Exception:  # noqa: BLE001 - one bad message must never take down the socket
            # Type and size only: the body is the account's raw thermostat data.
            _LOGGER.debug(
                "Ignored websocket message (type %s, %d characters)",
                _message_type(message),
                len(message),
                exc_info=True,
            )
            return
        self.async_update_listeners()

    async def websocket_loop(self) -> None:
        """Keep Carrier's websocket open for as long as the integration is loaded.

        Runs as a config-entry background task, so Home Assistant cancels it on unload. While the
        socket keeps failing it backs off from RECONNECT_FIRST up to RECONNECT_MAX seconds.
        """
        socket = self.api.api_websocket  # created by carrier_api when it signed in (first refresh)
        socket.callback_add(self._on_message)
        delay = RECONNECT_FIRST
        while True:
            if isinstance(self.last_exception, ConfigEntryAuthFailed):
                await asyncio.sleep(RECONNECT_MAX)  # waiting for the user to enter the new password
                continue
            started = monotonic()
            try:
                await socket.listener()  # returns (or raises) when the connection closes
            except Exception as err:  # noqa: BLE001
                # Message only: a full traceback can contain the access token (it is in the URL).
                _LOGGER.debug("Carrier websocket dropped: %s: %s", type(err).__name__, err)
            if monotonic() - started > 300:
                delay = RECONNECT_FIRST  # it had been connected a while: reconnect promptly
            await asyncio.sleep(delay)
            delay = min(delay * 2, RECONNECT_MAX)


def _message_type(message: str) -> str:
    """A websocket message's type (messageType, or name for some), for the log; "unknown" if it has none."""
    try:
        data = json.loads(message)
    except ValueError:
        return "unknown (not JSON)"
    if not isinstance(data, dict):
        return "unknown"
    return str(data.get("messageType") or data.get("name") or "unknown")[:40]
