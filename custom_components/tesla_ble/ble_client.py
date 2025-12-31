"""Home Assistant BLE client implementation for Tesla BLE."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.core import HomeAssistant

from .core.ble_interface import (
    TESLA_NOTIFY_CHAR_UUID,
    TESLA_WRITE_CHAR_UUID,
    TeslaBLEInterface,
)

_LOGGER = logging.getLogger(__name__)


class TeslaHABLEClient(TeslaBLEInterface):
    """Home Assistant concrete implementation of TeslaBLEInterface.

    This client uses Home Assistant's Bluetooth component to leverage
    Bluetooth proxies and handle connections in a way that is compatible
    with the HA ecosystem.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the BLE client.

        Args:
            hass: The Home Assistant instance.
        """
        self._hass = hass
        self._client: BleakClient | None = None
        self._address: str | None = None

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to the vehicle."""
        return self._client is not None and self._client.is_connected

    async def connect(self, address: str) -> bool:
        """Connect to the vehicle using HA's Bluetooth infrastructure.

        Args:
            address: The MAC address or local name of the vehicle.

        Returns:
            True if connection was successful, False otherwise.
        """
        self._address = address
        _LOGGER.debug("Attempting to connect to Tesla vehicle at %s", address)

        try:
            # Get a BleakClient wrapper that works with HA's proxies
            device = async_ble_device_from_address(
                self._hass, address, connectable=True
            )
            if not device:
                _LOGGER.error("Could not find device with address %s", address)
                return False

            self._client = await establish_connection(
                BleakClient,
                device,
                name=address,
            )
            _LOGGER.info("Successfully connected to Tesla vehicle at %s", address)
            return True
        except BleakError as err:
            _LOGGER.error(
                "Bleak error while connecting to Tesla vehicle at %s: %s",
                address,
                err,
            )
            self._client = None
            return False
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Unexpected error connecting to Tesla vehicle at %s: %s",
                address,
                err,
            )
            self._client = None
            return False

    async def disconnect(self) -> None:
        """Disconnect from the vehicle."""
        if self._client:
            _LOGGER.debug("Disconnecting from Tesla vehicle at %s", self._address)
            try:
                await self._client.disconnect()
            except BleakError as err:
                _LOGGER.warning("Error during disconnect: %s", err)
            finally:
                self._client = None

    async def write_characteristic(self, data: bytes) -> None:
        """Write data to the Tesla specific characteristic.

        Args:
            data: The bytes to write.
        """
        if not self.is_connected or not self._client:
            _LOGGER.error("Cannot write: Not connected to vehicle")
            return

        try:
            # Tesla protocol uses write without response for performance.
            # We must manually fragment the data into small chunks (20 bytes)
            # because "Write Without Response" packets are not automatically
            # fragmented by most BLE stacks and will be dropped if they exceed
            # the negotiated MTU (or the default min MTU).
            #
            # NOTE: BLE MTU is usually negotiated. Bleak handles this if response=True.
            # For response=False, we must be careful.
            
            # Use a conservative chunk size.
            CHUNK_SIZE = 20
            total_chunks = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE
            
            _LOGGER.info(
                "Writing %d bytes to %s in %d chunks",
                len(data),
                TESLA_WRITE_CHAR_UUID,
                total_chunks
            )

            for i in range(0, len(data), CHUNK_SIZE):
                chunk = data[i : i + CHUNK_SIZE]
                chunk_num = i // CHUNK_SIZE + 1
                _LOGGER.info("Writing chunk %d/%d: %s", chunk_num, total_chunks, chunk.hex())
                
                await self._client.write_gatt_char(
                    TESLA_WRITE_CHAR_UUID, chunk, response=False
                )
                # Small sleep to avoid overwhelming the controller's TX queue
                await asyncio.sleep(0.05)
            
            _LOGGER.info("Finished writing all chunks")
                
        except BleakError as err:
            _LOGGER.error("Error writing to Tesla vehicle characteristic: %s", err)
            # We don't disconnect here, but the connection might be dead

    async def register_notification_callback(
        self, callback: Callable[[bytes], None]
    ) -> None:
        """Register a callback for receiving notifications from the vehicle.

        Args:
            callback: A function that takes bytes as an argument.
        """
        if not self.is_connected or not self._client:
            _LOGGER.error("Cannot register notification: Not connected to vehicle")
            return

        def _handle_notification(_: Any, data: bytearray) -> None:
            """Handle incoming notification data."""
            _LOGGER.debug("Received BLE notification: %s", data.hex())
            callback(bytes(data))

        try:
            await self._client.start_notify(
                TESLA_NOTIFY_CHAR_UUID, _handle_notification
            )
            _LOGGER.debug("Successfully registered notification callback")
        except BleakError as err:
            _LOGGER.error(
                "Error starting notifications on Tesla vehicle characteristic: %s",
                err,
            )
