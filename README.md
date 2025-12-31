# Tesla BLE Local Control for Home Assistant

A Home Assistant Addon built with Rust that enables local, low-latency control of Tesla vehicles via Bluetooth Low Energy (BLE). This addon communicates with vehicles using BLE and publishes all vehicle entities to MQTT for integration with Home Assistant.

> **⚠️ Work in Progress** - This project is currently under active development and is not yet functional. Do not attempt to install or use it.

## Features (Planned)

- **Rust + bluer**: Type-safe, high-performance implementation with low resource footprint and memory safety
- **Local BLE Control**: Commands sent directly from the addon to vehicle via BLE, no Tesla Cloud dependency
- **MQTT Entity Publishing**: All vehicle state and controls published as MQTT entities for Home Assistant discovery
- **USB Bluetooth Adapter Passthrough**: Direct passthrough of USB Bluetooth adapters to the addon container for native BLE access via BlueZ
- **Built-in Pairing Handler**: The addon handles the complete vehicle pairing flow including whitelist operations
- **Secure Protocol**: Full implementation of Tesla Vehicle Command Protocol including ECDH key exchange and authenticated messaging
- **Planned Entities**:
  - **Lock**: Lock and unlock your vehicle
  - **Climate**: Toggle climate control
  - **Charging**: Start/stop charging, monitor battery level and range
  - **Buttons**: Open trunk, frunk, and charge port
  - **Sensors**: Battery SOC, range, and closure states (trunk/frunk)

## Architecture

This addon follows the Home Assistant Addon specification with a Rust codebase compiled to a native binary.

### Project Structure

```
hass-tesla-ble/
├── src/
│   └── main.rs              # Main addon entry point
├── Cargo.toml               # Rust dependencies
├── Cargo.lock               # Lockfile
├── Dockerfile               # Container build (Rust)
├── build.rs                 # Prost build script for proto compilation
├── config.json              # Addon configuration
├── proto/                   # Protocol buffer definitions
│   ├── vcsec.proto
│   ├── vehicle.proto
│   └── ...
└── references/              # Reference implementations
```

### Tech Stack

- **Language**: Rust - Memory-safe, zero-cost abstractions, excellent async support
- **BLE**: bluer - BlueZ D-Bus bindings for Bluetooth Low Energy on Linux
- **MQTT**: rumqttd/paho-mqtt - MQTT client for Home Assistant communication
- **Protocol Buffers**: prost + prost-build - Compile Protocol Buffers to Rust
- **Async Runtime**: tokio - Async runtime for concurrent BLE and MQTT operations
- **Cryptography**: ed25519, x25519 - ECDH key exchange and message signing

## Installation (Not Yet Available)

Once functional:

1. Add this repository to your Home Assistant Supervisor add-on store
2. Install the "Tesla BLE Local Control" add-on
3. Configure MQTT broker connection in add-on options
4. Start the add-on and configure vehicle pairing via the add-on logs

## Configuration

The addon requires basic configuration to get started:

```json
{
  "mqtt": {
    "host": "core-mosquitto",
    "port": 1883,
    "username": "",
    "password": "",
    "discovery_prefix": "homeassistant"
  },
  "bluetooth": {
    "adapter": "hci0",
    "mode": "usb_passthrough"
  },
  "vehicle": {
    "vin": "your-vehicle-vin"
  }
}
```

**Vehicle VIN**: Provide your Tesla vehicle's 17-character VIN. This is used to identify your vehicle during the BLE discovery and pairing process. You can find your VIN in the Tesla mobile app under your vehicle details, on the vehicle's registration documents, or on the driver's side dashboard.

The addon automatically handles:
- Cryptographic key pair generation during pairing
- Credential storage after successful pairing
- No manual private key configuration required

### Bluetooth Configuration

The addon requires a USB Bluetooth adapter passed through from the host system. This provides direct access to BLE hardware via BlueZ for maximum reliability and performance.

**Requirements:**
- BlueZ Bluetooth daemon must be available in the container
- D-Bus system bus access for bluer crate
- USB Bluetooth adapter passthrough enabled

1. Connect a USB Bluetooth dongle to your Home Assistant host
2. In the add-on options, enable USB passthrough for the adapter
3. Specify the adapter device (e.g., `hci0` or `hci1`) in the configuration

## Pairing Process

The addon handles the complete Tesla vehicle pairing flow:

1. **Discovery**: Scan for nearby Tesla vehicles via BLE using bluer
2. **Key Generation**: Generate a unique cryptographic key pair using Rust crypto libraries
3. **Whitelist Request**: Send a pairing request to the vehicle
4. **Authorization**: Approve the request on the vehicle's center console or with a key card
5. **Verification**: Confirm successful pairing and store credentials
6. **Auto-Discovery**: Automatically configure MQTT entities in Home Assistant

All pairing steps are managed by the addon - no additional configuration flows are required in Home Assistant itself.

## MQTT Entity Structure

Entities will be published following Home Assistant MQTT Discovery conventions:

```
homeassistant/lock/{vehicle_vin}/lock/config
homeassistant/switch/{vehicle_vin}/climate/config
homeassistant/sensor/{vehicle_vin}/battery/config
...
```

## Protocol Implementation

This project implements the Tesla Vehicle Command Protocol using the provided Protocol Buffer definitions in the [`proto/`](proto/) directory, compiled to Rust via prost:

- **[`vcsec.proto`](proto/vcsec.proto)**: Vehicle Security (key pairing, authorization)
- **[`vehicle.proto`](proto/vehicle.proto)**: Vehicle control messages
- **[`car_server.proto`](proto/car_server.proto)**: Car server communication
- **[`common.proto`](proto/common.proto)**: Common message types

Protocol buffer compilation is handled automatically via `build.rs` using `prost-build`.

## Development Status

- [ ] Rust project setup (Cargo.toml, main.rs)
- [ ] BlueZ/bluer integration
- [ ] Protocol buffer compilation (prost, build.rs)
- [ ] BLE client implementation (scanning, connection, characteristic operations)
- [ ] MQTT client integration
- [ ] Home Assistant MQTT discovery
- [ ] Vehicle pairing flow (key generation, whitelisting, ECDH)
- [ ] Basic command execution (lock/unlock)
- [ ] Sensor state monitoring
- [ ] Docker container build (rust:alpine base)
- [ ] Testing and debugging

## Building from Source

```bash
# Build the Rust project
cargo build --release

# Run in release mode
cargo run --release

# Run tests
cargo test
```

The `build.rs` script automatically compiles Protocol Buffer definitions using `prost-build` before the main compilation.

## Dependencies

Key Rust crates used in this project:

```toml
[dependencies]
bluer = "0.17"          # BlueZ D-Bus bindings for BLE
rumqttd = "0.19"        # MQTT client (or paho-mqtt)
prost = "0.12"          # Protocol Buffers runtime
tokio = { version = "1", features = ["full"] }  # Async runtime
ed25519-dalek = "2"     # Ed25519 signatures
x25519-dalek = "2"      # ECDH key exchange
serde = "1"             # Serialization
serde_json = "1"        # JSON support
log = "0.4"             # Logging
env_logger = "0.11"     # Logger implementation

[build-dependencies]
prost-build = "0.12"    # Protocol Buffer compiler
```

## System Requirements

- Home Assistant OS or Supervisor
- USB Bluetooth adapter compatible with BlueZ
- MQTT broker (typically Home Assistant's Mosquitto add-on)
- Docker container support for Rust-based add-on

## Disclaimer

This project is not affiliated with or endorsed by Tesla, Inc. Use it at your own risk. Controlling your vehicle via third-party software can have safety implications.

## References

This project builds upon research and implementations by:
- [pedroktfc](references/pedro/) - ESPHome Tesla BLE implementation
- [yoziru](references/yoziru/) - Tesla BLE protocol research
