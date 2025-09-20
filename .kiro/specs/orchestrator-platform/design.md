# Design Document

## Overview

The Orchestrator platform implements a 4-layer modular architecture that provides clear separation of concerns between hardware control, communication, and user interface layers. The design prioritizes modularity, scalability, and ease of maintenance through well-defined interfaces and standardized communication protocols.

The system runs primarily on a Raspberry Pi, with the Hardware Abstraction Layer (HAL) providing direct hardware control, MQTT serving as the communication backbone, and Node-RED offering both visual programming capabilities and web-based user interfaces.

## Architecture

### Layer 1: Physical Hardware
- **Raspberry Pi 4**: Main onboard computer running Linux
- **Actuators**: DC motors with encoders, servo motors, grippers
- **Sensors**: 2D LiDAR, wheel encoders, I2C/SPI/UART sensors
- **Communication**: GPIO, I2C, SPI, UART interfaces

### Layer 2: Hardware Abstraction Layer (HAL)
- **Runtime**: Python 3.8+ application running as systemd service
- **Architecture**: Object-oriented design with inheritance hierarchy
- **Base Classes**: 
  - `Actuator` - Base class for all actuators
  - `Sensor` - Base class for all sensors
  - `Device` - Common interface for all hardware components
- **Communication**: MQTT client for publishing telemetry and receiving commands

### Layer 3: Communication (MQTT)
- **Broker**: Mosquitto MQTT broker running locally on Raspberry Pi
- **QoS Levels**: 
  - QoS 0 for telemetry data (fire-and-forget)
  - QoS 1 for commands (at-least-once delivery)
- **Topic Structure**:
  - Commands: `orchestrator/cmd/{component}`
  - Telemetry: `orchestrator/data/{sensor}`
  - Status: `orchestrator/status/{subsystem}`

### Layer 4: Control & User Interface (Node-RED)
- **Runtime**: Node.js application with Node-RED framework
- **Components**:
  - Flow Editor for visual programming
  - Dashboard for web UI
  - MQTT nodes for communication
- **Access**: Web interface accessible on local network

## Components and Interfaces

### Hardware Abstraction Layer Components

#### Base Device Interface
```python
class Device:
    def __init__(self, device_id: str, mqtt_client):
        self.device_id = device_id
        self.mqtt_client = mqtt_client
        self.status = "initialized"
    
    def publish_status(self, data: dict):
        topic = f"orchestrator/status/{self.device_id}"
        self.mqtt_client.publish(topic, json.dumps(data))
```

#### Actuator Base Class
```python
class Actuator(Device):
    def execute_command(self, command: dict):
        raise NotImplementedError
    
    def stop(self):
        raise NotImplementedError
    
    def get_status(self) -> dict:
        raise NotImplementedError
```

#### Sensor Base Class
```python
class Sensor(Device):
    def __init__(self, device_id: str, mqtt_client, publish_rate: float = 1.0):
        super().__init__(device_id, mqtt_client)
        self.publish_rate = publish_rate
        self._running = False
    
    def start_publishing(self):
        self._running = True
        threading.Thread(target=self._publish_loop, daemon=True).start()
    
    def read_data(self) -> dict:
        raise NotImplementedError
```

#### Motor Controller Implementation
```python
class MotorController(Actuator):
    def __init__(self, device_id: str, mqtt_client, gpio_pins: dict):
        super().__init__(device_id, mqtt_client)
        self.gpio_pins = gpio_pins
        self.encoder_count = 0
        self.target_distance = 0
    
    def execute_command(self, command: dict):
        action = command.get("action")
        if action == "move_forward":
            self.move_forward(command.get("distance", 0))
        elif action == "stop":
            self.stop()
```

### MQTT Communication Schema

#### Command Message Format
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "command_id": "uuid-string",
  "action": "move_forward|stop|rotate|grip",
  "parameters": {
    "distance": 100,
    "speed": 0.5,
    "angle": 90
  }
}
```

#### Telemetry Message Format
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "device_id": "lidar_01",
  "data": {
    "ranges": [1.2, 1.5, 0.8, 2.1],
    "angles": [0, 90, 180, 270],
    "min_distance": 0.8
  }
}
```

#### Status Message Format
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "subsystem": "robot",
  "status": "active|idle|error|emergency_stop",
  "position": {"x": 10.5, "y": 5.2, "heading": 90},
  "mission": "complete|in_progress|failed",
  "reason": "obstacle_detected|target_reached|user_stop"
}
```

### Node-RED Flow Architecture

#### Core Flow Types
1. **Command Flows**: Translate UI interactions to MQTT commands
2. **Telemetry Flows**: Process sensor data and update dashboard
3. **Safety Flows**: Monitor conditions and trigger emergency stops
4. **Mission Flows**: Orchestrate complex multi-step operations

#### Dashboard Components
- Control panels with start/stop/pause buttons
- Real-time status displays
- LiDAR visualization canvas
- Configuration forms for mission parameters
- Log viewer for system events

## Data Models

### Robot State Model
```python
@dataclass
class RobotState:
    position: Position
    heading: float
    velocity: Velocity
    status: str
    last_updated: datetime
    
@dataclass
class Position:
    x: float
    y: float
    
@dataclass
class Velocity:
    linear: float
    angular: float
```

### Mission Model
```python
@dataclass
class Mission:
    mission_id: str
    name: str
    steps: List[MissionStep]
    status: str
    created_at: datetime
    
@dataclass
class MissionStep:
    step_id: str
    action: str
    parameters: dict
    timeout: float
    retry_count: int
```

### Sensor Data Models
```python
@dataclass
class LidarScan:
    timestamp: datetime
    ranges: List[float]
    angles: List[float]
    min_range: float
    max_range: float
    
@dataclass
class EncoderReading:
    timestamp: datetime
    left_count: int
    right_count: int
    distance_traveled: float
```

## Error Handling

### HAL Error Handling
- Hardware communication timeouts with exponential backoff
- Device initialization failure recovery
- Graceful degradation when sensors become unavailable
- Emergency stop propagation to all actuators

### MQTT Error Handling
- Connection loss detection and automatic reconnection
- Message delivery confirmation for critical commands
- Dead letter queue for failed message processing
- Heartbeat mechanism for connection monitoring

### Node-RED Error Handling
- Flow execution error catching and logging
- Dashboard connection loss handling
- Invalid command parameter validation
- User session management and timeout

## Testing Strategy

### Unit Testing
- Individual HAL component testing with mock hardware
- MQTT message serialization/deserialization testing
- Node-RED flow logic testing with test data injection

### Integration Testing
- End-to-end command flow testing (UI → MQTT → HAL → Hardware)
- Safety system response time testing
- Multi-component coordination testing
- Network communication reliability testing

### Hardware-in-the-Loop Testing
- Real hardware component integration testing
- Sensor data accuracy validation
- Actuator response timing verification
- Emergency stop system validation

### Performance Testing
- MQTT message throughput and latency testing
- Dashboard responsiveness under load
- Real-time telemetry streaming performance
- System resource utilization monitoring

### Safety Testing
- Obstacle detection response time validation
- Emergency stop system reliability testing
- Fail-safe behavior verification
- Communication failure recovery testing