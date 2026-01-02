"""Constants for the Tesla BLE integration."""

from typing import Final

DOMAIN: Final = "tesla_ble"

CONF_VIN: Final = "vin"
CONF_PUBLIC_KEY: Final = "public_key"
CONF_PRIVATE_KEY: Final = "private_key"

# Options
CONF_TIMEOUT_SECONDS: Final = "timeout_seconds"
DEFAULT_TIMEOUT_SECONDS: Final = 900  # 15 minutes

# Tesla BLE Service UUID
TESLA_SERVICE_UUID: Final = "00000211-b2d1-43f0-9b88-960cebf8b91e"
