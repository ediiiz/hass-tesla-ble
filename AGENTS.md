# Agent Context & Directives

## Project Overview
We are building a Home Assistant Custom Component (Integration) named `hass-tesla-ble`.
**Goal:** Control Tesla vehicles locally via Bluetooth Low Energy (BLE) using Home Assistant's existing remote BLE proxy infrastructure.
**Key Constraint:** NO additional hardware (like ESP32s) should be required if the user already has BLE proxies. The logic runs entirely within Home Assistant's Python environment.

## Architecture & Technology Stack
- **Platform:** Home Assistant Custom Component (Integration).
- **Language:** Python 3.12+.
- **Package Manager:** `uv` (for fast, reliable dependency management).
- **Code Quality:**
  - **Typing:** Strict typing with `ty`
  - **Linting:** `ruff` for linting and formatting.
  - **Models:** `pydantic` for robust data validation and settings management.
- **BLE Stack:** `homeassistant.components.bluetooth` (specifically `async_bleAK` client wrappers) to leverage proxies transparently.
- **Protocol:** Tesla Vehicle Command Protocol (Protocol Buffers).
  - We must generate Python code from the `.proto` definitions found in the reference implementation.
  - **Security:** The integration must implement the full cryptographic handshake (ECDH key exchange, authentication) required by Tesla vehicles.

## Development Directives
1.  **Context-Driven Development:** Every file and function must have clear, typed interfaces. We build from the core data models *outwards* to the HA interface.
2.  **Reference Implementation:** The `esphome-tesla-ble` (C++) project is our "gold standard" for logic. We are porting this logic to Python.
    - *Mapping:*
      - `SessionManager` (C++) -> `TeslaSessionManager` (Python)
      - `BLEManager` (C++) -> `TeslaBLEClient` (Python using HA Bluetooth)
      - `VehicleStateManager` (C++) -> `TeslaVehicleEntity` (Python HA Entity)
3.  **Dependency Isolation:** Do NOT rely on the official `tesla-vehicle-command` Go library wrapper if possible. We want a pure Python implementation using `cryptography` for the crypto operations and `protobuf` for message serialization.

## Workflow
1.  **Proto Definition:** Extract `.proto` files from references and generate Python classes.
2.  **Core Library:** Build a standalone-capable Python library (`tesla_ble_core`) within the component that handles:
    - Crypto (Keys, Signatures).
    - Protocol (VCSEC, CarServer messages).
    - Session State (Counters, Epochs).
3.  **HA Integration:** Wrap the core library in standard Home Assistant constructs (`ConfigFlow`, `Coordinator`, `Entity`).

## Critical files
- `custom_components/tesla_ble/manifest.json`: Integration definition.
- `custom_components/tesla_ble/config_flow.py`: Setup & Pairing wizard.
- `custom_components/tesla_ble/core/`: The ported logic (crypto, proto, session).
