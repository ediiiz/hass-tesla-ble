# Data Model: Improve Tesla BLE Proxy Integration

## Core Models (`custom_components/tesla_ble/core/models.py`)

Using `pydantic` for data validation and serialization.

### Session State
Stores the cryptographic material and sync state.

```python
class TeslaSession(BaseModel):
    vehicle_vin: str
    private_key: SecretStr  # Local private key (PEM)
    public_key: str        # Local public key (Hex)
    vehicle_public_key: str # Vehicle's public key (Hex)
    
    # Counter synchronization
    counter: int = 0
    epoch: bytes = b""
    
    # Validation helpers
    def get_private_key_bytes(self) -> bytes: ...
```

### Protocol Messages
Generated from protobufs (`custom_components/tesla_ble/core/proto/`).

## Configuration Entry (`custom_components/tesla_ble/const.py`)

Structure of data stored in `.storage/core.config_entries`.

```json
{
  "entry_id": "...",
  "domain": "tesla_ble",
  "title": "My Model 3",
  "data": {
    "vin": "5YJ...",
    "mac_address": "XX:XX:XX:XX:XX:XX",
    "private_key": "...",
    "public_key": "...",
    "vehicle_public_key": "..."
  },
  "options": {
    "always_connected": true,
    "scan_interval": 30
  }
}
```

## Application Logic Interfaces

### `TeslaBLEClient` (`core/ble_interface.py`)

Wrapper around `bleak_retry_connector`.

```python
class TeslaBLEClient:
    def __init__(self, address: str, session: TeslaSession): ...
    
    async def connect(self) -> bool: ...
    async def disconnect(self): ...
    
    async def send_command(self, domain: Domain, command: Command) -> None: ...
    
    def register_callback(self, callback: Callable[[BluetoothServiceInfoBleak], None]): ...
```

### `TeslaSessionManager` (`core/session_manager.py`)

Handles the cryptographic handshake.

```python
class TeslaSessionManager:
    def __init__(self, session: TeslaSession): ...
    
    def sign_message(self, message: bytes) -> bytes: ...
    def encrypt_message(self, message: bytes) -> bytes: ...
    def decrypt_message(self, message: bytes) -> bytes: ...
    
    # State mutation
    def increment_counter(self): ...
```

## Home Assistant Entities

### `TeslaVehicleEntity` (Base)
Inherits from `CoordinatorEntity`.

- `_attr_available`: bool (mapped to connection state)
- `_attr_device_info`: DeviceInfo (VIN, Model)

### `Lock` (`lock.py`)
- `async_lock()`
- `async_unlock()`

### `BinarySensor` (`binary_sensor.py`)
- `charging_state`
- `door_state`
