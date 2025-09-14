# Structured Logging Service

The Orchestrator platform includes a comprehensive structured logging service that provides centralized logging with JSON output format, standardized log levels, and consistent message formatting for easy parsing and monitoring.

## Features

- **JSON Output Format**: All logs are output in structured JSON format for easy parsing by log aggregation tools
- **Standardized Message Formats**: Consistent message structure across all components
- **Context Management**: Support for persistent and temporary context fields
- **Device-Specific Logging**: Specialized loggers for hardware devices with device-specific context
- **Service-Specific Logging**: Specialized loggers for services with service-specific context
- **Performance Metrics**: Built-in support for logging performance metrics
- **MQTT Event Logging**: Standardized logging for MQTT communication events
- **Thread-Safe**: Safe for use in multi-threaded applications
- **Configurable**: Flexible configuration for log levels, output destinations, and formatting

## Quick Start

### Basic Usage

```python
from hal_service.logging_service import get_logger, configure_logging

# Configure logging
configure_logging({
    "level": "INFO",
    "format": "json",
    "console_output": True,
    "file_output": True,
    "log_dir": "logs"
})

# Get a logger
logger = get_logger("my_component")

# Log messages
logger.info("System started", version="1.0.0")
logger.warning("Configuration issue detected", config_file="config.yaml")
logger.error("Operation failed", error_code="E001")
```

### Device Logging

```python
from hal_service.logging_service import get_logging_service

service = get_logging_service()
device_logger = service.get_device_logger("motor_01")

# Log device events
device_logger.log_device_event("motor_01", "initialization", "success", voltage=12.5)
device_logger.log_device_event("motor_01", "command_received", "success", 
                              command="move_forward", distance=100)

# Log performance metrics
device_logger.log_performance_metric("motor_speed", 1.5, "m/s")
```

### Service Logging

```python
service_logger = service.get_service_logger("mqtt_client")

# Log MQTT events
service_logger.log_mqtt_event("orchestrator/cmd/motor", "subscribe", "success")
service_logger.log_mqtt_event("orchestrator/data/lidar", "publish", "success", 
                             message_size=1024)
```

## Configuration

The logging service can be configured with the following options:

```python
config = {
    "level": "INFO",           # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "json",          # Output format: json or text
    "console_output": True,    # Enable console logging
    "file_output": True,       # Enable file logging
    "log_dir": "logs",         # Directory for log files
    "max_log_size": 10485760,  # Maximum log file size in bytes (10MB)
    "backup_count": 5          # Number of backup log files to keep
}
```

## Context Management

### Persistent Context

Set context fields that persist across all log messages:

```python
logger.set_context(device_type="motor", max_speed=2.0)
logger.info("Motor started")  # Will include device_type and max_speed

logger.clear_context()  # Remove all persistent context
```

### Temporary Context

Use context managers for temporary context fields:

```python
with logger.context(operation="calibration", phase="startup"):
    logger.info("Starting calibration")  # Includes operation and phase
    logger.info("Calibration complete")  # Includes operation and phase

logger.info("Normal operation")  # No temporary context
```

## JSON Output Format

All log messages are output in a standardized JSON format:

```json
{
  "timestamp": "2025-09-14T13:55:44.552639",
  "level": "INFO",
  "logger": "orchestrator.device.motor_01",
  "message": "Device event: initialization",
  "module": "logging_service",
  "function": "_log_with_context",
  "line": 144,
  "process": {
    "pid": 400515,
    "name": "MainProcess"
  },
  "thread": {
    "id": 140484470731008,
    "name": "MainThread"
  },
  "extra": {
    "device_id": "motor_01",
    "component_type": "device",
    "event_type": "initialization",
    "event_status": "success",
    "voltage": 12.5,
    "component": "hal_service",
    "service": "device.motor_01",
    "platform": "orchestrator"
  }
}
```

## Standardized Event Types

### Device Events

```python
logger.log_device_event(device_id, event_type, status, **context)
```

Common event types:
- `initialization` - Device startup and initialization
- `command_received` - Command received from MQTT
- `command_executed` - Command execution completed
- `data_published` - Sensor data published to MQTT
- `status_change` - Device status changed
- `error` - Device error occurred

### MQTT Events

```python
logger.log_mqtt_event(topic, action, status, **context)
```

Common actions:
- `publish` - Message published to topic
- `subscribe` - Subscribed to topic
- `receive` - Message received from topic
- `connect` - Connected to broker
- `disconnect` - Disconnected from broker

### Performance Metrics

```python
logger.log_performance_metric(metric_name, value, unit, **context)
```

Common metrics:
- `cpu_usage` - CPU utilization percentage
- `memory_usage` - Memory usage in bytes
- `sensor_read_time` - Time to read sensor data
- `command_execution_time` - Time to execute commands
- `message_throughput` - Messages per second

## Integration with HAL Components

The logging service is automatically integrated with HAL base classes:

```python
from hal_service import Device, Sensor, Actuator

class MyMotor(Actuator):
    def __init__(self, device_id, mqtt_client, config=None):
        super().__init__(device_id, mqtt_client, config)
        # self.logger is automatically available
        
    def execute_command(self, command):
        self.logger.log_device_event(
            self.device_id, 
            "command_received", 
            "success",
            command=command.get("action")
        )
        # ... execute command
```

## Log Analysis

The structured JSON format makes it easy to analyze logs with tools like:

- **jq**: Command-line JSON processor
- **ELK Stack**: Elasticsearch, Logstash, and Kibana
- **Fluentd**: Log collector and processor
- **Grafana**: Visualization and monitoring
- **Python scripts**: Custom analysis with json module

### Example jq queries:

```bash
# Get all error messages
cat logs/orchestrator.log | jq 'select(.level == "ERROR")'

# Get device events for motor_01
cat logs/orchestrator.log | jq 'select(.extra.device_id == "motor_01")'

# Get performance metrics
cat logs/orchestrator.log | jq 'select(.extra.metric_type == "performance")'

# Count messages by level
cat logs/orchestrator.log | jq -r '.level' | sort | uniq -c
```

## Best Practices

1. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General operational messages
   - WARNING: Something unexpected happened but system continues
   - ERROR: Serious problem occurred
   - CRITICAL: System cannot continue

2. **Include relevant context**:
   ```python
   logger.info("Motor command executed", 
               command="move_forward", 
               distance=100, 
               execution_time=0.5)
   ```

3. **Use standardized event logging**:
   ```python
   # Good
   logger.log_device_event("motor_01", "initialization", "success")
   
   # Avoid
   logger.info("Motor 01 initialized successfully")
   ```

4. **Log performance metrics consistently**:
   ```python
   start_time = time.time()
   # ... do work
   execution_time = time.time() - start_time
   logger.log_performance_metric("operation_time", execution_time, "seconds")
   ```

5. **Handle exceptions properly**:
   ```python
   try:
       # ... risky operation
   except Exception as e:
       logger.exception("Operation failed", operation="motor_control")
   ```

## Testing

Run the logging service tests:

```bash
# Basic functionality test (no external dependencies)
python hal_service/test_logging_standalone.py

# Full test suite (requires pytest)
python -m pytest tests/test_logging_service.py -v

# Demo script
python hal_service/demo_logging.py
```

## Requirements

The logging service uses only Python standard library components and has no external dependencies for core functionality. Integration with the HAL system requires:

- Python 3.8+
- pydantic (for configuration validation)
- paho-mqtt (for MQTT integration)

## File Structure

```
hal_service/
├── logging_service.py          # Main logging service implementation
├── demo_logging.py             # Demonstration script
├── test_logging_standalone.py  # Standalone tests
└── README_LOGGING.md           # This documentation

tests/
└── test_logging_service.py     # Full test suite
```