# Tesla BLE Local Control for Home Assistant

A Home Assistant Addon built with TypeScript and Bun that enables local, low-latency control of Tesla vehicles via Bluetooth Low Energy (BLE). This addon communicates with vehicles using BLE and publishes all vehicle entities to MQTT for integration with Home Assistant.

> **⚠️ Work in Progress** - This project is currently under active development and is not yet functional. Do not attempt to install or use it.

## Features (Planned)

- **TypeScript + Bun Runtime**: Modern, type-safe implementation with fast startup and low resource usage
- **Local BLE Control**: Commands sent directly from the addon to vehicle via BLE, no Tesla Cloud dependency
- **MQTT Entity Publishing**: All vehicle state and controls published as MQTT entities for Home Assistant discovery
- **USB Bluetooth Adapter Passthrough**: Direct passthrough of USB Bluetooth adapters to the addon container for native BLE access
- **Built-in Pairing Handler**: The addon handles the complete vehicle pairing flow including whitelist operations
- **Secure Protocol**: Full implementation of Tesla Vehicle Command Protocol including ECDH key exchange and authenticated messaging
- **Planned Entities**:
  - **Lock**: Lock and unlock your vehicle
  - **Climate**: Toggle climate control
  - **Charging**: Start/stop charging, monitor battery level and range
  - **Buttons**: Open trunk, frunk, and charge port
  - **Sensors**: Battery SOC, range, and closure states (trunk/frunk)

## Architecture

This addon follows the Home Assistant Addon specification with a TypeScript codebase running on Bun.

### Project Structure

```
hass-tesla-ble/
├── index.ts              # Main addon entry point
├── config.json           # Addon configuration
├── Dockerfile            # Container build (Bun runtime)
├── package.json          # TypeScript dependencies
├── tsconfig.json         # TypeScript configuration
├── bun.lockb             # Bun lockfile
├── proto/                # Protocol buffer definitions
│   ├── vcsec.proto
│   ├── vehicle.proto
│   └── ...
└── references/           # Reference implementations
```

### Tech Stack

- **Runtime**: Bun - Fast JavaScript runtime with native TypeScript support
- **Language**: TypeScript - Type-safe development
- **Communication**: MQTT - Entity publishing to Home Assistant
- **Bluetooth**: Web Bluetooth / Noble (depending on platform) - BLE connectivity
- **Protocol**: Protocol Buffers - Vehicle communication protocol

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

The addon requires a USB Bluetooth adapter passed through from the host system. This provides direct access to BLE hardware for maximum reliability and performance.

1. Connect a USB Bluetooth dongle to your Home Assistant host
2. In the add-on options, enable USB passthrough for the adapter
3. Specify the adapter device (e.g., `hci0` or `hci1`) in the configuration

## Pairing Process

The addon handles the complete Tesla vehicle pairing flow:

1. **Discovery**: Scan for nearby Tesla vehicles via BLE
2. **Key Generation**: Generate a unique cryptographic key pair for the addon
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

This project implements the Tesla Vehicle Command Protocol using the provided Protocol Buffer definitions in the [`proto/`](proto/) directory:

- **[`vcsec.proto`](proto/vcsec.proto)**: Vehicle Security (key pairing, authorization)
- **[`vehicle.proto`](proto/vehicle.proto)**: Vehicle control messages
- **[`car_server.proto`](proto/car_server.proto)**: Car server communication
- **[`common.proto`](proto/common.proto)**: Common message types

## Development Status

- [ ] TypeScript project setup
- [ ] Bun runtime configuration
- [ ] BLE client implementation
- [ ] Protocol buffer compilation
- [ ] MQTT broker connection
- [ ] Home Assistant MQTT discovery
- [ ] Vehicle pairing flow
- [ ] Basic command execution (lock/unlock)
- [ ] Sensor state monitoring
- [ ] Docker container build
- [ ] Testing and debugging

## Building from Source

```bash
# Install dependencies
bun install

# Build TypeScript
bun run build

# Run for development
bun run dev
```

## Disclaimer

This project is not affiliated with or endorsed by Tesla, Inc. Use it at your own risk. Controlling your vehicle via third-party software can have safety implications.

## References

This project builds upon research and implementations by:
- [pedroktfc](references/pedro/) - ESPHome Tesla BLE implementation
- [yoziru](references/yoziru/) - Tesla BLE protocol research
