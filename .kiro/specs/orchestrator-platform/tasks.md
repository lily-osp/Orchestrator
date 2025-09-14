# Project Orchestrator: Detailed Implementation Plan

**Last Updated:** September 14, 2025

This document provides a detailed, phased breakdown of all tasks required to implement the Orchestrator robotics control platform, following a hierarchical checklist format.

---

### **Phase 1: Foundation & Core Services (Sprint 1-2)**
**Goal:** Establish the project's skeleton, including the core communication, configuration, and foundational code structures.

- [x] **1. Setup Project Monorepo & CI/CD (FND-01)**
  - Create Git repo with directories: `hal_service`, `node_red_config`, `docs`, `tests`.
  - Setup a basic CI pipeline (e.g., GitHub Actions) for code linting and running tests.
  - **Priority:** Critical
  - **Effort (Days):** 1
  - **Dependencies:** None
  - *Requirements: 6.1, 6.4*

- [x] **2. Implement HAL Base Classes (FND-02)**
  - Define abstract base classes in Python: `Device`, `Sensor`, `Actuator`.
  - Define core method signatures (`initialize`, `stop`, `read_data`, etc.) for the interfaces.
  - **Priority:** Critical
  - **Effort (Days):** 2
  - **Dependencies:** FND-01
  - *Requirements: 1.1, 1.3, 6.2*

- [x] **3. Develop MQTT Client Wrapper (FND-03)**
  - Create a robust Python class to manage the Mosquitto connection.
  - Implement automatic reconnection logic with exponential backoff.
  - Handle JSON serialization/deserialization and topic validation.
  - **Priority:** High
  - **Effort (Days):** 3
  - **Dependencies:** FND-01
  - *Requirements: 2.1, 2.3, 7.1, 7.2*

- [x] **4. Define Configuration Service (FND-04)**
  - Create a system to load device parameters (GPIO pins, I2C addresses) from a `config.yaml` file.
  - Implement schema validation (e.g., using Pydantic) for the configuration file.
  - **Priority:** High
  - **Effort (Days):** 2
  - **Dependencies:** FND-01
  - *Requirements: 6.1, 6.4*

- [x] **5. Implement Structured Logging Service (FND-05)**
  - Configure centralized logging (outputting as JSON) for all Python services.
  - Standardize log levels and message formats for easy parsing and monitoring.
  - **Priority:** Medium
  - **Effort (Days):** 2
  - **Dependencies:** FND-01
  - *Requirements: 6.1, 7.4*

---

### **Phase 2: Core Hardware & Safety Implementation (Sprint 3-4)**
**Goal:** Implement the most critical hardware interfaces and the essential safety subsystem.

- [x] **6. Implement MotorController Class (HAL-01)**
  - Create `MotorController` inheriting from the `Actuator` base class.
  - Implement motor control via GPIO and PWM.
  - Subscribe to `orchestrator/cmd/motors` for commands.
  - Use encoder feedback for precise distance and rotation control.
  - **Priority:** Critical
  - **Effort (Days):** 4
  - **Dependencies:** FND-02, FND-03, FND-04
  - *Requirements: 1.1, 1.2, 1.3, 2.2*

- [x] **7. Implement EncoderSensor Class (HAL-02)**
  - Create `EncoderSensor` inheriting from the `Sensor` base class.
  - Implement logic to read wheel encoders via GPIO interrupts.
  - Publish cumulative distance, velocity, and tick counts.
  - **Priority:** High
  - **Effort (Days):** 3
  - **Dependencies:** FND-02, FND-03, FND-04
  - *Requirements: 1.1, 1.2, 1.3, 2.2*

- [x] **8. Implement LidarSensor Class (HAL-03)**
  - Create `LidarSensor` inheriting from the `Sensor` base class.
  - Implement communication with the LiDAR via its specific SDK (UART/USB).
  - Continuously scan and publish `LidarScan` data objects to `orchestrator/data/lidar`.
  - **Priority:** Critical
  - **Effort (Days):** 4
  - **Dependencies:** FND-02, FND-03, FND-04
  - *Requirements: 1.1, 1.2, 1.3, 5.1, 5.2*

- [x] **9. Develop HAL Orchestration Service (HAL-04)**
  - Create the main `hal_service.py` script.
  - This service will initialize and manage all hardware device instances based on the `config.yaml`.
  - Implement graceful shutdown procedures to safely stop all hardware.
  - **Priority:** High
  - **Effort (Days):** 2
  - **Dependencies:** HAL-01, HAL-02, HAL-03
  - *Requirements: 1.4, 6.3*

- [x] **10. Develop Standalone Safety Subsystem (SAF-01)**
  - Create a dedicated, high-priority Python process for safety monitoring.
  - This process subscribes directly to sensor data (e.g., `orchestrator/data/lidar`).
  - If an obstacle is detected, it publishes an immediate override command to `orchestrator/cmd/estop`.
  - **Priority:** Critical
  - **Effort (Days):** 3
  - **Dependencies:** FND-03, HAL-03
  - *Requirements: 5.1, 5.2, 5.3, 5.4*

- [x] **11. Develop State Management Service (STA-01)**
  - Create a service that subscribes to encoder data to perform odometry calculations.
  - Track the robot's estimated X/Y position and heading.
  - Publish the official robot state to `orchestrator/status/robot`.
  - **Priority:** High
  - **Effort (Days):** 3
  - **Dependencies:** FND-03, HAL-02
  - *Requirements: 4.3, 5.4*

---

### **Phase 3: Control Layer & User Interface (Sprint 5-6)**
**Goal:** Build the Node-RED flows and web dashboard for user control and monitoring.

- [x] **12. Setup Node-RED Environment (CTL-01)**
  - Install Node-RED and the `node-red-dashboard` plugin.
  - Configure the MQTT broker connection nodes.
  - **Priority:** High
  - **Effort (Days):** 1
  - **Dependencies:** FND-03
  - *Requirements: 3.1, 3.3*

- [x] **13. Build Node-RED Command Flows (CTL-02)**
  - Create flows that translate UI actions (button clicks, slider inputs) into formatted MQTT JSON commands.
  - Implement input validation for all command parameters within the flows.
  - **Priority:** High
  - **Effort (Days):** 3
  - **Dependencies:** CTL-01, STA-01
  - *Requirements: 3.1, 3.3, 7.1*

- [x] **14. Build Node-RED Telemetry Flows (CTL-03)**
  - Create flows that subscribe to all `.../data/*` and `.../status/*` topics.
  - Process and format incoming data for display in the various dashboard widgets.
  - **Priority:** High
  - **Effort (Days):** 4
  - **Dependencies:** CTL-01, STA-01
  - *Requirements: 3.4, 4.4, 2.2*

- [x] **15. Develop Web Dashboard UI (CTL-04)**
  - Design and build the dashboard UI with a dark theme and `glassmorphism` elements.
  - Add controls (Start, Stop, E-Stop), status displays (position, logs), and mission parameters.
  - Implement a real-time LiDAR visualization canvas.
  - **Priority:** High
  - **Effort (Days):** 5
  - **Dependencies:** CTL-02, CTL-03
  - *Requirements: 4.1, 4.2, 4.3, 4.4*

- [x] **16. Implement Mission Sequencer Flow (CTL-05)**
  - Create a complex flow that can execute a sequence of commands from a JSON array input.
  - This flow will manage the mission state (`in_progress`, `completed`, `failed`) and step progression.
  - **Priority:** Medium
  - **Effort (Days):** 4
  - **Dependencies:** CTL-02, STA-01
  - *Requirements: 3.2, 3.4, 6.4, 7.3*

---

### **Phase 4: Testing, Deployment & Documentation (Sprint 7-8)**
**Goal:** Ensure the system is robust, reliable, and maintainable through comprehensive testing and clear documentation.

- [ ] **17. Create Hardware Simulation (Mock HAL) (TST-01)**
  - Build a mock Python library that mimics the HAL's MQTT interface.
  - This will simulate fake sensor data and acknowledge commands, allowing for UI/control development without physical hardware.
  - **Priority:** High
  - **Effort (Days):** 4
  - **Dependencies:** Phase 1, Phase 2
  - *Requirements: 1.4, 6.2*

- [ ] **18. Write Unit & Integration Tests (TST-02)**
  - Write `pytest` unit tests for all individual HAL classes.
  - Create integration tests that validate the full command loop (MQTT -> HAL -> MQTT).
  - Add these tests to the CI pipeline from FND-01.
  - **Priority:** High
  - **Effort (Days):** 5
  - **Dependencies:** TST-01
  - *Requirements: 2.3, 5.4, 7.1, 7.4*

- [ ] **19. Develop Deployment Scripts (DEP-01)**
  - Create scripts (e.g., Ansible, Shell) to automate the setup of a new Raspberry Pi.
  - Scripts should install all dependencies, configure the MQTT broker, and set up services.
  - Configure the Python HAL and Node-RED to run automatically as `systemd` services.
  - **Priority:** Medium
  - **Effort (Days):** 3
  - **Dependencies:** HAL-04, CTL-01
  - *Requirements: 6.1, 6.4*

- [ ] **20. Write Project Documentation (DOC-01)**
  - Create a detailed `README.md` with setup instructions for developers.
  - Write a user guide explaining how to operate the robot via the dashboard.
  - Document the complete MQTT topic structure and all message schemas.
  - **Priority:** Medium
  - **Effort (Days):** 3
  - **Dependencies:** All Phases
  - *Requirements: 6.1, 6.4*