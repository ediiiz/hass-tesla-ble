"""Sensor platform for Tesla BLE integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VIN, DOMAIN
from .coordinator import TeslaBLEDataUpdateCoordinator
from .entity import TeslaVehicleEntity


def _normalize_connection_source(raw: Any) -> str:
    """Normalize HA bluetooth 'source' values into stable sensor options."""
    if raw is None:
        return "unknown"
    value = str(raw).lower()
    # HA commonly uses values like "local" or "remote" (proxy), but we keep it tolerant.
    if "local" in value:
        return "local"
    if "remote" in value or "proxy" in value:
        return "remote"
    return "unknown"


@dataclass(frozen=True, kw_only=True)
class TeslaBLESensorDescription(SensorEntityDescription):
    """Sensor description with a coordinator-backed value getter."""

    value_fn: Callable[[TeslaBLEDataUpdateCoordinator], Any]


SENSOR_TYPES: tuple[TeslaBLESensorDescription, ...] = (
    TeslaBLESensorDescription(
        key="battery_level",
        name="Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.get("charge_state", {}).get("battery_level"),
    ),
    TeslaBLESensorDescription(
        key="battery_range",
        name="Range",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.get("charge_state", {}).get("battery_range"),
    ),
    TeslaBLESensorDescription(
        key="charger_power",
        name="Charging Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.get("charge_state", {}).get("charger_power"),
    ),
    TeslaBLESensorDescription(
        key="charge_rate",
        name="Charging Rate",
        native_unit_of_measurement="mph",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.get("charge_state", {}).get("charge_rate"),
    ),
    # Diagnostics
    TeslaBLESensorDescription(
        key="connected",
        name="Connection",
        device_class=SensorDeviceClass.ENUM,
        options=["connected", "disconnected"],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: "connected" if c.data.get("connected") else "disconnected",
    ),
    TeslaBLESensorDescription(
        key="rssi",
        name="RSSI",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.data.get("rssi"),
    ),
    TeslaBLESensorDescription(
        key="last_seen",
        name="Last Seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.data.get("last_seen"),
    ),
    TeslaBLESensorDescription(
        key="connection_source",
        name="Connection Source",
        device_class=SensorDeviceClass.ENUM,
        options=["local", "remote", "unknown"],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _normalize_connection_source(
            c.data.get("connection_source")
        ),
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


class TeslaBLESensor(TeslaVehicleEntity, SensorEntity):
    """Implementation of a Tesla BLE sensor."""

    entity_description: TeslaBLESensorDescription

    def __init__(
        self,
        coordinator: TeslaBLEDataUpdateCoordinator,
        vin: str,
        description: TeslaBLESensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    @property
    def native_value(self) -> float | int | str | datetime | None:
        """Return the state of the sensor."""
        value = self.entity_description.value_fn(self.coordinator)
        if value is None or isinstance(value, (float, int, str, datetime)):
            return value
        return str(value)
