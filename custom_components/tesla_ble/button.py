"""Button platform for Tesla BLE integration."""

from __future__ import annotations

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VIN, DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator
from .entity import TeslaBLEEntity

BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="open_trunk",
        name="Open Trunk",
        icon="mdi:car-back",
    ),
    ButtonEntityDescription(
        key="open_frunk",
        name="Open Frunk",
        icon="mdi:car-front",
    ),
    ButtonEntityDescription(
        key="open_charge_port",
        name="Open Charge Port",
        icon="mdi:ev-station",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tesla BLE buttons from a config entry."""
    coordinator: TeslaBLEDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    vin = config_entry.data[CONF_VIN]

    async_add_entities(
        TeslaBLEButton(coordinator, vin, description) for description in BUTTON_TYPES
    )


class TeslaBLEButton(TeslaBLEEntity, ButtonEntity):
    """Implementation of a Tesla BLE button."""

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator: TeslaBLEDataUpdateCoordinator,
        vin: str,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.entity_description.key == "open_trunk":
            cmd = self.coordinator.protocol.create_open_trunk_command()
            await self.coordinator.async_send_command(cmd)
        elif self.entity_description.key == "open_frunk":
            cmd = self.coordinator.protocol.create_open_frunk_command()
            await self.coordinator.async_send_command(cmd)
        elif self.entity_description.key == "open_charge_port":
            cmd = self.coordinator.protocol.create_charge_port_door_open_command()
            await self.coordinator.async_send_command(cmd)

        await self.coordinator.async_request_refresh()
