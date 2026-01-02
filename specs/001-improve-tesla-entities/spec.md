# Feature Specification: Improve Tesla Entities

**Feature Branch**: `001-improve-tesla-entities`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "read the reference implementation for the tesla entities and improve it in our solution."

## Clarifications

### Session 2026-01-02
- Q: What is the primary data update strategy relative to vehicle sleep? → A: **Smart Wake Management**: Poll for 11 minutes in wake window, then sleep. Active states (charging/unlocked/user present) override sleep.
- Q: Does "User Present" (FR-004) refer to vehicle state or BLE proximity? → A: **Vehicle Internal State**: Must reflect the car's internal driver-detection flag to avoid keeping the car awake unnecessarily.
- Q: Should the timeout (FR-007) be configurable in UI? → A: **Yes (Options Flow)**: Implement a user-facing Options Flow setting to adjust the unavailability timeout (e.g., for spotty connections).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Charging & Climate Management (Priority: P1)

As a Tesla owner, I want to control and monitor my vehicle's charging and climate systems locally via Home Assistant so that I can automate charging based on solar production and pre-condition the car without cloud latency.

**Why this priority**: Charging and climate are the high-frequency daily use cases that benefit most from local control (reliability/speed).

**Independent Test**:
1. Verify charging controls toggle vehicle charging state.
2. Verify charging metrics (Power, Voltage, Amps) update in real-time.
3. Verify climate controls toggle HVAC system.
4. Verify temperature readings are accurate.

**Acceptance Scenarios**:

1. **Given** vehicle is plugged in, **When** I toggle the Charging control to On, **Then** the vehicle starts charging and status updates to 'Charging'.
2. **Given** basic state, **When** I toggle the Climate control to On, **Then** the HVAC turns on.
3. **Given** charging in progress, **When** I view the charging details, **Then** I see active Voltage, Current, and Power values.

---

### User Story 2 - Vehicle Access & Security Controls (Priority: P2)

As a user, I want to control physical access points (locks, trunks, windows) and security features (Sentry Mode) so that I can manage the vehicle's physical security locally.

**Why this priority**: Access controls are critical but slightly lower frequency than charging logic.

**Independent Test**:
1. Verify vehicle Lock/Unlock commands work.
2. Verify Frunk and Trunk open commands work.
3. Verify Sentry Mode toggle works.
4. Verify Window vent command works.

**Acceptance Scenarios**:

1. **Given** vehicle is locked, **When** I send the Unlock command, **Then** the vehicle unlocks.
2. **Given** vehicle is idle, **When** I send the Open Frunk command, **Then** the Frunk unlatches.
3. **Given** vehicle is parked, **When** I toggle Sentry Mode, **Then** the vehicle enables/disables Sentry Mode.

---

### User Story 3 - Enhanced Telemetry & Monitoring (Priority: P3)

As a user, I want to see detailed vehicle metrics like odometer, various binary states (user present, sleep status), and door states so that I have complete observability of my vehicle.

**Why this priority**: Monitoring data is valuable for dashboards but less critical for control automations.

**Independent Test**:
1. Check Odometer reading matches vehicle.
2. Check presence detection ("User Present") updates.
3. Check status of individual doors/flaps.

**Acceptance Scenarios**:

1. **Given** the integration is running, **When** I view the device details, **Then** I see the accurate Odometer reading.
2. **Given** no one is in the car, **When** I approach the car, **Then** the User Present status changes to Detected.

### Edge Cases

- **Vehicle Asleep**: If the vehicle is asleep, commands should either wake it automatically or fail with a clear "Vehicle Asleep" error (depending on command criticality).
- **BLE Disconnected**: detailed controls should become unavailable or show "Unknown" state when BLE connection is lost.
- **Concurrent Commands**: System should handle rapid succession of commands (e.g. Lock then immediately Unlock) without getting stuck.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide controls for Frunk, Trunk, Charge Port, and Window venting capabilities.
- **FR-002**: System MUST provide switching capabilities for Climate, Sentry Mode, Steering Wheel Heater, Defrost, and Charging.
- **FR-003**: System MUST provide sensors for Odometer, Internal Temperature, External Temperature, Charge Energy Added, Charge Distance Added, and charging statistics (Voltage, Amps).
- **FR-004**: System MUST provide binary status indicators for "User Present" (Vehicle Internal State), "Vehicle Asleep", and, where supported, individual door/flap states.
- **FR-005**: System MUST provide momentary actions for Flash Lights, Honk Horn, Wake Up, and Force Data Update.
- **FR-006**: System MUST utilize a **Smart Wake Management** strategy: active polling occurs only during the 11-minute wake window or when active states (Charging, Unlocked, User Present) are detected; otherwise, polling pauses to allow sleep.
- **FR-007**: All entities MUST report "unavailable" status when the BLE connection is interrupted for a configurable timeout period (exposed via **Options Flow**).

### Key Entities *(include if feature involves data)*

- **VehicleStatus**: Represents locks, closures, and sleep state.
- **ChargeState**: Represents battery level, range, and charging metrics.
- **ClimateState**: Represents temperatures and HVAC status.
- **DriveState**: Represents odometer and movement data.

### Assumptions & Dependencies

- **Assumption**: The user has a working BLE Proxy infrastructure visible to Home Assistant.
- **Assumption**: The target vehicle supports the same BLE protocol command set as the reference implementation.
- **Dependency**: Requires `async_bleAK` or compatible library for encrypted communication.
- **Dependency**: Requires valid key pairing (already handled by Config Flow, but assumed present for entities to work).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the controls available in the ESPHome reference implementation (that are supported by the HA Bluetooth Proxy approach) are exposed to the user.
- **SC-002**: Users can intuit standard Home Assistant domains (Cover, Lock, Switch) for Vehicle functions (e.g. Frunk acts as a Cover).
- **SC-003**: Entity state updates occur within 10 seconds of a BLE advertisement/response being received.
