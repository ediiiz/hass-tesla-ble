"""The Tesla BLE integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .ble_client import TeslaHABLEClient
from .const import CONF_PRIVATE_KEY, CONF_PUBLIC_KEY, DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator
from .core.session_manager import TeslaSessionManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.LOCK,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tesla BLE from a config entry."""
    address = entry.data[CONF_ADDRESS]
    public_key = bytes.fromhex(entry.data[CONF_PUBLIC_KEY])
    private_key = bytes.fromhex(entry.data[CONF_PRIVATE_KEY])

    # Initialize core components
    session_manager = TeslaSessionManager(
        private_key_bytes=private_key,
        public_key_bytes=public_key,
    )
    client = TeslaHABLEClient(hass)

    # Initialize coordinator
    coordinator = TeslaBLEDataUpdateCoordinator(
        hass,
        client,
        session_manager,
        address,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: TeslaBLEDataUpdateCoordinator = hass.data[DOMAIN].pop(
            entry.entry_id
        )
        # Disconnect client
        await coordinator.client.disconnect()

    return unload_ok
