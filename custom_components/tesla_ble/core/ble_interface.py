"""Interface for Tesla BLE communication."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Final

# Tesla BLE Service and Characteristic UUIDs
TESLA_SERVICE_UUID: Final = "00000211-0000-1000-8000-00805f9b34fb"
TESLA_WRITE_CHAR_UUID: Final = "00000002-0000-1000-8000-00805f9b34fb"
TESLA_NOTIFY_CHAR_UUID: Final = "00000003-0000-1000-8000-00805f9b34fb"


class TeslaBLEInterface(ABC):
    """Abstract base class for Tesla BLE clients."""

    @abstractmethod
    async def connect(self, address: str) -> bool:
        """Connect to the vehicle.

        Args:
            address: The MAC address or local name of the vehicle.

        Returns:
            True if connection was successful, False otherwise.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the vehicle."""

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected to the vehicle."""

    @abstractmethod
    async def write_characteristic(self, data: bytes) -> None:
        """Write data to the Tesla specific characteristic.

        Args:
            data: The bytes to write.
        """

    @abstractmethod
    async def register_notification_callback(
        self, callback: Callable[[bytes], None]
    ) -> None:
        """Register a callback for receiving notifications.

        Args:
            callback: A function that takes bytes as an argument.
        """
