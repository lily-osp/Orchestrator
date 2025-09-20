# MQTT Client Wrapper Documentation

## Overview

The MQTT Client Wrapper provides a robust, production-ready MQTT client for the Orchestrator platform with automatic reconnection, JSON message handling, and topic validation.

## Features

- **Automatic Reconnection**: Exponential backoff reconnection with configurable delays
- **JSON Serialization**: Automatic JSON encoding/decoding of message payloads
- **Topic Validation**: Enforces Orchestrator platform topic naming conventions
- **Error Handling**: Comprehensive error handling and logging
- **Connection Monitoring**: Connection status callbacks and monitoring
- **Thread Safety**: Safe for use in multi-threaded applications

## Requirements Covered

- **2.1**: Asynchronous MQTT-based communication with JSON messages
- **2.3**: Non-blocking communication between layers
- **7.1**: Standardized communication protocols with JSON message formats
- **7.2**: Consistent topic naming conventions

## Quick Start

```python
from mqtt_client import MQTTClientWrapper, MQTTConfig

# Create configuration
config = MQTTConfig(
    broker_host="localhost",
    broker_port=1883,
    client_id="my_device"
)

# Create and connect client
client = MQTTClientWrapper(config)
client.connect()

# Subscribe to commands
def handle_command(message_data):
    print(f"Command: {message_data['payload']}")

client.subscribe("orchestrator/cmd/+", handle_command)

# Publish telemetry data
telemetry = {
    "device_id": "sensor_01",
    "temperature": 25.5,
    "humidity": 60.2
}
client.publish("orchestrator/data/sensor_01", telemetry)
```

## Configuration

### MQTTConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `broker_host` | str | "localhost" | MQTT broker hostname |
| `broker_port` | int | 1883 | MQTT broker port |
| `keepalive` | int | 60 | Connection keepalive interval |
| `client_id` | str | "orchestrator_hal" | Unique client identifier |
| `username` | str | None | MQTT username (optional) |
| `password` | str | None | MQTT password (optional) |
| `max_reconnect_delay` | int | 300 | Maximum reconnection delay (seconds) |
| `base_reconnect_delay` | int | 1 | Base reconnection delay (seconds) |

## Topic Conventions

The Orchestrator platform uses a structured topic hierarchy:

### Command Topics
- Pattern: `orchestrator/cmd/{component}`
- Purpose: Send commands to hardware components
- Examples:
  - `orchestrator/cmd/motors`
  - `orchestrator/cmd/gripper`
  - `orchestrator/cmd/lidar`

### Data Topics
- Pattern: `orchestrator/data/{sensor}`
- Purpose: Publish sensor telemetry data
- Examples:
  - `orchestrator/data/lidar`
  - `orchestrator/data/encoder_left`
  - `orchestrator/data/temperature`

### Status Topics
- Pattern: `orchestrator/status/{subsystem}`
- Purpose: Publish system status updates
- Examples:
  - `orchestrator/status/robot`
  - `orchestrator/status/safety`
  - `orchestrator/status/mission`

## Message Format

All messages use JSON format with automatic timestamp addition:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "device_id": "lidar_01",
  "data": {
    "ranges": [1.2, 1.5, 0.8, 2.1],
    "angles": [0, 90, 180, 270]
  }
}
```

## API Reference

### MQTTClientWrapper Class

#### Methods

##### `connect() -> bool`
Connect to the MQTT broker.

**Returns**: `True` if connection initiated successfully, `False` otherwise.

##### `disconnect()`
Disconnect from the MQTT broker and stop reconnection attempts.

##### `publish(topic: str, payload: dict, qos: int = 0, retain: bool = False) -> bool`
Publish a message to the specified topic.

**Parameters**:
- `topic`: MQTT topic (must follow Orchestrator conventions)
- `payload`: Dictionary to serialize as JSON
- `qos`: Quality of Service level (0, 1, or 2)
- `retain`: Whether to retain the message

**Returns**: `True` if message queued successfully, `False` otherwise.

##### `subscribe(topic_pattern: str, callback: callable, qos: int = 0) -> bool`
Subscribe to topics matching the pattern.

**Parameters**:
- `topic_pattern`: MQTT topic pattern (supports `+` and `#` wildcards)
- `callback`: Function called when messages received
- `qos`: Quality of Service level

**Returns**: `True` if subscription successful, `False` otherwise.

##### `unsubscribe(topic_pattern: str) -> bool`
Unsubscribe from the specified topic pattern.

##### `add_connection_callback(name: str, callback: callable)`
Add a callback for connection status changes.

**Callback signature**: `callback(connected: bool)`

##### `is_connected -> bool`
Property indicating current connection status.

##### `get_status() -> dict`
Get comprehensive client status information.

## Error Handling

The client handles various error conditions gracefully:

- **Connection Loss**: Automatic reconnection with exponential backoff
- **Invalid Topics**: Validation and rejection of malformed topics
- **JSON Errors**: Logging and skipping of malformed JSON messages
- **Callback Errors**: Isolation of callback exceptions to prevent system failure

## Logging

The client uses Python's standard logging module with the logger name `mqtt_client`. Configure logging levels as needed:

```python
import logging
logging.getLogger('mqtt_client').setLevel(logging.DEBUG)
```

## Testing

### Unit Tests
Run the comprehensive unit test suite:
```bash
python -m pytest tests/test_mqtt_client.py -v
```

### Functional Tests
Test with a real MQTT broker:
```bash
python test_mqtt_functional.py
```

### Validation
Run basic validation without broker:
```bash
python validate_mqtt.py
```

## Integration with Orchestrator Platform

The MQTT client is designed to integrate seamlessly with other Orchestrator components:

1. **HAL Service**: Uses the client to publish sensor data and receive commands
2. **Safety System**: Subscribes to sensor data and publishes emergency stops
3. **Node-RED**: Connects to the same broker for control and monitoring
4. **State Management**: Publishes robot status and mission updates

## Performance Considerations

- **Message Rate**: Designed for typical robotics telemetry rates (1-100 Hz)
- **Payload Size**: Optimized for small to medium JSON payloads (< 1KB typical)
- **Memory Usage**: Minimal memory footprint with efficient message handling
- **CPU Usage**: Low CPU overhead with asynchronous processing

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure MQTT broker is running and accessible
2. **Invalid Topic Errors**: Check topic follows `orchestrator/{type}/{component}` pattern
3. **JSON Decode Errors**: Verify message payloads are valid JSON
4. **Callback Exceptions**: Check callback functions handle errors properly

### Debug Mode

Enable debug logging for detailed operation information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

- `paho-mqtt >= 1.6.0`: MQTT client library
- `json`: JSON serialization (built-in)
- `threading`: Reconnection handling (built-in)
- `logging`: Error and debug logging (built-in)