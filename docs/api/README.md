# API Documentation

This directory contains API documentation for the Orchestrator Platform.

## Contents

### MQTT API
- Complete MQTT communication protocol: [`../MQTT_REFERENCE.md`](../MQTT_REFERENCE.md)
- Topic structure and message schemas
- Command and telemetry message formats
- Quality of Service guidelines

### HAL API
- Hardware Abstraction Layer interfaces: [`../hal_service/`](../hal_service/)
- Component-specific APIs and usage examples
- Configuration schemas and parameters

### Node-RED API
- Node-RED flow interfaces: [`../node-red/`](../node-red/)
- Dashboard API and customization
- Flow development guidelines

## Auto-Generated Documentation

This directory is reserved for auto-generated API documentation from code comments and docstrings.

### Generating API Documentation

To generate API documentation from code:

```bash
# Generate Python API docs (using pydoc or sphinx)
python -m pydoc -w hal_service

# Generate Node-RED flow documentation
# (Custom scripts in development)
```

### API Documentation Standards

- **Docstring Format**: Google-style docstrings for Python
- **Type Annotations**: Full type hints for all public APIs
- **Examples**: Practical usage examples for all public methods
- **Error Handling**: Documented exceptions and error conditions

## API Versioning

The Orchestrator Platform uses semantic versioning for API compatibility:

- **Major Version**: Breaking API changes
- **Minor Version**: New features, backward compatible
- **Patch Version**: Bug fixes, backward compatible

Current API version: `1.0.0`

## API Reference Quick Links

### Core APIs
- [MQTT Communication Protocol](../MQTT_REFERENCE.md)
- [HAL Base Classes](../hal_service/README_MOTOR.md)
- [Configuration Management](../hal_service/README_LOGGING.md)

### Component APIs
- [Motor Controller API](../hal_service/README_MOTOR.md)
- [Sensor APIs](../hal_service/README_ENCODER.md)
- [Safety System API](../hal_service/README_SAFETY.md)

### Integration APIs
- [Node-RED Integration](../node-red/README.md)
- [Dashboard API](../node-red/README_DASHBOARD_UI.md)
- [Mission Control API](../node-red/MISSION_SEQUENCER_IMPLEMENTATION.md)