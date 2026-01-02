# Research: Improve Tesla BLE Proxy Integration

## Unknowns Resolution

### 1. BLE Connection Reliability
**Context**: Connecting to BLE devices via proxies can be flaky if previous connections aren't cleaned up or if the vehicle moves between proxies.
**Reference**: `yalexs_homeassistant_bt_reference_implementation.txt`
**Findings**:
- The Yale integration uses `close_stale_connections_by_address(address)` before attempting setup. This is critical for `FR-003`.
- It uses `bleak_retry_connector` for robust connection handling.
- It implements an "Always Connected" toggle (`CONF_ALWAYS_CONNECTED`) which directly maps to `FR-004` and `FR-005`.
**Decision**:
- Adopt `bleak_retry_connector` for the `TeslaBLEClient`.
- Implement `close_stale_connections_by_address` in `__init__.py` or `config_flow.py` before connection attempts.
- Expose "Always Connected" limitation in Options Flow.

### 2. Pairing Process (Config Flow)
**Context**: Tesla pairing involves:
1. Connecting to the car.
2. Sending a "Request key" message.
3. User tapping key card on center console.
4. Car sending "Key added" confirmation.
**Reference**: `yalexs_ble/config_flow.py` uses `async_step_integration_discovery` and `async_step_key_slot`.
**Findings**:
- Yale validates keys offline or via cloud. Tesla requires *interactive* pairing with the device.
- We need a `async_step_pair` that maintains a connection while polling/waiting for the auth callback.
**Decision**:
- Create a `TeslaPairingWizard` helper class used by ConfigFlow.
- It will establish a temporary `BleakClient` just for the pairing transaction.
- Upon success, it returns the public key/token to be stored in `ConfigEntry`.

### 3. Protocol Implementation
**Context**: We need to speak Tesla's VCSEC protocol.
**Reference**: `proto/` directory exists with `.proto` files.
**Findings**:
- We have `vcsec.proto`, `car_server.proto`, etc.
- We need to generate Python classes.
**Decision**:
- Use `protoc` (via `uv` or system) to generate Python code into `custom_components/tesla_ble/core/proto/`.
- Ensure `__init__.py` in that dir exposes them cleanly.

### 4. Logic Porting (ESPHome to Python)
**Context**: `esphome-tesla-ble` is C++.
**Reference**: `references/pedro/esphome-tesla-ble-reference.txt` (implied availability).
**Findings**:
- `SessionManager` state machine needs to be ported to `TeslaSessionManager`.
- Crypto primitives (ECDH) need to map to `cryptography` library.
**Decision**:
- `TeslaSessionManager` will handle:
  - `GenerateEphemeralKey()`
  - `SignMessage()`
  - `VerifySignature()`
  - `IncrementCounter()`

## Technology Choices

| Area | Choice | Rationale | Alternatives |
|------|--------|-----------|--------------|
| **BLE Client** | `bleak_retry_connector` | Standard HA library, handles proxy edge cases better than raw `BleakClient`. | Raw `bleak` (flakey) |
| **Crypto** | `cryptography` | Reference standard for secure primitives in Python. | `pycryptodome` (less standard in modern HA) |
| **Serialization** | `protobuf` | Official Google library, matches `.proto` source. | `pure-protobuf` (less robust) |
| **State Mgmt** | `pydantic` | Typesafe state handling for sessions and keys. | Raw dicts (error prone) |

## Data Flow

1. **Discovery**: `BluetoothServiceInfoBleak` received → `ConfigFlow`.
2. **Pairing**: `ConfigFlow` initializes `TeslaBLEClient` (temp) → Handshake → Store Keys.
3. **Runtime**: `TeslaBLEClient` (persistent) → `TeslaSessionManager` (encrypt/decrypt) → `TeslaVehicleEntity` (update HA state).
