# Project Plan: hass-tesla-ble

This document outlines the development plan for the `hass-tesla-ble` Home Assistant integration.

## Milestone 1: Project Setup & Protocol Definitions
**Goal:** Establish the project structure and generate the necessary Protocol Buffer Python classes.

- [x] **1.1. Project Structure:** Create the initial directory structure for a Home Assistant Custom Component.
    - `custom_components/tesla_ble/`
    - `custom_components/tesla_ble/core/`
    - `pyproject.toml` (update dependencies)
- [x] **1.2. Extract Proto Files:** Extract `.proto` content from `references/yoziru-tesla-ble-*.txt` into individual files.
    - `proto/universal_message.proto`
    - `proto/vcsec.proto`
    - `proto/car_server.proto`
    - `proto/signatures.proto`
    - `proto/common.proto`
    - `proto/keys.proto`
    - `proto/errors.proto`
    - `proto/managed_charging.proto`
- [x] **1.3. Generate Python Classes:** Use `protoc` to generate Python code from the `.proto` files into `custom_components/tesla_ble/core/proto/`.

## Milestone 2: Core Library Implementation (Porting)
**Goal:** Port the C++ logic to a standalone Python library within the component.

- [x] **2.1. Crypto Module:** Implement ECDH key exchange, request signing, and message encryption/decryption using `cryptography` library.
    - `custom_components/tesla_ble/core/crypto.py`
- [x] **2.2. Session Manager:** Implement `TeslaSessionManager` to handle keys, counters, epochs, and authentication state.
    - `custom_components/tesla_ble/core/session_manager.py`
- [x] **2.3. BLE Client Interface:** Create an abstract base class or interface for the BLE client to decouple logic from HA's specific Bluetooth implementation.
    - `custom_components/tesla_ble/core/ble_interface.py`
- [x] **2.4. Protocol Layer:** Implement the logic to build and parse VCSEC and CarServer messages.
    - `custom_components/tesla_ble/core/protocol.py`

## Milestone 3: Home Assistant Integration - Connectivity
**Goal:** Connect to the vehicle using Home Assistant's Bluetooth stack.

- [x] **3.1. HA Bluetooth Client:** Implement the concrete BLE client using `homeassistant.components.bluetooth`.
    - `custom_components/tesla_ble/ble_client.py`
- [x] **3.2. Config Flow (Discovery):** Implement the `ConfigFlow` to discover Tesla BLE devices.
    - `custom_components/tesla_ble/config_flow.py`
- [x] **3.3. Config Flow (Pairing):** Implement the pairing wizard steps (key generation, whitelist request).

## Milestone 4: Home Assistant Integration - Entities & Control
**Goal:** Expose vehicle state and controls to Home Assistant.

- [x] **4.1. Coordinator:** Implement `DataUpdateCoordinator` to manage polling intervals and state updates.
    - `custom_components/tesla_ble/coordinator.py`
- [x] **4.2. Vehicle State Manager:** Port `VehicleStateManager` logic to map protocol data to HA states.
- [x] **4.3. Lock Entity:** Implement `lock.tesla_ble_lock`.
- [x] **4.4. Sensors:** Implement sensors for battery, charging state, etc.
- [x] **4.5. Controls:** Implement switches/buttons for charging, trunk, etc.

## Milestone 5: Optimization & Polish
**Goal:** Ensure reliability and code quality.

- [x] **5.1. Error Handling:** Robust handling of BLE disconnections and protocol errors.
- [x] **5.2. Typing & Linting:** Ensure strict typing (`ty`) and linting (`ruff`) compliance.
- [x] **5.3. Documentation:** Update `README.md` with installation and usage instructions.
