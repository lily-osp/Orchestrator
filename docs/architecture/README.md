# Architecture Documentation

This directory contains system architecture documentation for the Orchestrator Platform.

## Contents

### System Architecture
- **4-Layer Architecture**: Hardware, HAL, Communication, Control layers
- **Component Interactions**: Service communication patterns
- **Data Flow**: Information flow through the system
- **Safety Architecture**: Multi-layered safety system design

### Design Patterns
- **Hardware Abstraction**: Device abstraction patterns
- **Publisher-Subscriber**: MQTT communication patterns
- **State Management**: Centralized state management
- **Error Handling**: Fault tolerance and recovery

### Deployment Architecture
- **Service Architecture**: Systemd service organization
- **Network Architecture**: MQTT broker and client topology
- **Security Architecture**: Authentication and authorization
- **Monitoring Architecture**: Logging and telemetry collection

## Architecture Overview

The Orchestrator Platform implements a modular 4-layer architecture:

```
┌─────────────────────────────────────────┐
│          Control & UI Layer             │
│        (Node-RED, Web Interface)        │
├─────────────────────────────────────────┤
│         Communication Layer             │
│           (MQTT Broker)                 │
├─────────────────────────────────────────┤
│      Hardware Abstraction Layer        │
│    (Python HAL Service, Safety,        │
│     State Management, Logging)          │
├─────────────────────────────────────────┤
│         Physical Hardware               │
│   (Raspberry Pi, Sensors, Actuators)   │
└─────────────────────────────────────────┘
```

### Layer Responsibilities

#### Layer 1: Physical Hardware
- **Raspberry Pi 4**: Main onboard computer
- **Sensors**: Encoders, LiDAR, I2C/SPI sensors
- **Actuators**: Motors, servos, grippers
- **Interfaces**: GPIO, I2C, SPI, UART

#### Layer 2: Hardware Abstraction Layer (HAL)
- **Device Abstraction**: Unified interfaces for hardware
- **Safety Monitoring**: Real-time safety checks
- **State Management**: System state persistence
- **Communication**: MQTT client integration

#### Layer 3: Communication Layer
- **MQTT Broker**: Message routing and delivery
- **Topic Organization**: Hierarchical topic structure
- **Quality of Service**: Reliable message delivery
- **Message Schemas**: Structured data formats

#### Layer 4: Control & UI Layer
- **Visual Programming**: Node-RED flow editor
- **Web Dashboard**: Real-time monitoring and control
- **Mission Control**: Automated sequence execution
- **User Interface**: Responsive web-based UI

## Design Principles

### Modularity
- **Loose Coupling**: Components communicate via well-defined interfaces
- **High Cohesion**: Related functionality grouped together
- **Pluggable Architecture**: Easy to add/remove components
- **Configuration-Driven**: Behavior controlled by configuration

### Reliability
- **Fault Tolerance**: Graceful handling of component failures
- **Automatic Recovery**: Self-healing capabilities
- **Redundancy**: Multiple safety layers
- **Monitoring**: Comprehensive health checking

### Scalability
- **Horizontal Scaling**: Add more sensors/actuators easily
- **Vertical Scaling**: Upgrade individual components
- **Performance**: Efficient resource utilization
- **Extensibility**: Support for future enhancements

### Safety
- **Defense in Depth**: Multiple safety layers
- **Fail-Safe Design**: Safe failure modes
- **Real-Time Response**: Immediate safety reactions
- **Validation**: Input validation and bounds checking

## Component Architecture

### HAL Service Architecture
```
HAL Service
├── Base Classes
│   ├── Device (abstract)
│   ├── Sensor (abstract)
│   └── Actuator (abstract)
├── Implementations
│   ├── MotorController
│   ├── EncoderSensor
│   ├── LidarSensor
│   └── SafetyMonitor
├── Services
│   ├── MQTTClient
│   ├── ConfigManager
│   ├── LoggingService
│   └── StateManager
└── Utilities
    ├── DataValidation
    ├── ErrorHandling
    └── HealthMonitoring
```

### Node-RED Architecture
```
Node-RED
├── Flow Types
│   ├── Command Flows
│   ├── Telemetry Flows
│   ├── Safety Flows
│   └── Mission Flows
├── Dashboard
│   ├── Control Panels
│   ├── Status Displays
│   ├── Telemetry Visualization
│   └── Configuration Forms
├── Integration
│   ├── MQTT Nodes
│   ├── HTTP Nodes
│   ├── WebSocket Nodes
│   └── Custom Nodes
└── Storage
    ├── Flow Persistence
    ├── Context Storage
    └── File Storage
```

## Communication Architecture

### MQTT Topic Hierarchy
```
orchestrator/
├── cmd/          # Commands (QoS 1)
├── data/         # Telemetry (QoS 0)
├── status/       # Status (QoS 1)
├── events/       # Events (QoS 1)
└── config/       # Configuration (QoS 1)
```

### Message Flow Patterns
- **Command-Response**: Synchronous command execution
- **Publish-Subscribe**: Asynchronous data distribution
- **Request-Reply**: Synchronous data queries
- **Event Notification**: Asynchronous event broadcasting

## Safety Architecture

### Multi-Layer Safety
1. **Hardware Safety**: Physical emergency stops, limit switches
2. **Software Safety**: Runtime parameter validation
3. **Communication Safety**: Watchdog timers, heartbeats
4. **System Safety**: Resource monitoring, graceful shutdown

### Safety Response Times
- **Emergency Stop**: <100ms hardware response
- **Obstacle Avoidance**: <200ms software response
- **Communication Timeout**: 5s watchdog timeout
- **System Health Check**: 1s monitoring interval

## Deployment Architecture

### Service Organization
```
System Services
├── orchestrator-hal.service
├── orchestrator-safety.service
├── state-manager.service
├── mosquitto.service
└── node-red.service
```

### Network Topology
```
Network Architecture
├── Local MQTT Broker (1883)
├── Node-RED Interface (1880)
├── SSH Access (22)
└── Optional VPN Access
```

## Performance Characteristics

### Throughput
- **MQTT Messages**: 1000+ messages/second
- **Sensor Data**: 10-100 Hz per sensor
- **Command Response**: <50ms typical
- **Dashboard Updates**: 1-10 Hz

### Resource Usage
- **CPU**: 10-30% typical load
- **Memory**: 256-512 MB typical usage
- **Storage**: 1-10 GB for logs and data
- **Network**: 1-10 Mbps typical bandwidth

## Future Architecture Considerations

### Planned Enhancements
- **Distributed Architecture**: Multi-robot coordination
- **Cloud Integration**: Remote monitoring and control
- **AI/ML Integration**: Intelligent behavior and learning
- **Advanced Safety**: Predictive safety systems

### Scalability Roadmap
- **Microservices**: Break HAL into smaller services
- **Container Deployment**: Docker/Kubernetes support
- **Load Balancing**: Multiple MQTT brokers
- **Data Pipeline**: Stream processing for telemetry

---

## Architecture Documentation Standards

### Diagram Standards
- **UML Diagrams**: Component, sequence, deployment diagrams
- **Network Diagrams**: Topology and data flow
- **State Diagrams**: System and component states
- **Architecture Diagrams**: Layer and component relationships

### Documentation Updates
- **Version Control**: Architecture changes tracked in git
- **Review Process**: Architecture changes require review
- **Impact Analysis**: Document changes to interfaces
- **Migration Guides**: Document upgrade procedures

---

*This architecture documentation provides the foundation for understanding, maintaining, and extending the Orchestrator Platform.*