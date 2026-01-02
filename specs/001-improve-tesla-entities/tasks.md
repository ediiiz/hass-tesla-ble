# Tasks: Improve Tesla Entities

> **Feature**: improve-tesla-entities
> **Status**: Planned

## Phase 1: Setup
*(Project initialization and environment preparation)*

- [ ] T001 Verify project structure and prerequisites
- [ ] T002 Verify proto definitions and core library availability in `custom_components/tesla_ble/core/`

## Phase 2: Foundational
*(Blocking prerequisites for all user stories: Smart Wake & Options Flow)*

**Goal**: Establish the "Smart Wake" polling infrastructure and user-configurable timeouts required by all entities.

- [ ] T003 **[P]** Implement Options Flow for timeout configuration in `custom_components/tesla_ble/config_flow.py`
- [ ] T004 Implement Smart Wake Management polling logic in `custom_components/tesla_ble/coordinator.py`
- [ ] T005 Implement unavailability timeout logic in `custom_components/tesla_ble/entity.py`

## Phase 3: User Story 1 - Core Charging & Climate Management (P1)
*(High-frequency daily control: Charging & HVAC)*

**Goal**: Enable local control of Charging and Climate systems with real-time feedback.
**Independent Test**: Verify Climate toggle turns HVAC on; Verify Charging toggle starts charging; Verify Temp/Power sensors update.

- [ ] T006 **[US1]** Add ClimateState and ChargeState models in `custom_components/tesla_ble/core/models.py`
- [ ] T007 **[US1]** Update data parsing logic for Climate/Charge in `custom_components/tesla_ble/coordinator.py`
- [ ] T008 **[US1]** Create Climate Entity base in `custom_components/tesla_ble/climate.py`
- [ ] T009 **[P]** **[US1]** Implement Charging, Defrost, and Steering Wheel Heater switches in `custom_components/tesla_ble/switch.py`
- [ ] T010 **[P]** **[US1]** Implement Temperature and Charging Power sensors in `custom_components/tesla_ble/sensor.py`
- [ ] T011 **[US1]** Add translations for Climate and Charge entities in `custom_components/tesla_ble/translations/en.json`

## Phase 4: User Story 2 - Vehicle Access & Security Controls (P2)
*(Physical access and security management)*

**Goal**: Enable control of locks, frunk/trunk, windows, and security modes.
**Independent Test**: Verify Lock/Unlock; Verify Frunk/Trunk open; Verify Sentry Mode toggle; Verify Window vent.

- [ ] T012 **[US2]** Add VehicleStatus model for locks/doors in `custom_components/tesla_ble/core/models.py`
- [ ] T013 **[US2]** Update data parsing logic for Vehicle Status in `custom_components/tesla_ble/coordinator.py`
- [ ] T014 **[US2]** Create Cover Entity for Frunk, Trunk, Windows, Charge Port in `custom_components/tesla_ble/cover.py`
- [ ] T015 **[P]** **[US2]** Update Lock Entity implementation in `custom_components/tesla_ble/lock.py`
- [ ] T016 **[P]** **[US2]** Implement Sentry Mode switch in `custom_components/tesla_ble/switch.py`
- [ ] T017 **[US2]** Add translations for Access and Security entities in `custom_components/tesla_ble/translations/en.json`

## Phase 5: User Story 3 - Enhanced Telemetry & Monitoring (P3)
*(Detailed vehicle metrics and binary states)*

**Goal**: Provide full observability including odometer, presence detection, and granular door states.
**Independent Test**: Verify Odometer reading; Verify User Present binary sensor; Verify Flap states.

- [ ] T018 **[US3]** Add DriveState model for Odometer in `custom_components/tesla_ble/core/models.py`
- [ ] T019 **[US3]** Update data parsing logic for Telemetry/DriveState in `custom_components/tesla_ble/coordinator.py`
- [ ] T020 **[P]** **[US3]** Implement Binary Sensors for User Present, Vehicle Asleep, and Door States in `custom_components/tesla_ble/binary_sensor.py`
- [ ] T021 **[P]** **[US3]** Implement Odometer sensor in `custom_components/tesla_ble/sensor.py`
- [ ] T022 **[P]** **[US3]** Implement Button entities for Flash Lights, Honk Horn, Wake Up in `custom_components/tesla_ble/button.py`
- [ ] T023 **[US3]** Add translations for Telemetry entities in `custom_components/tesla_ble/translations/en.json`

## Phase 6: Polish
*(Refinement and standardization)*

- [ ] T024 Review and finalize string keys in `custom_components/tesla_ble/strings.json`
- [ ] T025 Run full linting and typing checks across `custom_components/tesla_ble/`

## Dependencies

1. **Foundational Phase** (Coordinator, Config Flow) must complete before **US1**.
2. **US1**, **US2**, **US3** are largely independent but rely on the updated Coordinator/Models.
3. **US1** (Charging/Climate) is P1 and should be prioritized.

## Parallel Execution Examples

- **Phase 3 (US1)**: While one developer implements `climate.py` (T008), another can implement the switches in `switch.py` (T009) and sensors in `sensor.py` (T010).
- **Phase 4 (US2)**: `lock.py` updates (T015) and Sentry Mode in `switch.py` (T016) can be built in parallel with the new `cover.py` (T014).
- **Phase 5 (US3)**: Binary sensors (T020), Odometer (T021), and Buttons (T022) can all be implemented in parallel once `models.py` and `coordinator.py` are updated.

## Implementation Strategy

1. **MVP (Phase 3)**: Deliver a working integration that handles the most critical daily functions: Climate and Charging. This proves the core "Smart Wake" and "Control" loop.
2. **Security (Phase 4)**: Add physical access layers next.
3. **Observability (Phase 5)**: Enrich the experience with full telemetry.
