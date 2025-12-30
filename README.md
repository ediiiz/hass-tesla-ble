# Tesla BLE Local Control for Home Assistant

This Home Assistant custom integration allows for local, low-latency control of Tesla vehicles via Bluetooth Low Energy (BLE). It leverages Home Assistant's built-in Bluetooth stack and remote BLE proxies, requiring no additional hardware beyond what Home Assistant already supports.

## Features

- **Local Control**: All commands are sent directly from Home Assistant to the vehicle via BLE. No Tesla Cloud dependency for basic operations.
- **Remote BLE Proxy Support**: Works seamlessly with ESPHome Bluetooth proxies, extending your range throughout your property.
- **Secure Protocol**: Full implementation of the Tesla Vehicle Command Protocol, including ECDH key exchange and authenticated messaging.
- **Fast Response**: Near-instantaneous execution of commands.
- **Comprehensive Entities**:
  - **Lock**: Lock and unlock your vehicle.
  - **Climate**: Toggle climate control.
  - **Charging**: Start/stop charging and monitor battery level/range.
  - **Buttons**: Open trunk, frunk, and charge port.
  - **Sensors**: Monitor battery SOC, range, and closure states (trunk/frunk).

## Installation

### Option 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Add this repository as a Custom Repository in HACS (Category: Integration).
3. Search for "Tesla BLE" and click **Download**.
4. Restart Home Assistant.

### Option 2: Manual

1. Download the `custom_components/tesla_ble` directory from this repository.
2. Copy it to your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.

## Configuration & Pairing Guide

Pairing a Tesla vehicle via BLE requires a secure handshake and authorization on the vehicle's screen.

### 1. Discovery
- Go to **Settings > Devices & Services** in Home Assistant.
- Click **Add Integration** and search for **Tesla BLE**.
- The integration will scan for nearby Tesla vehicles. Select your vehicle from the list.

### 2. Authorization (Whitelist Operation)
- After selecting your vehicle, Home Assistant will generate a unique cryptographic key pair for this integration.
- You will be prompted to "Pair" with the vehicle.
- **Crucial Step**: You must be near the vehicle with a physical Key Card (or phone key).
- When you click "Next" in Home Assistant, it sends a `WhitelistOperation` request to the vehicle.
- **Vehicle Interaction**: You must tap your Key Card on the center console (behind the cup holders) or follow the prompts on the vehicle's center screen to authorize the new "Home Assistant" key.

### 3. Verification
- Once authorized, the vehicle will appear as a new device in Home Assistant with its VIN as the unique identifier.
- You can now control the vehicle locally.

## Troubleshooting

### Connection Issues
- **Range**: Ensure your Home Assistant Bluetooth adapter or BLE proxy is within 5-10 meters of the vehicle.
- **Proxy Latency**: If using an ESPHome proxy, ensure it has a stable network connection.
- **Multiple Clients**: Tesla vehicles have a limit on active BLE connections. If your phone app is actively connected and "awake," it might occasionally interfere with Home Assistant's initial connection.

### Pairing Failures
- **Timeout**: If the vehicle doesn't prompt for authorization, try waking the vehicle first (e.g., by opening a door or using the official app) and then restart the config flow.
- **Key Limit**: If your vehicle has reached its limit of paired keys, you may need to remove an old key via the vehicle's UI (Controls > Locks).

## Architecture

This integration is a pure Python implementation of the Tesla Vehicle Command Protocol. It does not rely on external Go binaries or wrappers.

- **`core/crypto.py`**: Handles ECDH, HKDF, and AES-GCM operations using the `cryptography` library.
- **`core/protocol.py`**: Implements the RoutableMessage logic and VCSEC/CarServer message building.
- **`ble_client.py`**: Wraps Home Assistant's `async_bleAK` for robust connection management.

## Disclaimer

This project is not affiliated with or endorsed by Tesla, Inc. Use it at your own risk. Controlling your vehicle via third-party software can have safety implications.
