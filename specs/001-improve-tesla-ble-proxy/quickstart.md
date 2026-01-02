# Quickstart: Improve Tesla BLE Proxy Integration

## Installation

Since this is a custom component, you must install it via HACS or manually.

1.  **HACS**: Add this repository as a custom repository.
2.  **Manual**: Copy `custom_components/tesla_ble` to your HA `config/custom_components/` directory.

## Prerequisties

- **Bluetooth Infrastructure**: access to a Bluetooth adapter (local or ESPHome proxy).
- **Tesla Key Card**: You MUST have your physical key card ready to pair the integration with your vehicle.

## Setup & Pairing

1.  Go to **Settings > Devices & Services**.
2.  Click **Add Integration** and search for "Tesla BLE".
3.  **Discovery**:
    - The integration should automatically discover nearby Tesla vehicles transmitting BLE beacons.
    - If your car is found, click "Configure".
4.  **Pairing**:
    - The wizard will connect to the car.
    - **Action**: When prompted, tap your Key Card on the center console (cup holder area) to authorize the new key.
    - The wizard will auto-advance once the car accepts the key.

## Configuration Options

Click "Configure" on the integration entry to change settings:

- **Always Connected** (Default: On): Maintains a persistent BLE connection for instant commands. Turning this off saves vehicle battery but adds ~5s delay to commands.

## Troubleshooting

- **"No devices found"**: ensure your proxy is close enough to the vehicle and the vehicle is awake (open a door).
- **"Pairing failed"**: Try removing the "Home Assistant" key from the car's lock menu and try again.
