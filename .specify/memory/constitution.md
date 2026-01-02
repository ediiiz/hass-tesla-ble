<!--
Sync Impact Report:
- Version change: 1.0.0 -> 1.1.0
- Modified principles:
  - V. Code Quality & Standards -> V. Code Quality & Standards (clarify pydantic v3-ready syntax expectations)
- Added sections:
  - Governance: Amendment Procedure
  - Governance: Versioning Policy
  - Governance: Compliance Review Expectations
- Removed sections: None
- Templates requiring updates (✅ updated / ⚠ pending):
  - .specify/templates/plan-template.md: ✅ (No change required; "Constitution Check" remains compatible)
  - .specify/templates/spec-template.md: ✅ (No change required)
  - .specify/templates/tasks-template.md: ✅ (No change required)
  - .specify/templates/agent-file-template.md: ✅ (No change required)
  - .specify/templates/checklist-template.md: ✅ (No change required)
  - .specify/templates/commands/*.md: N/A (no commands templates directory in this repo)
- Follow-up TODOs / deferred placeholders: None
-->

# hass-tesla-ble Constitution
<!-- Governance and Core Principles for the hass-tesla-ble Integration -->

## Core Principles

### I. Context-Driven Development
Every file and function MUST have clear, typed interfaces. We build from the core data models
*outwards* to the Home Assistant interface. Development proceeds from data structures to core
logic, and finally to the HA entity/config flow layer to ensure robust foundations.

### II. Reference Implementation Parity
The `esphome-tesla-ble` (C++) project is the "gold standard" for logic and behavior. We are
porting this logic to Python, keeping strict architectural parity where applicable:

- C++ `SessionManager` → Python `TeslaSessionManager`
- C++ `BLEManager` → Python `TeslaBLEClient`
- C++ `VehicleStateManager` → Python `TeslaVehicleEntity`

### III. Dependency Isolation
The integration MUST be a pure Python implementation capable of running within standard Home
Assistant containers.

- We do NOT rely on the official `tesla-vehicle-command` Go library wrapper or external binaries.
- We use `cryptography` for ECDH/auth and `protobuf` for message serialization.

### IV. Hardware Independence
NO additional hardware (specifically dedicated ESP32 dongles per protocol) should be required if
the user already has standard Home Assistant BLE proxies.

The logic MUST run entirely within Home Assistant's Python environment leveraging the
`homeassistant.components.bluetooth` stack.

### V. Code Quality & Standards
- **Typing**: Strict typing is required (using `ty` or the standard `typing` module).
- **Linting**: All code MUST pass `ruff` linting and formatting.
- **Validation**: Data models and settings MUST use pydantic with v3-ready syntax:
  - Prefer Pydantic v2+ APIs (`model_config = ConfigDict`, `.model_validate()`, `.model_dump()`).
  - Avoid deprecated v1-style APIs (`class Config`, `.parse_obj()`, `.dict()`).

Rationale: A stable, typed, and validated core is required for secure crypto/session logic and to
avoid regressions when integrating with Home Assistant.

## Architecture

### Component Structure
The architecture MUST separate the "Core Library" from the "HA Integration":

1. **Core Library (`custom_components/tesla_ble/core/`)**: Standalone-capable Python logic
   handling Crypto, Proto, and Session State. Independent of HA imports where possible.
2. **HA Integration (`custom_components/tesla_ble/`)**: Standard HA constructs (`ConfigFlow`,
   `Coordinator`, `Entity`) that wrap the Core Library.

## Governance
This Constitution supersedes all other loose practices. Amendments to these principles require a
version bump and documented rationale.

### Amendment Procedure
- Amendments MUST be made via a Pull Request that updates this file.
- The PR MUST include an updated Sync Impact Report (top-of-file HTML comment).
- Any dependent templates and guidance docs MUST be reviewed and updated as needed.

### Versioning Policy
The Constitution uses semantic versioning:

- **MAJOR**: Backward-incompatible governance changes; principle removals; principle redefinitions.
- **MINOR**: New principles/sections or materially expanded guidance that changes expectations.
- **PATCH**: Clarifications, wording fixes, typo fixes, and non-semantic refinements.

### Compliance Review Expectations
- Every feature plan MUST include a "Constitution Check" section mapping work to each principle
  (or documenting justified exceptions).
- Any deliberate principle violations MUST be explicitly documented (e.g., in a plan's complexity
  tracking section) with rationale and mitigation.
- Pull Requests SHOULD be reviewed for principle compliance before merge.

### Compliance
All architectural decisions and Pull Requests must be verified against these principles. Reference
`AGENTS.md` for specific technical context and runtime directives.

**Version**: 1.1.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-02
