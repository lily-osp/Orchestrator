# Motor Controller Implementation

This document describes the MotorController implementation for the Orchestrator platform.

## Overview

The MotorController class provides DC motor control with encoder feedback for precise distance and rotation control. It inherits from the Actuator base class and integrates with the MQTT communication system.

## Features

- **PWM Speed Control**: Variable speed control using GPIO PWM
- **Direction Control**: Forward/reverse movement via GPIO direction pin
- **Encoder Feedback**: Precise distance measurement using wheel encoders
- **MQTT Integration**: Command subscription and telemetry publishing
- **Safety Features**: Movement limits, error handling, and emergency stop
- **Real-time Control**: 10Hz control loop with gradual acceleration/deceleration

## Configuration

Motors are configured in the `config.yaml` file:

```yaml
motors:
  - name: left_motor
    type: dc
    gpio_pins:
      enable: 18      # PWM pin for speed control
      direction: 19   # GPIO pin for direction control
    encoder_pins:
      a: 20          # Encoder channel A
      b: 21          # Encoder channel B (optional)
    max_speed: 1.0   # Maximum speed (0.0 to 1.0)
    acceleration: 0.5 # Acceleration rate
```

## MQTT Topics

### Command Topic
- **Topic**: `orchestrator/cmd/{motor_name}`
- **QoS**: 1 (at-least-once delivery)

### Telemetry Topic
- **Topic**: `orchestrator/data/{motor_name}`
- **QoS**: 0 (fire-and-forget)

### Status Topic
- **Topic**: `orchestrator/status/{motor_name}`
- **QoS**: 0 (fire-and-forget)

### Acknowledgment Topic
- **Topic**: `orchestrator/ack/{motor_name}`
- **QoS**: 1 (at-least-once delivery)

## Command Format

Commands are sent as JSON messages:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "command_id": "unique-command-id",
  "action": "move_forward|move_backward|rotate_left|rotate_right|stop|set_speed",
  "parameters": {
    "distance": 1.0,    // meters (for move commands)
    "speed": 0.5,       // 0.0 to 1.0 (fraction of max_speed)
    "angle": 90.0,      // degrees (for rotate commands)
    "direction": 1      // 1 for forward, -1 for reverse (for set_speed)
  }
}
```

### Supported Actions

#### move_forward
Move the motor forward by a specified distance.
```json
{
  "action": "move_forward",
  "parameters": {
    "distance": 1.0,  // meters
    "speed": 0.5      // 0.0 to 1.0
  }
}
```

#### move_backward
Move the motor backward by a specified distance.
```json
{
  "action": "move_backward", 
  "parameters": {
    "distance": 0.5,  // meters
    "speed": 0.3      // 0.0 to 1.0
  }
}
```

#### rotate_left / rotate_right
Rotate the motor by a specified angle.
```json
{
  "action": "rotate_left",
  "parameters": {
    "angle": 90.0,    // degrees
    "speed": 0.3      // 0.0 to 1.0
  }
}
```

#### set_speed
Set continuous motor speed without distance target.
```json
{
  "action": "set_speed",
  "parameters": {
    "speed": 0.7,     // 0.0 to 1.0
    "direction": 1    // 1 for forward, -1 for reverse
  }
}
```

#### stop
Stop the motor immediately.
```json
{
  "action": "stop"
}
```

## Telemetry Format

Motor telemetry is published continuously:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "device_id": "left_motor",
  "data": {
    "motor_id": "left_motor",
    "is_moving": true,
    "current_speed": 0.5,
    "target_speed": 0.5,
    "direction": 1,
    "encoder_count": 1250,
    "distance_traveled": 0.392,
    "target_distance": 1.0,
    "velocity": 0.15,
    "duty_cycle": 50.0
  }
}
```

## Usage Example

```python
from hal_service.motor_controller import MotorController
from hal_service.mqtt_client import MQTTClientWrapper, MQTTConfig
from hal_service.config import MotorConfig

# Create MQTT client
mqtt_config = MQTTConfig(broker_host="localhost")
mqtt_client = MQTTClientWrapper(mqtt_config)
mqtt_client.connect()

# Create motor configuration
motor_config = MotorConfig(
    name="left_motor",
    type="dc",
    gpio_pins={"enable": 18, "direction": 19},
    encoder_pins={"a": 20, "b": 21},
    max_speed=1.0,
    acceleration=0.5
)

# Create and initialize motor controller
motor = MotorController("left_motor", mqtt_client, motor_config)
motor.initialize()

# Execute commands
command = {
    "action": "move_forward",
    "parameters": {"distance": 1.0, "speed": 0.5},
    "command_id": "cmd_001"
}
motor.execute_command(command)

# Get status
status = motor.get_status()
print(f"Motor status: {status}")

# Cleanup
motor.stop()
mqtt_client.disconnect()
```

## Hardware Requirements

- **Raspberry Pi**: GPIO pins for motor control
- **Motor Driver**: H-bridge or motor driver board (e.g., L298N)
- **DC Motor**: With optional encoder for feedback
- **Power Supply**: Appropriate voltage/current for motors

## GPIO Pin Connections

```
Raspberry Pi    Motor Driver    Motor/Encoder
GPIO 18    -->  Enable (PWM)    
GPIO 19    -->  Direction       
GPIO 20    -->                  Encoder A
GPIO 21    -->                  Encoder B
```

## Error Handling

The MotorController includes comprehensive error handling:

- **GPIO Initialization Errors**: Logged and initialization fails gracefully
- **Command Validation**: Invalid parameters are rejected
- **MQTT Communication Errors**: Automatic reconnection and error logging
- **Hardware Failures**: Graceful degradation and status reporting
- **Thread Safety**: Movement commands are thread-safe with locks

## Performance Characteristics

- **Control Loop Frequency**: 10Hz (100ms intervals)
- **PWM Frequency**: 1kHz (configurable)
- **Encoder Resolution**: 1000 pulses per revolution (configurable)
- **Acceleration**: Gradual speed changes to prevent mechanical stress
- **Response Time**: < 100ms for command acknowledgment

## Testing

Run the motor controller tests:

```bash
python -m pytest tests/test_motor_controller.py -v
```

Run the example demo:

```bash
python hal_service/motor_example.py
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **1.1**: Modular hardware abstraction with standardized motor interface
- **1.2**: Simple, standardized methods (move_forward, rotate_left, etc.)
- **1.3**: Encapsulated GPIO/PWM protocol details within the class
- **2.2**: Asynchronous MQTT communication for commands and telemetry

## Dependencies

- **FND-02**: Base classes (Actuator, Device)
- **FND-03**: MQTT client wrapper
- **FND-04**: Configuration service
- **RPi.GPIO**: Raspberry Pi GPIO control (with mock for development)
- **Threading**: For control loops and thread safety