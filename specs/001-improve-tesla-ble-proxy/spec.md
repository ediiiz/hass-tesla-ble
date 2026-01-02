# Feature Specification: Improve Tesla BLE Proxy Integration

**Feature Branch**: `001-improve-tesla-ble-proxy`  
**Created**: 2026-01-02  
**Status**: Draft  
**Input**: User description: "reaad the reference bt implementation from the yale bt lock for homeassistant and make a detailed plan on how to improve our tesla ble integration! It uses the best pratices on how to use remote bt proxy to connect to a device and how to connect."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Robust Proxy Connectivity (Priority: P1)

As a Home Assistant user with Bluetooth proxies, I want the Tesla integration to reliably connect to my vehicle via any available proxy without needed dedicated hardware, so that I can control my car even if the HA server is far away.

**Why this priority**: Core functionality request. The integration currently lacks robust lifecycle management for proxies, leading to flaky connections.

**Independent Test**: Remove HA server from direct BLE range of the car, keep a proxy in range. Reload integration. Entities should become available and commands should work.

**Acceptance Scenarios**:

1. **Given** a visible Tesla vehicle nearby a Bluetooth proxy and HA startup, **When** the integration loads, **Then** it should successfully connect via the proxy and entities should be available.
2. **Given** a connected vehicle, **When** the proxy goes offline or the car moves out of range, **Then** all entities should update to "Unavailable".
3. **Given** a vehicle that comes back into range, **When** an advertisement is seen, **Then** the system should automatically reconnect/restore availability.

---

### User Story 2 - Instant Command Response (Always-Connected) (Priority: P1)

As a user, I want the integration to maintain a persistent connection to the car by default, so that commands like "Unlock" happen instantly without waiting for a connection handshake every time.

**Why this priority**: Improves user experience significantly by reducing latency for critical actions.

**Independent Test**: Configure integration with "Always Connected" enabled (default). Monitor connection status to ensure it remains open during idle periods.

**Acceptance Scenarios**:

1. **Given** the integration is configured (default), **When** no commands are being sent, **Then** the bluetooth connection remains active ("Always Connected").
2. **Given** the integration is configured for "Connect on Demand", **When** idle, **Then** the connection disconnects after a timeout/poll cycle.
3. **Given** an active connection, **When** a "Lock" command is sent, **Then** it executes immediately without a "Connecting..." delay.

---

### User Story 3 - Pairing Feedback (Priority: P2)

As a user setting up the integration, I want the pairing wizard to automatically detect when the car has accepted my key, so I don't have to guess when to click "Next".

**Why this priority**: improving the setup experience reduces support burden and user frustration.

**Independent Test**: Run through the config flow. Tap the key card on the console. The wizard should auto-advance.

**Acceptance Scenarios**:

1. **Given** the pairing step in config flow, **When** I tap my key card on the center console and the car accepts the key, **Then** the wizard automatically advances to the success screen.
2. **Given** the pairing step, **When** no response is received within the timeout, **Then** a "Confirm Manual" button becomes available/prominent.

---

### User Story 4 - Connection Diagnostics (Priority: P3)

As a user troubleshooting range issues, I want to see diagnostic entities for signal strength (RSSI) and connection source, so I can optimize my proxy placement.

**Why this priority**: Helps advanced users and reduces "it doesn't work" bug reports by providing self-help data.

**Independent Test**: Inspect the new Diagnostic entities on the device page.

**Acceptance Scenarios**:

1. **Given** a connected vehicle, **When** I view the device diagnostics, **Then** I see "RSSI" (Signal Strength) and "Connection Source" (e.g., "proxy", "local").

---

### Edge Cases

- **Startup without Device**: If the car is not in range during startup, the setup should not fail permanently but wait or initialize in a "Waiting" state.
- **Stale Connections**: If a previous session crashed, the system must forcefully clean up existing connections before attempting a new one to avoid "Busy" errors.
- **Auth Revocation**: If the user removes the key from the car screen, the integration should detect the auth failure and mark entities unavailable or request re-authentication.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST register an advertisement listener to detect packets from the specific Tesla VIN/MAC.
- **FR-002**: System MUST accurately track when the device leaves BLE range and becomes unavailable.
- **FR-003**: System MUST implement a "stale connection cleaner" that attempts to disconnect any existing client for the target address before a new connection attempt.
- **FR-004**: System MUST by default maintain a persistent BLE connection ("Always Connected" mode).
- **FR-005**: System MUST provide a configuration option to disable "Always Connected" (switch to "Connect on Demand" mode).
- **FR-006**: Setup process MUST enter a recoverable retry state if the device is not found during initial load, allowing the system to retry later.
- **FR-007**: Pairing flow MUST listen for the security confirmation message from the car to auto-advance the wizard.
- **FR-008**: System MUST de-duplicate notification callbacks to ensure only one listener is active per characteristic.
- **FR-009**: System MUST expose Diagnostic entities for: RSSI, Last Seen Timestamp, Connection Source.
- **FR-010**: System MUST mark entities as "Unavailable" if authentication fails or the BLE device is not seen.

### Key Entities *(include if feature involves data)*

- **BLE Client Wrapper**: The unified wrapper handles connection logic.
- **Session Manager**: Manages the crypto state and authentication.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When "Always Connected" is active, connection drops are automatically re-established within 30 seconds of the device being available.
- **SC-002**: Latency for commands (e.g., Lock) is under 2 seconds when in "Always Connected" mode (excluding car mechanics).
- **SC-003**: Pairing process successfully auto-advances upon key acceptance in 90% of attempts (network conditions permitting).
- **SC-004**: System logs RSSI and Connection Source correctly for 100% of connections.
