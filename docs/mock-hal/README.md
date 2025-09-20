# Mock Hardware Abstraction Layer (HAL)

This directory contains a complete mock implementation of the Orchestrator HAL that simulates all hardware components without requiring physical devices. It's designed for UI/control development, testing, and demonstration purposes.

## Overview

The Mock HAL provides:

- **Realistic sensor data simulation** - LiDAR scans with obstacles, encoder feedback, motor telemetry
- **Command processing** - Responds to motor commands and updates simulation state
- **MQTT interface compatibility** - Same topics and message formats as real HAL
- **Coordinated simulation** - All components maintain consistent state (robot position, obstacles, etc.)
- **Configurable behavior** - Adjustable delays, failure rates, and simulation parameters

## Components

### Core Components

- **`MockHALOrchestrator`** - Main orchestrator that manages all mock devices
- **`MockMQTTClient`** - In-memory MQTT broker simulation
- **`SimulationCoordinator`** - Maintains consistent state across all mock devices

### Mock Devices

- **`MockMotorController`** - Simulates DC motor with encoder feedback
- **`MockEncoderSensor`** - Generates realistic encoder pulses and odometry
- **`MockLidarSensor`** - Creates 360° scans with obstacles and walls
- **`MockSafetyMonitor`** - Monitors for obstacles and triggers emergency stops
- **`MockStateManager`** - Tracks robot position and publishes state

### Data Generators

- **`LidarDataGenerator`** - Creates realistic LiDAR scans with obstacles
- **`EncoderDataGenerator`** - Simulates wheel encoder behavior
- **`MotorDataGenerator`** - Models motor physics (current, temperature, etc.)

## Quick Start

### 1. Run the Mock HAL

```bash
# Basic usage
python hal_service/mock/mock_orchestrator.py

# With custom config
python hal_service/mock/mock_orchestrator.py --config my_config.yaml

# Enable debug logging
python hal_service/mock/mock_orchestrator.py --log-level DEBUG

# Disable timing delays for faster testing
python hal_service/mock/mock_orchestrator.py --no-delays

# Enable random failures for error testing
python hal_service/mock/mock_orchestrator.py --enable-failures
```

### 2. Test the Implementation

```bash
# Run the test script
python tests/test_mock_hal.py
```

### 3. Connect Your Application

The mock HAL uses the same MQTT topics as the real HAL:

```python
import paho.mqtt.client as mqtt
import json

# Connect to mock MQTT (runs in-memory)
client = mqtt.Client()
client.connect("localhost", 1883, 60)

# Send motor command
command = {
    "timestamp": "2025-01-15T10:30:00Z",
    "command_id": "move_001",
    "action": "move_forward",
    "parameters": {
        "distance": 1.0,
        "speed": 0.5
    }
}
client.publish("orchestrator/cmd/left_motor", json.dumps(command))

# Subscribe to telemetry
def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print(f"Received: {msg.topic} -> {data}")

client.on_message = on_message
client.subscribe("orchestrator/data/+")
client.subscribe("orchestrator/status/+")
```

## MQTT Topics

The mock HAL implements the complete MQTT interface:

### Command Topics
- `orchestrator/cmd/left_motor` - Left motor commands
- `orchestrator/cmd/right_motor` - Right motor commands  
- `orchestrator/cmd/estop` - Emergency stop commands
- `orchestrator/cmd/state_manager` - State management commands

### Data Topics
- `orchestrator/data/left_encoder` - Left encoder telemetry
- `orchestrator/data/right_encoder` - Right encoder telemetry
- `orchestrator/data/lidar_01` - LiDAR scan data
- `orchestrator/data/left_motor` - Left motor telemetry
- `orchestrator/data/right_motor` - Right motor telemetry

### Status Topics
- `orchestrator/status/robot` - Robot state (position, heading, velocity)
- `orchestrator/status/safety_monitor` - Safety system status
- `orchestrator/status/system` - Overall system health
- `orchestrator/status/hal` - HAL orchestrator status

## Simulation Features

### Realistic Physics

The mock HAL simulates realistic robot behavior:

- **Differential drive kinematics** - Proper wheel-based movement
- **Motor acceleration/deceleration** - Gradual speed changes
- **Encoder feedback** - Tick counting with noise and backlash
- **LiDAR scanning** - Ray-casting with obstacles and walls

### Environment Simulation

- **Room boundaries** - 5m x 5m room with walls
- **Static obstacles** - Configurable obstacle positions and sizes
- **Sensor noise** - Realistic measurement uncertainty
- **Mechanical effects** - Backlash, efficiency, temperature

### Configurable Parameters

```python
# Adjust simulation parameters
orchestrator = MockHALOrchestrator(
    enable_realistic_delays=True,  # Add hardware-like delays
    enable_failures=False          # Simulate random failures
)

# Configure individual generators
lidar_gen = LidarDataGenerator(
    min_range=0.15,
    max_range=12.0,
    noise_level=0.02
)
```

## Testing and Development

### Unit Testing

```python
from hal_service.mock import MockMotorController, MockMQTTClient

# Test individual components
mqtt_client = MockMQTTClient()
motor = MockMotorController("test_motor", mqtt_client, {})

# Send commands and verify responses
command = {"action": "move_forward", "parameters": {"distance": 1.0}}
success = motor.execute_command(command)
assert success

# Check telemetry
messages = mqtt_client.get_message_history("orchestrator/data/test_motor")
assert len(messages) > 0
```

### Integration Testing

```python
# Test complete system
orchestrator = MockHALOrchestrator()
orchestrator.initialize()

# Inject commands
orchestrator.inject_command("left_motor", move_command)

# Verify state changes
robot_state = orchestrator.get_simulation_coordinator().get_robot_state()
assert robot_state['position']['x'] != 0  # Robot moved
```

### Performance Testing

```python
# Monitor message throughput
mqtt_client = orchestrator.get_mqtt_client()
stats = mqtt_client.get_mock_client().get_stats()

print(f"Messages/sec: {stats['messages_published'] / uptime}")
print(f"Latency: {stats['avg_latency_ms']}ms")
```

## Configuration

The mock HAL uses the same configuration format as the real HAL:

```yaml
# config.yaml
system:
  logging:
    level: INFO
    format: json

mqtt:
  broker_host: localhost
  broker_port: 1883

motors:
  - name: left_motor
    type: dc
    gpio_pins:
      enable: 18
      direction: 19
    max_speed: 1.0

sensors:
  - name: lidar_01
    type: lidar
    interface:
      port: /dev/ttyUSB0
      baudrate: 115200
    publish_rate: 10.0
```

## Troubleshooting

### Common Issues

1. **No telemetry data**
   - Check that devices are initialized: `orchestrator.get_system_status()`
   - Verify MQTT subscriptions are working

2. **Unrealistic behavior**
   - Adjust simulation parameters in data generators
   - Check coordinate system and units

3. **Performance issues**
   - Disable realistic delays: `--no-delays`
   - Reduce publish rates in configuration

### Debug Mode

```bash
# Enable detailed logging
python hal_service/mock/mock_orchestrator.py --log-level DEBUG

# Check message history
messages = orchestrator.get_message_history()
for msg in messages[-10:]:  # Last 10 messages
    print(f"{msg.topic}: {msg.payload}")
```

## Extending the Mock HAL

### Adding New Sensors

```python
class MockCameraSensor(Sensor):
    def __init__(self, device_id, mqtt_client, config):
        super().__init__(device_id, mqtt_client, config)
        # Initialize camera simulation
    
    def read_data(self):
        # Generate mock camera data
        return {
            "image_width": 640,
            "image_height": 480,
            "objects_detected": [...]
        }
```

### Custom Data Generators

```python
class CustomDataGenerator:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2
    
    def generate_data(self, sim_state):
        # Generate custom sensor data based on simulation state
        return {"custom_value": sim_state.robot_x * self.param1}
```

### Environment Modifications

```python
# Add custom obstacles
sim_coordinator = orchestrator.get_simulation_coordinator()
sim_coordinator.sim_state.obstacles.append((x, y, radius))

# Modify room layout
lidar_gen = sim_coordinator.lidar_generator
lidar_gen.base_environment = create_custom_environment()
```

## API Reference

See the individual module docstrings for detailed API documentation:

- `mock_orchestrator.py` - Main orchestrator class
- `mock_devices.py` - Device implementations  
- `mock_mqtt_client.py` - MQTT simulation
- `data_generators.py` - Data generation utilities

## License

This mock implementation follows the same license as the main Orchestrator project.