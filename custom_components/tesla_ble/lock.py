"""Lock entity for Tesla BLE integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VIN, DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator
from .entity import TeslaVehicleEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tesla BLE lock from a config entry."""
    coordinator: TeslaBLEDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    vin = entry.data[CONF_VIN]
    async_add_entities([TeslaBLELock(coordinator, vin)])


class TeslaBLELock(TeslaVehicleEntity, LockEntity):
    """Tesla BLE vehicle lock."""

    _attr_name = "Lock"
    _attr_translation_key = "lock"

    @property
    def is_locked(self) -> bool | None:
        """Return True if the vehicle is locked."""
        return self.coordinator.data.get("locked")

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the vehicle."""
        _LOGGER.debug("Locking Tesla vehicle %s", self.vin)
        command = self.coordinator.protocol.create_lock_command()
        await self.coordinator.async_send_command(command)

        # Optimistically update state
        self.coordinator.data["locked"] = True
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the vehicle."""
        _LOGGER.debug("Unlocking Tesla vehicle %s", self.vin)
        command = self.coordinator.protocol.create_unlock_command()
        await self.coordinator.async_send_command(command)

        # Optimistically update state
        self.coordinator.data["locked"] = False
        self.async_write_ha_state()
