"""Switch platform for Tesla BLE integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VIN, DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator
from .entity import TeslaBLEEntity

SWITCH_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="climate_control",
        name="Climate Control",
        device_class=SwitchDeviceClass.SWITCH,
        icon="mdi:fan",
    ),
    SwitchEntityDescription(
        key="charging",
        name="Charging",
        device_class=SwitchDeviceClass.SWITCH,
        icon="mdi:ev-station",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tesla BLE switches from a config entry."""
    coordinator: TeslaBLEDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    vin = config_entry.data[CONF_VIN]

    async_add_entities(
        TeslaBLESwitch(coordinator, vin, description) for description in SWITCH_TYPES
    )


class TeslaBLESwitch(TeslaBLEEntity, SwitchEntity):
    """Implementation of a Tesla BLE switch."""

    entity_description: SwitchEntityDescription

    def __init__(
        self,
        coordinator: TeslaBLEDataUpdateCoordinator,
        vin: str,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.entity_description.key == "climate_control":
            climate_state = self.coordinator.data.get("climate_state", {})
            return climate_state.get("is_climate_on")

        if self.entity_description.key == "charging":
            charge_state = self.coordinator.data.get("charge_state", {})
            state = charge_state.get("charging_state")
            return state == "Charging"

        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if self.entity_description.key == "climate_control":
            cmd = self.coordinator.protocol.create_climate_command(on=True)
            await self.coordinator.async_send_command(cmd)
        elif self.entity_description.key == "charging":
            cmd = self.coordinator.protocol.create_charge_command(start=True)
            await self.coordinator.async_send_command(cmd)

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if self.entity_description.key == "climate_control":
            cmd = self.coordinator.protocol.create_climate_command(on=False)
            await self.coordinator.async_send_command(cmd)
        elif self.entity_description.key == "charging":
            cmd = self.coordinator.protocol.create_charge_command(start=False)
            await self.coordinator.async_send_command(cmd)

        await self.coordinator.async_request_refresh()
