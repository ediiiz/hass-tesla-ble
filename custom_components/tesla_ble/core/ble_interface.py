"""Interface for Tesla BLE communication."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final

from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
)
from bleak_retry_connector import (
    close_stale_connections_by_address as _close_stale_connections_by_address,
)
from google.protobuf.message import DecodeError
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback

from .proto import universal_message_pb2

if TYPE_CHECKING:
    from .session_manager import TeslaSessionManager


# Tesla BLE Service and Characteristic UUIDs
TESLA_SERVICE_UUID: Final = "00000211-b2d1-43f0-9b88-960cebf8b91e"
TESLA_WRITE_CHAR_UUID: Final = "00000212-b2d1-43f0-9b88-960cebf8b91e"
TESLA_NOTIFY_CHAR_UUID: Final = "00000213-b2d1-43f0-9b88-960cebf8b91e"


async def close_stale_connections_by_address(address: str) -> None:
    """Close stale connections by address."""
    await _close_stale_connections_by_address(address)


class TeslaBLEError(Exception):
    """Base exception for Tesla BLE errors."""


class TeslaConnectionError(TeslaBLEError):
    """Error connecting to the vehicle."""


class TeslaBLEInterface:
    """Abstract base class for Tesla BLE clients."""

    async def connect(self, address: str | None = None) -> bool:
        """Connect to the vehicle.

        Args:
            address: Optional BLE address override.

        Returns:
            True if connection was successful, False otherwise.
        """
        raise NotImplementedError

    async def disconnect(self) -> None:
        """Disconnect from the vehicle."""
        raise NotImplementedError

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to the vehicle."""
        raise NotImplementedError

    async def write_characteristic(self, data: bytes) -> None:
        """Write data to the Tesla specific characteristic.

        Args:
            data: The bytes to write.
        """
        raise NotImplementedError

    async def send_command(self, domain: int, command: bytes) -> None:
        """Send a command to the vehicle.

        Args:
            domain: The target domain (e.g. VCSEC).
            command: The serialized command protobuf bytes.
        """
        raise NotImplementedError

    async def register_notification_callback(
        self, callback: Callable[[bytes], None]
    ) -> None:
        """Register a callback for receiving notifications.

        Args:
            callback: A function that takes bytes as an argument.
        """
        raise NotImplementedError


class TeslaBLEClient(TeslaBLEInterface):
    """Tesla BLE client implementation using Bleak."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        session_manager: TeslaSessionManager | None = None,
    ) -> None:
        """Initialize the Tesla BLE client.

        Args:
            hass: The Home Assistant instance.
            address: The MAC address of the vehicle.
            session_manager: The session manager instance.
        """
        self._hass = hass
        self._address = address
        self._session_manager = session_manager
        self._client: BleakClientWithServiceCache | None = None
        self._logger = logging.getLogger(__name__)
        self._notification_callbacks: list[Callable[[bytes], None]] = []
        self._keep_alive_task: asyncio.Task[None] | None = None
        self._connection_lock = asyncio.Lock()
        self._expected_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to the vehicle."""
        return self._client is not None and self._client.is_connected

    async def connect(self, address: str | None = None) -> bool:
        """Connect to the vehicle."""
        async with self._connection_lock:
            if address is not None:
                self._address = address

            if self.is_connected:
                return True

            self._logger.debug("Attempting to connect to %s", self._address)
            self._expected_connected = True

            device = bluetooth.async_ble_device_from_address(
                self._hass, self._address, connectable=True
            )
            if not device:
                self._logger.debug("Device %s not found", self._address)
                return False

            try:
                self._client = await establish_connection(
                    BleakClientWithServiceCache,
                    device,
                    self._address,
                    disconnected_callback=self._on_disconnect,
                    max_attempts=3,
                )
                self._logger.info("Connected to %s", self._address)

                # Start notifications immediately upon connection
                await self._client.start_notify(
                    TESLA_NOTIFY_CHAR_UUID, self._notification_handler
                )

                return True
            except Exception as e:
                self._logger.warning("Failed to connect to %s: %s", self._address, e)
                if self._client:
                    # noinspection PyBroadException
                    try:
                        await self._client.disconnect()
                    except Exception:  # pylint: disable=broad-except
                        pass
                    self._client = None
                return False

    async def disconnect(self) -> None:
        """Disconnect from the vehicle."""
        self._expected_connected = False
        self._cancel_keep_alive()

        async with self._connection_lock:
            if self._client:
                self._logger.debug("Disconnecting from %s", self._address)
                # noinspection PyBroadException
                try:
                    await self._client.disconnect()
                except Exception:  # pylint: disable=broad-except
                    pass
                self._client = None

    @callback
    def _on_disconnect(self, client: BleakClientWithServiceCache) -> None:
        """Handle disconnection."""
        self._logger.warning("Disconnected from %s", self._address)
        # NOTE: We intentionally avoid mutating `self._client` here.
        # The disconnect callback may race with connect()/disconnect() which hold
        # `_connection_lock`. `is_connected` relies on `self._client.is_connected`.
        # The keep-alive loop will reconnect and overwrite `self._client`.

        # Trigger keep-alive check immediately if expected to be connected
        if self._expected_connected and not self._keep_alive_task:
            self.start_keep_alive()

    def start_keep_alive(self) -> None:
        """Start the keep-alive loop."""
        if self._keep_alive_task and not self._keep_alive_task.done():
            return
        self._expected_connected = True
        self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())

    def _cancel_keep_alive(self) -> None:
        """Cancel the keep-alive loop."""
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            self._keep_alive_task = None

    async def _keep_alive_loop(self) -> None:
        """Keep the connection alive."""
        self._logger.debug("Keep-alive loop started for %s", self._address)
        while self._expected_connected:
            if not self.is_connected:
                self._logger.debug("Keep-alive reconnecting to %s", self._address)
                await self.connect()

            # Wait before checking again. If connected, we wait longer.
            # If not connected, we wait a bit to avoid hammer.
            # establish_connection already has backoff, but we add our own loop delay.
            await asyncio.sleep(5 if self.is_connected else 5)

    async def write_characteristic(self, data: bytes) -> None:
        """Write data to the Tesla specific characteristic."""
        if not self.is_connected:
            raise TeslaConnectionError("Not connected")

        assert self._client is not None
        try:
            await self._client.write_gatt_char(
                TESLA_WRITE_CHAR_UUID, data, response=True
            )
        except Exception as e:
            self._logger.error("Failed to write to %s: %s", self._address, e)
            raise TeslaConnectionError(f"Write failed: {e}") from e

    async def send_command(self, domain: int, command: bytes) -> None:
        """Send a command to the vehicle.

        Args:
            domain: The target domain (e.g. VCSEC).
            command: The serialized command protobuf bytes.
        """
        if not self._session_manager:
            await self.write_characteristic(command)
            return

        msg = self._session_manager.wrap_message(domain, command)
        data = msg.SerializeToString()
        await self.write_characteristic(data)

    async def register_notification_callback(
        self, callback: Callable[[bytes], None]
    ) -> None:
        """Register a callback for receiving notifications."""
        self._notification_callbacks.append(callback)

    @callback
    def _notification_handler(self, sender: Any, data: bytearray) -> None:
        """Handle incoming notifications."""
        data_bytes = bytes(data)

        if self._session_manager:
            try:
                msg = universal_message_pb2.RoutableMessage()
                msg.ParseFromString(data_bytes)
                domain = msg.from_destination.domain

                if msg.HasField("session_info"):
                    self._session_manager.update_session(domain, msg.session_info)

                # Attempt to decrypt payload.
                # unwrap_message returns protobuf bytes if not authenticated/encrypted,
                # otherwise the decrypted payload bytes.
                payload = self._session_manager.unwrap_message(domain, msg)
                data_bytes = payload

            except DecodeError:
                self._logger.debug("Failed to parse RoutableMessage, passing raw bytes")
            except Exception as e:
                self._logger.error("Error processing notification: %s", e)
                # If processing fails (e.g. decryption error), don't propagate garbage.
                return

        for cb in self._notification_callbacks:
            try:
                cb(data_bytes)
            except Exception as e:
                self._logger.error("Error in notification callback: %s", e)
