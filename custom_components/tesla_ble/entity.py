"""Base entity for Tesla BLE integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator


class TeslaBLEEntity(CoordinatorEntity[TeslaBLEDataUpdateCoordinator]):
    """Base class for Tesla BLE entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeslaBLEDataUpdateCoordinator,
        vin: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.vin = vin
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vin)},
            manufacturer="Tesla",
            model="Vehicle",  # We could refine this if we had more info
            name=f"Tesla {vin[-5:]}",
        )

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this entity."""
        if self.entity_description:
            return f"{self.vin}_{self.entity_description.key}"
        return f"{self.vin}_{self.__class__.__name__.lower()}"
