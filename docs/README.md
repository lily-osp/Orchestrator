# Orchestrator Platform

A modular robotics control system with a 4-layer architecture for flexible hardware abstraction and visual programming. This platform provides a comprehensive framework for building and controlling robotic systems with safety monitoring, state management, and real-time communication capabilities.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Core Components](#core-components)
- [Development Guide](#development-guide)
- [Testing](#testing)
- [Demos and Examples](#demos-and-examples)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

## Overview

The Orchestrator Platform is designed to provide a robust, scalable foundation for robotics applications. It implements a layered architecture that separates hardware concerns from application logic, enabling flexible deployment across different hardware configurations while maintaining consistent interfaces and safety guarantees.

### Key Features

- **Hardware Abstraction Layer (HAL)**: Unified interface for sensors, actuators, and communication
- **Safety System**: Multi-layered safety monitoring with hardware and software checks
- **State Management**: Centralized state persistence and synchronization
- **MQTT Communication**: Real-time messaging and control
- **Visual Programming**: Node-RED integration for flow-based programming
- **Comprehensive Testing**: Unit, integration, and functional test coverage
- **Modular Design**: Pluggable components and extensible architecture

## Architecture

The system implements a 4-layer architecture designed for flexibility and maintainability:

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
│         Physical Hardware Layer         │
│    (Motors, Sensors, Encoders,         │
│     Safety Hardware)                    │
└─────────────────────────────────────────┘
```

### Layer Descriptions

1. **Control & UI Layer**: Provides user interfaces and high-level control logic through Node-RED flows and web dashboards
2. **Communication Layer**: Handles all inter-component communication via MQTT messaging
3. **Hardware Abstraction Layer**: Abstracts hardware details and provides consistent APIs
4. **Physical Hardware Layer**: The actual robotic hardware components

## Project Structure

```
Orchestrator/
├── hal_service/              # Hardware Abstraction Layer components
│   ├── motor_controller.py   # Motor control and management
│   ├── lidar_sensor.py       # LIDAR sensor interface
│   ├── encoder_sensor.py     # Encoder feedback handling
│   ├── safety_monitor.py     # Safety system monitoring
│   ├── state_manager.py      # State persistence and management
│   ├── mqtt_client.py        # MQTT communication client
│   └── logging_service.py    # Centralized logging system
├── configs/                  # Configuration files and setup
│   ├── config.yaml          # Main configuration
│   ├── example_config.yaml  # Example configuration
│   └── node_red_config/     # Node-RED flows and setup
├── demos/                    # Demo applications and examples
├── docs/                     # Documentation
├── tests/                    # Test suite
├── deploy/                   # Deployment configurations
└── orchestrator_hal.py       # Main HAL orchestration service
```

## Quick Start

### Prerequisites

- Python 3.8+
- MQTT Broker (Mosquitto recommended)
- Node-RED (for visual programming interface)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Orchestrator
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Copy the example configuration and customize:

```bash
cp configs/example_config.yaml configs/config.yaml
# Edit config.yaml with your specific settings
```

### 3. Start Services

```bash
# Start MQTT broker (if not already running)
sudo systemctl start mosquitto

# Start the HAL service
python3 orchestrator_hal.py

# Start Node-RED (in another terminal)
node-red
```

### 4. Access Interfaces

- **Node-RED Dashboard**: http://localhost:1880
- **MQTT Broker**: localhost:1883
- **HAL Service Logs**: Check console output

## Installation

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM
- **Storage**: 1GB free space

### Dependencies

The platform requires the following key dependencies:

```bash
# Core Python packages
pip install paho-mqtt pyyaml numpy

# Hardware interfaces (optional, for actual hardware)
pip install RPi.GPIO  # For Raspberry Pi
pip install serial    # For serial communication

# Development tools
pip install pytest pytest-asyncio
```

### MQTT Broker Setup

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mosquitto mosquitto-clients

# Start and enable service
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### Node-RED Installation

```bash
# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Node-RED
sudo npm install -g --unsafe-perm node-red

# Start Node-RED
node-red
```

## Core Components

### 1. Motor Controller (`motor_controller.py`)

Manages motor operations with safety constraints and feedback control.

**Key Features:**
- PWM-based speed control
- Encoder feedback integration
- Safety limit enforcement
- Emergency stop functionality

**Configuration:**
```yaml
motors:
  left_motor:
    pin: 18
    max_speed: 100
    safety_limits:
      max_current: 2.0
      max_temperature: 60
```

### 2. LIDAR Sensor (`lidar_sensor.py`)

Interface for LIDAR sensors with obstacle detection and mapping capabilities.

**Key Features:**
- Real-time distance measurements
- Obstacle detection algorithms
- Data filtering and processing
- MQTT telemetry publishing

### 3. Safety Monitor (`safety_monitor.py`)

Comprehensive safety system with multiple monitoring layers.

**Safety Checks:**
- Hardware fault detection
- Software state validation
- Emergency stop handling
- System health monitoring

### 4. State Manager (`state_manager.py`)

Centralized state management with persistence and synchronization.

**Features:**
- JSON-based state persistence
- Real-time state updates
- State validation and recovery
- MQTT state broadcasting

### 5. MQTT Client (`mqtt_client.py`)

Robust MQTT communication with automatic reconnection and error handling.

**Features:**
- Automatic reconnection
- Message queuing
- Quality of Service (QoS) support
- Topic-based routing

### 6. Logging Service (`logging_service.py`)

Centralized logging with multiple output formats and levels.

**Features:**
- Structured logging (JSON format)
- Multiple log levels
- File rotation
- Remote logging support

## Development Guide

### Project Setup

1. **Environment Setup:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   ```bash
   cp configs/example_config.yaml configs/config.yaml
   # Customize configuration as needed
   ```

3. **Run Tests:**
   ```bash
   python -m pytest tests/
   ```

### Code Structure

The codebase follows these principles:

- **Modular Design**: Each component is self-contained
- **Interface Consistency**: Standardized APIs across components
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging throughout
- **Testing**: Unit and integration tests for all components

### Adding New Components

1. Create component file in `hal_service/`
2. Implement base interface from `base.py`
3. Add configuration schema
4. Write unit tests
5. Update documentation

### Configuration Management

Configuration is handled through YAML files with validation:

```python
from hal_service.config import Config

config = Config('configs/config.yaml')
motor_config = config.get_motor_config('left_motor')
```

## Testing

### Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests
├── functional/              # End-to-end functional tests
└── fixtures/                # Test data and fixtures
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/

# Run with coverage
python -m pytest --cov=hal_service

# Run specific test file
python -m pytest tests/test_motor_controller.py
```

### Test Categories

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **Functional Tests**: Test complete workflows
4. **Mock Tests**: Test with simulated hardware

## Demos and Examples

### Available Demos

1. **Basic System Demo** (`demos/standalone_demo.py`)
   - Complete system demonstration
   - All components working together
   - Mock hardware simulation

2. **Motor Control Demo** (`demos/motor_example.py`)
   - Motor control examples
   - Speed and direction control
   - Safety limit testing

3. **LIDAR Demo** (`demos/lidar_example.py`)
   - LIDAR data collection
   - Obstacle detection
   - Distance measurement

4. **MQTT Communication Demo** (`demos/mqtt_example.py`)
   - MQTT message publishing
   - Topic subscription
   - Message handling

### Running Demos

```bash
# Basic demo with mock hardware
python demos/standalone_demo.py

# Motor control demo
python demos/motor_example.py

# LIDAR demo (requires hardware)
python demos/lidar_example.py
```

## Configuration

### Main Configuration (`config.yaml`)

```yaml
# MQTT Configuration
mqtt:
  broker_host: "localhost"
  broker_port: 1883
  client_id: "orchestrator_hal"
  topics:
    commands: "robot/commands"
    telemetry: "robot/telemetry"
    status: "robot/status"

# Motor Configuration
motors:
  left_motor:
    pin: 18
    max_speed: 100
    safety_limits:
      max_current: 2.0
      max_temperature: 60
  right_motor:
    pin: 19
    max_speed: 100
    safety_limits:
      max_current: 2.0
      max_temperature: 60

# Safety Configuration
safety:
  emergency_stop_pin: 21
  watchdog_timeout: 5.0
  max_motor_current: 3.0
  temperature_threshold: 70

# Logging Configuration
logging:
  level: "INFO"
  file: "logs/orchestrator.log"
  max_size: "10MB"
  backup_count: 5
```

### Environment-Specific Configuration

Create environment-specific configs:

```bash
cp configs/example_config.yaml configs/config_production.yaml
cp configs/example_config.yaml configs/config_development.yaml
```

## Documentation

### Documentation Structure

- **User Guide**: Complete user manual
- **API Reference**: Component APIs and interfaces
- **Deployment Guide**: Installation and deployment
- **Development Guide**: Contributing and development
- **Architecture Guide**: System design and architecture

### Accessing Documentation

1. **Online**: Available at project documentation site
2. **Local**: Run local documentation server
3. **PDF**: Generated documentation packages

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use meaningful commit messages
- Ensure all tests pass

### Code Review Process

1. Automated testing
2. Code style checking
3. Manual review
4. Integration testing
5. Documentation review

## Troubleshooting

### Common Issues

#### 1. MQTT Connection Failed

**Symptoms:** "Failed to connect to MQTT broker"

**Solutions:**
```bash
# Check if Mosquitto is running
sudo systemctl status mosquitto

# Start Mosquitto if not running
sudo systemctl start mosquitto

# Check broker configuration
sudo nano /etc/mosquitto/mosquitto.conf
```

#### 2. Motor Not Responding

**Symptoms:** Motor commands sent but no movement

**Solutions:**
- Check GPIO pin assignments
- Verify motor connections
- Check power supply
- Review safety limits in config

#### 3. LIDAR Data Not Available

**Symptoms:** No LIDAR readings or connection errors

**Solutions:**
- Check serial port permissions
- Verify LIDAR power and connections
- Review serial port configuration
- Check device permissions: `sudo usermod -a -G dialout $USER`

#### 4. Node-RED Dashboard Not Loading

**Symptoms:** Dashboard not accessible or flows not working

**Solutions:**
```bash
# Check Node-RED status
node-red-admin status

# Restart Node-RED
sudo systemctl restart node-red

# Check port availability
netstat -tlnp | grep 1880
```

### Debugging

#### Enable Debug Logging

```yaml
# In config.yaml
logging:
  level: "DEBUG"
```

#### Check System Logs

```bash
# HAL service logs
tail -f logs/orchestrator.log

# System logs
journalctl -u orchestrator-hal -f

# MQTT broker logs
sudo journalctl -u mosquitto -f
```

#### Hardware Debugging

```bash
# Check GPIO status
gpio readall

# Test motor connections
python demos/motor_example.py

# Test LIDAR communication
python demos/lidar_example.py
```

### Performance Optimization

#### System Monitoring

```bash
# Monitor system resources
htop

# Check disk usage
df -h

# Monitor network connections
netstat -tulpn
```

#### Configuration Tuning

- Adjust MQTT QoS levels for performance
- Optimize logging levels for production
- Tune safety monitoring intervals
- Configure appropriate buffer sizes

### Getting Help

1. **Check Documentation**: Review relevant documentation sections
2. **Search Issues**: Look for similar issues in project issues
3. **Create Issue**: Submit detailed issue report
4. **Community Support**: Join project community channels

### Issue Reporting

When reporting issues, please include:

- Operating system and version
- Python version
- Complete error messages
- Steps to reproduce
- Configuration files (sanitized)
- System logs

---

## Support

For additional support and resources:

- **Documentation**: [Project Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Community**: [Project Community Forum](https://community.your-project.com)

---

*This documentation is continuously updated. For the latest version, please check the project repository.*
