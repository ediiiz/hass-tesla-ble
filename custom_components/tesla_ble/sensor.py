"""Sensor platform for Tesla BLE integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VIN, DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator
from .entity import TeslaBLEEntity

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_range",
        name="Range",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="charger_power",
        name="Charging Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="charge_rate",
        name="Charging Rate",
        native_unit_of_measurement="mph",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tesla BLE sensors from a config entry."""
    coordinator: TeslaBLEDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    vin = config_entry.data[CONF_VIN]

    async_add_entities(
        TeslaBLESensor(coordinator, vin, description) for description in SENSOR_TYPES
    )


class TeslaBLESensor(TeslaBLEEntity, SensorEntity):
    """Implementation of a Tesla BLE sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: TeslaBLEDataUpdateCoordinator,
        vin: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        charge_state = self.coordinator.data.get("charge_state", {})
        return charge_state.get(self.entity_description.key)
