# Tasks: Improve Tesla BLE Proxy Integration

**Input**: Design documents from `/specs/001-improve-tesla-ble-proxy/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

## Phase 1: Setup & Protobufs

**Purpose**: Initialize project structure and generate protocol buffers.

- [x] T001 Implement directory structure `custom_components/tesla_ble/core/proto/`
- [x] T002 Generate Python code from `.proto` files into `core/proto/` using `protoc`
- [x] T003 [P] Create `custom_components/tesla_ble/core/models.py` with `TeslaSession` pydantic model

## Phase 2: Foundational (Crypto & Session)

**Purpose**: Core logic implementation required for any operation.

- [x] T004 Implement `TeslaSessionManager` in `core/session_manager.py` (Key generation, ECDH)
- [x] T005 Implement message signing and encryption in `TeslaSessionManager`
- [x] T006 [P] Create unit tests for crypto logic in `tests/test_crypto.py`

## Phase 3: User Story 1 & 2 - Robust Connectivity (Priority: P1)

**Goal**: Connect to vehicle via proxy and maintain link.

### Implementation

- [x] T007 [P] [US1] Implement `TeslaBLEClient` in `core/ble_interface.py` using `bleak_retry_connector`
- [x] T008 [US1] Implement `connect()` and `disconnect()` with state tracking
- [x] T009 [US1] Implement "Always Connected" logic (keep-alive loop)
- [x] T010 [US1] Implement `send_command()` in `TeslaBLEClient` using `SessionManager` for encryption
- [x] T011 [US1] Expose `close_stale_connections_by_address` utility from Yale reference

## Phase 4: User Story 3 - Pairing & Integration (Priority: P2)

**Goal**: Setup wizard with interactive pairing.

### Implementation

- [x] T012 [P] [US3] Create `ConfigFlow` skeleton in `config_flow.py`
- [x] T013 [US3] Implement `async_step_bluetooth` for discovery
- [x] T014 [US3] Implement `TeslaPairingWizard` helper to handle ephemeral pairing connection
- [x] T015 [US3] Implement `async_step_pair` with "Tap Key Card" prompt and polling
- [x] T016 [US3] Save session keys to `ConfigEntry` upon success

## Phase 5: Entities & UI (Priority: P1)

**Goal**: Expose vehicle state to HA.

### Implementation

- [ ] T017 [P] [US1] Create `TeslaVehicleEntity` base class in `entity.py`
- [ ] T018 [US1] Implement `Lock` entity in `lock.py`
- [ ] T019 [US4] Implement Connection/RSSI diagnostic sensors in `sensor.py`
- [ ] T020 [US2] update `manifest.json` with dependencies and requirements
