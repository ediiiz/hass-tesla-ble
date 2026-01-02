"""Binary sensor platform for Tesla BLE integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VIN, DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator
from .entity import TeslaBLEEntity

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="charging_active",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    BinarySensorEntityDescription(
        key="rear_trunk",
        name="Rear Trunk",
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    BinarySensorEntityDescription(
        key="front_trunk",
        name="Front Trunk",
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    BinarySensorEntityDescription(
        key="charge_port_door_open",
        name="Charge Port",
        device_class=BinarySensorDeviceClass.DOOR,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tesla BLE binary sensors from a config entry."""
    coordinator: TeslaBLEDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    vin = config_entry.data[CONF_VIN]

    async_add_entities(
        TeslaBLEBinarySensor(coordinator, vin, description)
        for description in BINARY_SENSOR_TYPES
    )


class TeslaBLEBinarySensor(TeslaBLEEntity, BinarySensorEntity):
    """Implementation of a Tesla BLE binary sensor."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: TeslaBLEDataUpdateCoordinator,
        vin: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.entity_description.key == "charging_active":
            charge_state = self.coordinator.data.get("charge_state", {})
            state = charge_state.get("charging_state")
            # See vehicle.proto: Charging = 5
            return state == "Charging"

        if self.entity_description.key in ["rear_trunk", "front_trunk"]:
            closures = self.coordinator.data.get("closures_state", {})
            return closures.get(self.entity_description.key)

        if self.entity_description.key == "charge_port_door_open":
            charge_state = self.coordinator.data.get("charge_state", {})
            return charge_state.get("charge_port_door_open")

        return None
