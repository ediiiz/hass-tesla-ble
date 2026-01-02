# Interfaces: Improve Tesla BLE Proxy Integration

## Core Library Protocols

### `TeslaBLEClientProtocol`

The interface for the BLE transport layer.

```python
class TeslaBLEClientProtocol(Protocol):
    """Abstract interface for BLE communication."""
    
    @property
    def is_connected(self) -> bool: ...
    
    async def connect(self) -> bool:
        """Establish connection to the vehicle."""
        ...

    async def disconnect(self) -> None:
        """Close the connection."""
        ...
        
    async def write_gatt_char(self, char_uuid: str, data: bytes, response: bool = False) -> None:
        """Write data to a GATT characteristic."""
        ...
        
    def set_disconnected_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for disconnection events."""
        ...
```

### `TeslaSessionManagerProtocol`

The interface for session state and crypto operations.

```python
class TeslaSessionManagerProtocol(Protocol):
    """Abstract interface for session management."""
    
    def get_public_key(self) -> bytes:
        """Return the local public key bytes."""
        ...
        
    def sign(self, message: bytes) -> bytes:
        """Sign a message with the local private key."""
        ...
        
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt a message for the vehicle."""
        ...
        
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt a message from the vehicle."""
        ...
```

## Home Assistant Config Flow

### `ConfigFlowData`

Data structure passed between config flow steps.

```python
class ConfigFlowData(TypedDict):
    vin: str
    address: str
    name: str
    public_key: str
    private_key: str
```
