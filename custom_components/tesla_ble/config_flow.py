"""Config flow for Tesla BLE integration."""

from __future__ import annotations

import asyncio
import logging
import struct
from dataclasses import dataclass
from typing import Any, Final, Iterable

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow

from .ble_client import TeslaHABLEClient
from .const import (
    CONF_PRIVATE_KEY,
    CONF_PUBLIC_KEY,
    CONF_VIN,
    DOMAIN,
    TESLA_SERVICE_UUID,
)
from .core.ble_interface import close_stale_connections_by_address
from .core.proto import universal_message_pb2, vcsec_pb2
from .core.session_manager import TeslaSessionManager

_LOGGER = logging.getLogger(__name__)

_PAIRING_WAIT_SECONDS: Final[int] = 45


@dataclass(slots=True)
class _PairingResult:
    success: bool
    error: str | None = None


class TeslaPairingWizard:
    """Helper to perform an ephemeral pairing attempt over BLE."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TeslaHABLEClient,
        session_manager: TeslaSessionManager,
        address: str,
    ) -> None:
        self._hass = hass
        self._client = client
        self._session_manager = session_manager
        self._address = address

        self._rx_buffer = bytearray()
        self._result_event = asyncio.Event()
        self._result: _PairingResult | None = None

        self._notifications_registered = False

    async def async_prepare(self) -> None:
        """Connect and register notification callback."""
        await close_stale_connections_by_address(self._address)

        if not await self._client.connect(self._address):
            raise ConnectionError(f"Failed to connect to {self._address}")

        if not self._notifications_registered:
            await self._client.register_notification_callback(self._handle_notification)
            self._notifications_registered = True

    async def async_cleanup(self) -> None:
        """Disconnect from the vehicle."""
        await self._client.disconnect()

    def is_finished(self) -> bool:
        """Return True if pairing has completed (success or failure)."""
        return self._result is not None

    def get_result(self) -> _PairingResult | None:
        """Return the current pairing result (if any)."""
        return self._result

    async def async_send_pairing_request(self) -> None:
        """Send the VCSEC whitelist operation pairing request."""
        to_vcsec = self._session_manager.prepare_pairing_message()
        routable = universal_message_pb2.RoutableMessage()
        routable.to_destination.domain = universal_message_pb2.DOMAIN_VEHICLE_SECURITY  # type: ignore[attr-defined]
        routable.from_destination.domain = universal_message_pb2.DOMAIN_BROADCAST  # type: ignore[attr-defined]
        routable.flags = universal_message_pb2.FLAG_USER_COMMAND
        routable.protobuf_message_as_bytes = to_vcsec.SerializeToString()

        data = self._encode_ble_frame(routable.SerializeToString())
        await self._client.write_characteristic(data)

    async def async_wait_for_result(self, timeout: float) -> _PairingResult:
        """Wait for an OK/ERROR CommandStatus from the vehicle."""
        if self._result is not None:
            return self._result

        try:
            await asyncio.wait_for(self._result_event.wait(), timeout=timeout)
        except TimeoutError:
            return _PairingResult(success=False, error="pairing_failed")

        assert self._result is not None
        return self._result

    @staticmethod
    def _encode_ble_frame(payload: bytes) -> bytes:
        """Tesla BLE framing: 2-byte big-endian length prefix + payload."""
        return struct.pack(">H", len(payload)) + payload

    def _set_result_once(self, result: _PairingResult) -> None:
        if self._result is not None:
            return
        self._result = result
        self._result_event.set()

    def _handle_notification(self, data: bytes) -> None:
        """Handle BLE notifications; buffers frames and parses RoutableMessages."""
        self._rx_buffer.extend(data)

        while True:
            if len(self._rx_buffer) < 2:
                return

            frame_len = struct.unpack(">H", self._rx_buffer[:2])[0]
            if len(self._rx_buffer) < 2 + frame_len:
                return

            frame = bytes(self._rx_buffer[2 : 2 + frame_len])
            del self._rx_buffer[: 2 + frame_len]

            self._handle_frame(frame)

    def _handle_frame(self, frame: bytes) -> None:
        try:
            msg = universal_message_pb2.RoutableMessage.FromString(frame)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Pairing: failed to parse RoutableMessage: %s", err)
            return

        # Universal message error (rare during pairing but can happen)
        if msg.HasField("signedMessageStatus"):
            status = msg.signedMessageStatus
            if status.operation_status == universal_message_pb2.OPERATIONSTATUS_ERROR:
                _LOGGER.warning(
                    "Pairing: vehicle returned universal error: %s",
                    status.signed_message_fault,
                )
                self._set_result_once(_PairingResult(False, error="pairing_failed"))
                return

        # Only VCSEC responses are relevant to whitelisting.
        if msg.from_destination.domain != universal_message_pb2.DOMAIN_VEHICLE_SECURITY:  # type: ignore[attr-defined]
            return

        if msg.WhichOneof("payload") != "protobuf_message_as_bytes":
            return

        payload = msg.protobuf_message_as_bytes
        try:
            from_vcsec = vcsec_pb2.FromVCSECMessage.FromString(payload)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Pairing: failed to parse FromVCSECMessage: %s", err)
            return

        if from_vcsec.WhichOneof("sub_message") == "commandStatus":
            cmd_status = from_vcsec.commandStatus

            # When pairing, we care about whitelistOperationStatus.
            if cmd_status.WhichOneof("sub_message") == "whitelistOperationStatus":
                wl = cmd_status.whitelistOperationStatus

                # OK means the key was accepted/added.
                if (
                    cmd_status.operationStatus == vcsec_pb2.OPERATIONSTATUS_OK
                    and wl.operationStatus == vcsec_pb2.OPERATIONSTATUS_OK
                ):
                    _LOGGER.info("Pairing: whitelist operation OK (paired)")
                    self._set_result_once(_PairingResult(True))
                    return

                # WAIT means "tap key card / waiting for UI".
                if (
                    cmd_status.operationStatus == vcsec_pb2.OPERATIONSTATUS_WAIT
                    or wl.operationStatus == vcsec_pb2.OPERATIONSTATUS_WAIT
                ):
                    _LOGGER.debug("Pairing: whitelist operation WAIT (awaiting tap)")
                    return

                # ERROR is a hard fail.
                if (
                    cmd_status.operationStatus == vcsec_pb2.OPERATIONSTATUS_ERROR
                    or wl.operationStatus == vcsec_pb2.OPERATIONSTATUS_ERROR
                ):
                    _LOGGER.warning(
                        "Pairing: whitelist operation ERROR info=%s",
                        wl.whitelistOperationInformation,
                    )
                    self._set_result_once(_PairingResult(False, error="pairing_failed"))
                    return


class TeslaBLEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tesla BLE."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, str] = {}
        self._address: str | None = None
        self._vin: str | None = None

        self._session_manager: TeslaSessionManager | None = None
        self._client: TeslaHABLEClient | None = None
        self._pairing_wizard: TeslaPairingWizard | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a flow initialized by Bluetooth discovery."""
        self._discovery_info = discovery_info
        self._address = discovery_info.address
        self._discovered_devices = {
            discovery_info.address: discovery_info.name or discovery_info.address
        }

        await self.async_set_unique_id(self._address)
        self._abort_if_already_configured()

        return await self.async_step_vin()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the manual setup step (select a vehicle)."""
        if user_input is not None:
            self._address = user_input["device"]
            await self.async_set_unique_id(self._address)
            self._abort_if_already_configured()
            return await self.async_step_vin()

        discovered: Iterable[BluetoothServiceInfoBleak] = async_discovered_service_info(self.hass)
        self._discovered_devices: dict[str, str] = {}

        for info in discovered:
            is_tesla = False

            if (
                TESLA_SERVICE_UUID in info.service_uuids
                or "00001122-0000-1000-8000-00805f9b34fb" in info.service_uuids
            ):
                is_tesla = True
            elif (
                info.name
                and info.name.startswith("S")
                and info.name.endswith("C")
                and len(info.name) == 18
            ):
                try:
                    int(info.name[1:-1], 16)
                    is_tesla = True
                except ValueError:
                    is_tesla = False

            if is_tesla:
                self._discovered_devices[info.address] = info.name or info.address

        if not self._discovered_devices:
            return self.async_show_form(
                step_id="user",
                errors={"base": "no_devices_found"},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("device"): vol.In(self._discovered_devices)}
            ),
        )

    async def async_step_vin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the VIN entry step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            vin = str(user_input[CONF_VIN]).strip().upper()
            if len(vin) != 17:
                errors[CONF_VIN] = "invalid_vin"
            else:
                self._vin = vin
                return await self.async_step_pair()

        return self.async_show_form(
            step_id="vin",
            data_schema=vol.Schema({vol.Required(CONF_VIN): str}),
            errors=errors,
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the pairing step.

        This step attempts to auto-complete pairing by waiting for VCSEC to return
        `commandStatus.whitelistOperationStatus` with `OPERATIONSTATUS_OK`.
        If we time out, we show a manual "tap key card then click" form.
        """
        if self._address is None:
            return self.async_abort(reason="missing_address")

        if self._session_manager is None:
            self._session_manager = TeslaSessionManager(vin=self._vin)
        else:
            if self._vin:
                self._session_manager.set_vin(self._vin)

        if self._client is None:
            self._client = TeslaHABLEClient(self.hass)

        if self._pairing_wizard is None:
            self._pairing_wizard = TeslaPairingWizard(
                hass=self.hass,
                client=self._client,
                session_manager=self._session_manager,
                address=self._address,
            )

        try:
            await self._pairing_wizard.async_prepare()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Pairing: cannot connect to %s: %s", self._address, err)
            return self.async_show_form(
                step_id="user",
                errors={"base": "cannot_connect"},
            )

        try:
            # If user submits the form, we treat it as "try again now".
            await self._pairing_wizard.async_send_pairing_request()
            result = await self._pairing_wizard.async_wait_for_result(
                timeout=_PAIRING_WAIT_SECONDS
            )
        finally:
            # Keep the connection during manual retry screen, but cleanup once finished.
            if self._pairing_wizard.is_finished():
                await self._pairing_wizard.async_cleanup()

        if result.success:
            assert self._session_manager is not None
            return self.async_create_entry(
                title=f"Tesla {self._vin or self._address}",
                data={
                    CONF_ADDRESS: self._address,
                    CONF_VIN: self._vin,
                    CONF_PUBLIC_KEY: self._session_manager.public_key_bytes.hex(),
                    CONF_PRIVATE_KEY: self._session_manager.private_key_bytes.hex(),
                },
            )

        # If auto-wait failed/timeout, show the manual prompt form.
        # User can click continue; we will resend and wait again.
        return self.async_show_form(
            step_id="pair",
            errors={"base": result.error or "pairing_failed"},
            description_placeholders={
                "name": self._discovered_devices.get(self._address, self._address)
            },
        )

    def _abort_if_already_configured(self) -> None:
        """Abort if the device is already configured."""
        for entry in self._async_current_entries():
            if entry.data.get(CONF_ADDRESS) == self._address:
                raise AbortFlow("already_configured")
