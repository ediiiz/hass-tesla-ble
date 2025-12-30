from __future__ import annotations

import logging
import struct
from typing import TYPE_CHECKING, Any

from .proto import ( # type: ignore
    car_server_pb2,
    universal_message_pb2,
    vcsec_pb2,
)

if TYPE_CHECKING:
    from .session_manager import TeslaSessionManager

_LOGGER = logging.getLogger(__name__)


class TeslaProtocol:
    """High-level protocol layer for building and parsing Tesla messages."""

    def __init__(self, session_manager: TeslaSessionManager) -> None:
        """Initialize the protocol handler.

        Args:
            session_manager: The session manager for secure wrapping/unwrapping.
        """
        self._session_manager = session_manager

    # --- VCSEC COMMANDS (DOMAIN_VEHICLE_SECURITY) ---

    def create_wake_command(self) -> bytes:
        """Create a command to wake the vehicle."""
        return self._create_vcsec_rke_action(vcsec_pb2.RKE_ACTION_WAKE_VEHICLE)

    def create_unlock_command(self) -> bytes:
        """Create a command to unlock the vehicle."""
        return self._create_vcsec_rke_action(vcsec_pb2.RKE_ACTION_UNLOCK)

    def create_lock_command(self) -> bytes:
        """Create a command to lock the vehicle."""
        return self._create_vcsec_rke_action(vcsec_pb2.RKE_ACTION_LOCK)

    def create_open_trunk_command(self) -> bytes:
        """Create a command to open the rear trunk."""
        return self._create_vcsec_closure_move(
            rearTrunk=vcsec_pb2.CLOSURE_MOVE_TYPE_OPEN
        )

    def create_close_trunk_command(self) -> bytes:
        """Create a command to close the rear trunk."""
        return self._create_vcsec_closure_move(
            rearTrunk=vcsec_pb2.CLOSURE_MOVE_TYPE_CLOSE
        )

    def create_open_frunk_command(self) -> bytes:
        """Create a command to open the front trunk (frunk)."""
        return self._create_vcsec_closure_move(
            frontTrunk=vcsec_pb2.CLOSURE_MOVE_TYPE_OPEN
        )

    def create_charge_port_door_open_command(self) -> bytes:
        """Create a command to open the charge port door (VCSEC)."""
        return self._create_vcsec_closure_move(
            chargePort=vcsec_pb2.CLOSURE_MOVE_TYPE_OPEN
        )

    def create_charge_port_door_close_command(self) -> bytes:
        """Create a command to close the charge port door (VCSEC)."""
        return self._create_vcsec_closure_move(
            chargePort=vcsec_pb2.CLOSURE_MOVE_TYPE_CLOSE
        )

    def create_vcsec_status_poll(self) -> bytes:
        """Create a request for vehicle security status."""
        unsigned_msg = vcsec_pb2.UnsignedMessage()
        unsigned_msg.InformationRequest.informationRequestType = (
            vcsec_pb2.INFORMATION_REQUEST_TYPE_GET_STATUS
        )
        return self._wrap_vcsec_unsigned_message(unsigned_msg)

    # --- CAR SERVER COMMANDS (DOMAIN_INFOTAINMENT) ---

    def create_infotainment_poll(self) -> bytes:
        """Create a request for infotainment data (charge state)."""
        action = car_server_pb2.Action()
        action.vehicleAction.getVehicleData.getChargeState.SetInParent()
        return self._wrap_car_server_action(action)

    def create_climate_command(self, on: bool) -> bytes:
        """Create a command to turn climate on or off."""
        action = car_server_pb2.Action()
        action.vehicleAction.hvacAutoAction.power_on = on
        return self._wrap_car_server_action(action)

    def create_charge_command(self, start: bool) -> bytes:
        """Create a command to start or stop charging."""
        action = car_server_pb2.Action()
        if start:
            action.vehicleAction.chargingStartStopAction.start.SetInParent()
        else:
            action.vehicleAction.chargingStartStopAction.stop.SetInParent()
        return self._wrap_car_server_action(action)

    def create_charge_limit_command(self, percent: int) -> bytes:
        """Create a command to set the charge limit."""
        action = car_server_pb2.Action()
        action.vehicleAction.chargingSetLimitAction.percent = percent
        return self._wrap_car_server_action(action)

    def create_charge_amps_command(self, amps: int) -> bytes:
        """Create a command to set the charging current."""
        action = car_server_pb2.Action()
        action.vehicleAction.setChargingAmpsAction.charging_amps = amps
        return self._wrap_car_server_action(action)

    # --- PRIVATE HELPERS FOR MESSAGE CONSTRUCTION ---

    def _create_vcsec_rke_action(self, rke_action: int) -> bytes:
        """Helper to create a VCSEC RKE action message."""
        unsigned_msg = vcsec_pb2.UnsignedMessage()
        unsigned_msg.RKEAction = rke_action
        return self._wrap_vcsec_unsigned_message(unsigned_msg)

    def _create_vcsec_closure_move(self, **kwargs: int) -> bytes:
        """Helper to create a VCSEC closure move request."""
        unsigned_msg = vcsec_pb2.UnsignedMessage()
        for field, value in kwargs.items():
            setattr(unsigned_msg.closureMoveRequest, field, value)
        return self._wrap_vcsec_unsigned_message(unsigned_msg)

    def _wrap_vcsec_unsigned_message(
        self, unsigned_msg: Any
    ) -> bytes:
        """Wrap a VCSEC message into a secure RoutableMessage and prepend length."""
        # Wrap UnsignedMessage into ToVCSECMessage
        to_vcsec = vcsec_pb2.ToVCSECMessage()
        to_vcsec.signedMessage.protobufMessageAsBytes = unsigned_msg.SerializeToString()
        to_vcsec.signedMessage.signatureType = vcsec_pb2.SIGNATURE_TYPE_NONE

        payload_bytes = to_vcsec.SerializeToString()

        # Secure wrap
        routable_msg = self._session_manager.wrap_message(
            domain=universal_message_pb2.DOMAIN_VEHICLE_SECURITY,
            payload_bytes=payload_bytes,
        )

        return self._encode_ble_message(routable_msg)

    def _wrap_car_server_action(self, action: Any) -> bytes:
        """Wrap a CarServer action into a secure RoutableMessage and prepend length."""
        payload_bytes = action.SerializeToString()

        # Secure wrap
        routable_msg = self._session_manager.wrap_message(
            domain=universal_message_pb2.DOMAIN_INFOTAINMENT,
            payload_bytes=payload_bytes,
        )

        return self._encode_ble_message(routable_msg)

    def _encode_ble_message(self, msg: Any) -> bytes:
        """Prepend 2-byte BE length header to serialized RoutableMessage."""
        data = msg.SerializeToString()
        length = len(data)
        return struct.pack(">H", length) + data

    # --- PARSING ---

    def parse_ble_notification(self, data: bytes) -> dict[str, Any]:
        """Parse an incoming BLE notification.

        Args:
            data: The raw BLE notification bytes.

        Returns:
            A dictionary containing the parsed message details.
        """
        if len(data) < 2:
            _LOGGER.warning("BLE notification too short: %d bytes", len(data))
            return {"error": "Too short"}

        length = struct.unpack(">H", data[:2])[0]
        payload = data[2:]

        if len(payload) < length:
            _LOGGER.warning(
                "BLE notification payload incomplete: %d/%d bytes", len(payload), length
            )
            return {"error": "Incomplete"}

        # Only take the expected length
        payload = payload[:length]

        try:
            routable_msg = universal_message_pb2.RoutableMessage.FromString(payload)
        except Exception as e:
            _LOGGER.error("Failed to parse RoutableMessage: %s", e)
            return {"error": "Parse error"}

        domain = routable_msg.from_destination.domain

        try:
            decrypted_payload = self._session_manager.unwrap_message(
                domain, routable_msg
            )
        except Exception as e:
            _LOGGER.error("Failed to unwrap message from domain %s: %s", domain, e)
            return {"error": "Decryption error", "domain": domain}

        result: dict[str, Any] = {
            "domain": domain,
            "routable_message": routable_msg,
        }

        # Interpret decrypted payload
        if domain == universal_message_pb2.DOMAIN_VEHICLE_SECURITY:
            self._handle_vcsec_payload(decrypted_payload, result)
        elif domain == universal_message_pb2.DOMAIN_INFOTAINMENT:
            self._handle_infotainment_payload(decrypted_payload, result)
        elif domain == universal_message_pb2.DOMAIN_BROADCAST:
            # Broadcast messages are usually session info or status
            # SessionManager already handles session info inside unwrap_message
            # but we might still want to parse it here if needed.
            pass

        return result

    def _handle_vcsec_payload(self, payload: bytes, result: dict[str, Any]) -> None:
        """Parse VCSEC payload."""
        try:
            # Responses from vehicle are wrapped in FromVCSECMessage
            from_vcsec = vcsec_pb2.FromVCSECMessage.FromString(payload)
            result["msg_type"] = from_vcsec.WhichOneof("sub_message")
            result["payload"] = from_vcsec

            _LOGGER.debug("Parsed VCSEC message: %s", result["msg_type"])
        except Exception as e:
            _LOGGER.warning("Failed to parse FromVCSECMessage: %s", e)
            result["error"] = "VCSEC parse error"

    def _handle_infotainment_payload(
        self, payload: bytes, result: dict[str, Any]
    ) -> None:
        """Parse Infotainment payload."""
        try:
            # Responses from vehicle are wrapped in CarServer.Response
            response = car_server_pb2.Response.FromString(payload)
            result["msg_type"] = response.WhichOneof("response_msg")
            result["payload"] = response

            # If it's actionStatus, also include the result
            if response.HasField("actionStatus"):
                result["action_status"] = response.actionStatus.result

            _LOGGER.debug("Parsed Infotainment message: %s", result["msg_type"])
        except Exception as e:
            _LOGGER.warning("Failed to parse CarServer.Response: %s", e)
            result["error"] = "CarServer parse error"
