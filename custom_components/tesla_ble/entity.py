"""Base entity classes for Tesla BLE integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_TIMEOUT_SECONDS, DEFAULT_TIMEOUT_SECONDS, DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator


class TeslaVehicleEntity(CoordinatorEntity[TeslaBLEDataUpdateCoordinator]):
    """Base class for Tesla vehicle entities backed by the BLE coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeslaBLEDataUpdateCoordinator,
        vin: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._vin = vin
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vin)},
            manufacturer="Tesla",
            model="Vehicle",  # TODO: refine if/when we have model details
            name=f"Tesla {vin[-5:]}",
        )

    @property
    def vin(self) -> str:
        """Vehicle VIN."""
        return self._vin

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this entity."""
        if self.entity_description:
            return f"{self.vin}_{self.entity_description.key}"
        return f"{self.vin}_{self.__class__.__name__.lower()}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        last_seen = self.coordinator.data.get("last_seen")
        if last_seen is None:
            return False

        timeout = self.coordinator.entry.options.get(
            CONF_TIMEOUT_SECONDS, DEFAULT_TIMEOUT_SECONDS
        )

        return (dt_util.utcnow() - last_seen).total_seconds() < timeout


# Backwards-compatible alias (older code used TeslaBLEEntity).
TeslaBLEEntity = TeslaVehicleEntity
