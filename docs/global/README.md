# Documentation

This directory contains comprehensive documentation for the Orchestrator platform.

## Contents

### User Documentation
- [`USER_GUIDE.md`](USER_GUIDE.md) - Complete user guide for operating the robot via dashboard
- [`MQTT_REFERENCE.md`](MQTT_REFERENCE.md) - Complete MQTT topic structure and message schemas
- [`SYSTEM_ACCESS_GUIDE.md`](SYSTEM_ACCESS_GUIDE.md) - System access and configuration guide
- [`DEPLOYMENT.md`](DEPLOYMENT.md) - Deployment and installation instructions

### Technical Documentation
- [`node_red_config.md`](node_red_config.md) - Node-RED configuration and setup
- [`orchestrator_dashboard.html`](orchestrator_dashboard.html) - Dashboard interface documentation

### Component Documentation
- [`hal_service/`](hal_service/) - Hardware Abstraction Layer component documentation
  - [`README_ENCODER.md`](hal_service/README_ENCODER.md) - Encoder sensor interface
  - [`README_LIDAR.md`](hal_service/README_LIDAR.md) - LiDAR sensor interface
  - [`README_LOGGING.md`](hal_service/README_LOGGING.md) - Logging service
  - [`README_MOTOR.md`](hal_service/README_MOTOR.md) - Motor controller interface
  - [`README_MQTT.md`](hal_service/README_MQTT.md) - MQTT client implementation
  - [`README_SAFETY.md`](hal_service/README_SAFETY.md) - Safety monitoring system
  - [`README_STATE_MANAGER.md`](hal_service/README_STATE_MANAGER.md) - State management service

### Implementation Documentation
- [`node-red/`](node-red/) - Node-RED implementation documentation
  - [`README.md`](node-red/README.md) - Node-RED overview and setup
  - [`COMMAND_FLOWS_README.md`](node-red/COMMAND_FLOWS_README.md) - Command flow implementation
  - [`TELEMETRY_FLOWS_README.md`](node-red/TELEMETRY_FLOWS_README.md) - Telemetry flow implementation
  - [`DASHBOARD_UI_IMPLEMENTATION_SUMMARY.md`](node-red/DASHBOARD_UI_IMPLEMENTATION_SUMMARY.md) - Dashboard UI details
  - [`MISSION_SEQUENCER_IMPLEMENTATION.md`](node-red/MISSION_SEQUENCER_IMPLEMENTATION.md) - Mission sequencer
  - [`README_DASHBOARD_UI.md`](node-red/README_DASHBOARD_UI.md) - Dashboard UI guide
  - [`TELEMETRY_IMPLEMENTATION_SUMMARY.md`](node-red/TELEMETRY_IMPLEMENTATION_SUMMARY.md) - Telemetry implementation
  - [`IMPLEMENTATION_SUMMARY.md`](node-red/IMPLEMENTATION_SUMMARY.md) - Overall implementation summary

### Development Documentation
- [`mock-hal/`](mock-hal/) - Mock hardware abstraction layer documentation
  - [`README.md`](mock-hal/README.md) - Mock HAL implementation and usage

### Architecture Documentation
- [`api/`](api/) - API documentation (auto-generated)
- [`architecture/`](architecture/) - System architecture diagrams and documentation

## Quick Links

### For Users
- [**User Guide**](USER_GUIDE.md) - Start here for operating the robot
- [**MQTT Reference**](MQTT_REFERENCE.md) - Complete communication protocol reference
- [**System Access Guide**](SYSTEM_ACCESS_GUIDE.md) - System configuration and access

### For Developers
- [**HAL Service Documentation**](hal_service/) - Hardware abstraction layer components
- [**Node-RED Documentation**](node-red/) - Control interface implementation
- [**Mock HAL Documentation**](mock-hal/) - Development and testing tools

### For Deployment
- [**Deployment Guide**](DEPLOYMENT.md) - Installation and deployment instructions
- [**Node-RED Configuration**](node_red_config.md) - Node-RED setup and configuration

## Documentation Standards

All documentation follows these standards:

- **Markdown Format**: All documentation uses Markdown (.md) format
- **Clear Structure**: Hierarchical organization with table of contents
- **Code Examples**: Practical examples with syntax highlighting
- **Cross-references**: Links between related documentation
- **Version Control**: Documentation versioned with code changes

## Contributing to Documentation

When adding or updating documentation:

1. **Follow Structure**: Use the established directory structure
2. **Update Index**: Add new documents to this README
3. **Cross-reference**: Link related documents
4. **Test Examples**: Verify all code examples work
5. **Review Changes**: Have documentation changes reviewed

## Getting Help

If you can't find what you're looking for:

1. Check the [User Guide](USER_GUIDE.md) for operational questions
2. Review [Component Documentation](hal_service/) for technical details
3. Consult [MQTT Reference](MQTT_REFERENCE.md) for communication protocols
4. Check the main [README.md](../README.md) for project overview