"""DataUpdateCoordinator for Tesla BLE integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble_client import TeslaHABLEClient
from .core.proto import universal_message_pb2, vcsec_pb2
from .core.protocol import TeslaProtocol
from .core.session_manager import TeslaSessionManager

_LOGGER = logging.getLogger(__name__)


class TeslaBLEDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Tesla BLE data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TeslaHABLEClient,
        session_manager: TeslaSessionManager,
        address: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Tesla BLE Vehicle",
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self.session_manager = session_manager
        self.protocol = TeslaProtocol(session_manager)
        self.address = address
        self.data = {
            "locked": None,
            "charge_state": {},
            "climate_state": {},
            "closures_state": {},
        }

        # Register notification callback
        # We cannot await here in __init__, so we do it in _async_update_data
        # self.client.register_notification_callback(self._handle_notification)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the vehicle."""
        if not self.client.is_connected:
            _LOGGER.debug("Connecting to Tesla vehicle at %s", self.address)
            if not await self.client.connect(self.address):
                raise UpdateFailed(
                    f"Failed to connect to Tesla vehicle at {self.address}"
                )

        # Always ensure notifications are registered for this coordinator instance.
        # This handles both fresh connections and existing connections passed from
        # config flow.
        try:
            await self.client.register_notification_callback(self._handle_notification)
        except Exception as e:
            _LOGGER.debug("Notification callback not registered: %s", e)

        # Ensure we have authenticated sessions
        for domain in [
            universal_message_pb2.DOMAIN_VEHICLE_SECURITY,
            universal_message_pb2.DOMAIN_INFOTAINMENT,
        ]:
            if not self.session_manager.is_authenticated(domain):
                _LOGGER.debug("Authenticating domain %s", domain)
                try:
                    # Send SessionInfoRequest
                    request_msg = self.session_manager.prepare_session_info_request(
                        domain
                    )
                    data = self.protocol._encode_ble_message(request_msg)
                    await self.client.write_characteristic(data)
                except Exception as err:
                    _LOGGER.error(
                        "Failed to start handshake for domain %s: %s", domain, err
                    )

        # Poll for status if authenticated
        try:
            if self.session_manager.is_authenticated(
                universal_message_pb2.DOMAIN_VEHICLE_SECURITY
            ):
                _LOGGER.debug("Polling VCSEC status")
                poll_msg = self.protocol.create_vcsec_status_poll()
                await self.client.write_characteristic(poll_msg)

            if self.session_manager.is_authenticated(
                universal_message_pb2.DOMAIN_INFOTAINMENT
            ):
                _LOGGER.debug("Polling Infotainment status")
                poll_msg = self.protocol.create_infotainment_poll()
                await self.client.write_characteristic(poll_msg)
        except Exception as err:
            _LOGGER.warning("Error polling vehicle: %s", err)

        return self.data

    def _handle_notification(self, data: bytes) -> None:
        """Handle incoming BLE notifications."""
        parsed = self.protocol.parse_ble_notification(data)

        if "error" in parsed:
            _LOGGER.debug("Notification error: %s", parsed["error"])
            return

        domain = parsed.get("domain")
        msg_type = parsed.get("msg_type")
        payload = parsed.get("payload")

        if payload is None:
            return

        _LOGGER.debug("Received notification: domain=%s, type=%s", domain, msg_type)

        if domain == universal_message_pb2.DOMAIN_VEHICLE_SECURITY:
            if msg_type == "vehicleStatus":
                status: vcsec_pb2.VehicleStatus = payload.vehicleStatus
                # Update lock state
                self.data["locked"] = (
                    status.vehicleLockState
                    == vcsec_pb2.VehicleLockState_E.VEHICLELOCKSTATE_LOCKED
                )
                _LOGGER.debug("Updated lock state: %s", self.data["locked"])
                self.async_set_updated_data(self.data)

        elif domain == universal_message_pb2.DOMAIN_INFOTAINMENT:
            if msg_type == "vehicleData":
                vd = payload.vehicleData
                if vd.HasField("chargeState"):
                    cs = vd.chargeState
                    self.data["charge_state"] = {
                        "battery_level": cs.battery_level
                        if cs.HasField("optional_battery_level")
                        else None,
                        "charging_state": cs.charging_state.WhichOneof("type")
                        if cs.HasField("charging_state")
                        else None,
                        "battery_range": cs.est_battery_range
                        if cs.HasField("optional_est_battery_range")
                        else None,
                        "charger_power": cs.charger_power
                        if cs.HasField("optional_charger_power")
                        else None,
                        "charge_rate": cs.charge_rate_mph
                        if cs.HasField("optional_charge_rate_mph")
                        else None,
                        "charge_port_door_open": cs.charge_port_door_open
                        if cs.HasField("optional_charge_port_door_open")
                        else None,
                    }
                if vd.HasField("climateState"):
                    cls = vd.climateState
                    self.data["climate_state"] = {
                        "is_climate_on": cls.is_climate_on
                        if cls.HasField("optional_is_climate_on")
                        else None,
                    }
                if vd.HasField("closuresState"):
                    clss = vd.closuresState
                    self.data["closures_state"] = {
                        "front_trunk": clss.door_open_trunk_front
                        if clss.HasField("optional_door_open_trunk_front")
                        else None,
                        "rear_trunk": clss.door_open_trunk_rear
                        if clss.HasField("optional_door_open_trunk_rear")
                        else None,
                    }
                self.async_set_updated_data(self.data)

    async def async_send_command(self, command_bytes: bytes) -> None:
        """Send a command to the vehicle."""
        if not self.client.is_connected:
            if not await self.client.connect(self.address):
                _LOGGER.error("Failed to connect to send command")
                return

        await self.client.write_characteristic(command_bytes)
