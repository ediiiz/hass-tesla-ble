# Implementation Plan: Improve Tesla BLE Proxy Integration

**Branch**: `001-improve-tesla-ble-proxy` | **Date**: 2026-01-02 | **Spec**: [specs/001-improve-tesla-ble-proxy/spec.md](specs/001-improve-tesla-ble-proxy/spec.md)
**Input**: Feature specification from `/specs/001-improve-tesla-ble-proxy/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature aims to improve the robustness and user experience of the `hass-tesla-ble` integration by leveraging Home Assistant's Bluetooth proxy infrastructure. The primary focus is on reliable connectivity (User Story 1), instant command response (User Story 2), and a seamless pairing process (User Story 3). We will adopt best practices from the Yale Access Bluetooth integration reference implementation, specifically regarding BLE client management, stale connection handling, and config flow patterns.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: 
- `homeassistant.components.bluetooth` (Bluetooth stack)
- `bleak_retry_connector` (Connection reliability)
- `cryptography` (ECDH/Auth)
- `protobuf` (Tesla Protocol)
- `pydantic` (Data models)
**Storage**: Home Assistant Config Entries (JSON)
**Testing**: `pytest` with `pytest-homeassistant-custom-component`
**Target Platform**: Home Assistant (OS/Container/Core)
**Project Type**: Home Assistant Custom Component
**Performance Goals**: <2s command latency in "Always Connected" mode. Reconnection within 30s of availability.
**Constraints**: Pure Python, no additional hardware (ESP32 dongles), must run in standard HA environment.
**Scale/Scope**: Supports multiple vehicles, high reliability for critical actions (unlock/start).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Context-Driven Development**: Plan builds from data models (`TeslaSessionManager`) to HA entities.
- [x] **II. Reference Implementation Parity**: Adopts `esphome-tesla-ble` logic structure and Yale BLE integration connection patterns.
- [x] **III. Dependency Isolation**: pure Python implementation using `cryptography` and `protobuf`. No external Go binaries.
- [x] **IV. Hardware Independence**: Uses `homeassistant.components.bluetooth` to work with any proxy.
- [x] **V. Code Quality & Standards**: Enforces `ty`, `ruff`, and `pydantic`.

## Project Structure

### Documentation (this feature)

```text
specs/001-improve-tesla-ble-proxy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
custom_components/tesla_ble/
├── __init__.py
├── manifest.json
├── config_flow.py          # Pairing logic (Yalexs reference)
├── coordinator.py          # DataUpdateCoordinator
├── core/
│   ├── __init__.py
│   ├── ble_interface.py    # TeslaBLEClient (Bleak wrapper)
│   ├── crypto.py           # Keys & Signatures
│   ├── protocol.py         # VCSEC/Protobuf handling
│   ├── session_manager.py  # Auth state machine
│   └── proto/              # Generated protobuf classes
├── entity.py               # Base entity
├── lock.py                 # Lock entity
├── binary_sensor.py
└── sensor.py
```

**Structure Decision**: Standard Home Assistant Custom Component structure with a dedicated `core/` subdirectory for library-agnostic logic, separating the "driver" from the "integration".

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | | |
