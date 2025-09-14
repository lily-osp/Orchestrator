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
│         Physical Hardware               │
│   (Raspberry Pi, Sensors, Actuators)   │
└─────────────────────────────────────────┘
```

### Layer Responsibilities

1. **Physical Hardware**: Raspberry Pi, sensors (encoders, LIDAR), actuators (motors)
2. **Hardware Abstraction Layer**: Python services providing unified interfaces
3. **Communication Layer**: MQTT broker for real-time messaging
4. **Control & UI Layer**: Node-RED flows and web-based dashboards

## Project Structure

The codebase is organized into logical directories for maintainability and ease of navigation:

```
orchestrator-platform/
├── hal_service/              # Core HAL implementation
│   ├── __init__.py          # Package initialization
│   ├── base.py              # Base classes and interfaces
│   ├── config.py            # Configuration management
│   ├── encoder_sensor.py    # Encoder sensor interface
│   ├── lidar_sensor.py      # LIDAR sensor interface
│   ├── logging_service.py   # Logging service implementation
│   ├── motor_controller.py  # Motor control interface
│   ├── mqtt_client.py       # MQTT communication client
│   ├── safety_monitor.py    # Safety monitoring implementation
│   ├── state_manager.py     # State management implementation
│   └── requirements.txt     # HAL-specific dependencies
├── docs/                    # Comprehensive documentation
│   ├── README.md           # Documentation index
│   ├── node_red_config.md  # Node-RED setup guide
│   └── hal_service/        # Component-specific documentation
│       ├── README_ENCODER.md
│       ├── README_LIDAR.md
│       ├── README_LOGGING.md
│       ├── README_MOTOR.md
│       ├── README_MQTT.md
│       ├── README_SAFETY.md
│       └── README_STATE_MANAGER.md
├── tests/                   # Complete test suite
│   ├── conftest.py         # Test configuration and fixtures
│   ├── test_basic.py       # Basic functionality tests
│   ├── test_config.py      # Configuration tests
│   ├── test_*_sensor.py    # Sensor-specific tests
│   ├── test_*_controller.py # Controller tests
│   ├── test_*_service.py   # Service tests
│   └── test_*_integration.py # Integration tests
├── demos/                   # Examples and validation scripts
│   ├── config_example.py   # Configuration examples
│   ├── demo_*.py          # Component demonstrations
│   ├── *_example.py       # Usage examples
│   ├── validate_*.py      # Validation scripts
│   └── demo_logs/         # Demo execution logs
├── configs/                 # Configuration files
│   ├── config.yaml        # Main configuration
│   ├── example_config.yaml # Configuration template
│   ├── systemd/           # Service definitions
│   └── node_red_config/   # Node-RED configurations
├── logs/                    # Runtime logs
├── .kiro/specs/            # Feature specifications
│   └── orchestrator-platform/
│       ├── requirements.md # Feature requirements
│       ├── design.md      # System design
│       └── tasks.md       # Implementation tasks
├── .github/workflows/       # CI/CD configuration
├── orchestrator_hal.py     # Main HAL service
├── safety_monitor_service.py # Safety service
├── state_manager_service.py # State management service
├── requirements.txt        # Project dependencies
├── run_tests.py           # Test runner script
└── run_demo.py            # Demo runner script
```

## Quick Start

### Prerequisites

- Python 3.8+
- Raspberry Pi (for hardware components)
- MQTT broker (Mosquitto recommended)
- Node-RED (for visual programming interface)

### Basic Setup

1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd orchestrator-platform
   
   # Create virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r hal_service/requirements.txt
   ```

2. **Configure System Dependencies**
   ```bash
   # On Raspberry Pi
   sudo apt update
   sudo apt install mosquitto mosquitto-clients nodejs npm
   sudo systemctl enable mosquitto
   sudo systemctl start mosquitto
   
   # Install Node-RED
   sudo npm install -g --unsafe-perm node-red
   sudo npm install -g --unsafe-perm node-red-dashboard
   ```

3. **Configure Hardware**
   ```bash
   cp configs/example_config.yaml configs/config.yaml
   # Edit configs/config.yaml with your hardware settings
   
   # Enable I2C and SPI (on Raspberry Pi)
   sudo raspi-config
   # Navigate to Interface Options -> I2C -> Enable
   # Navigate to Interface Options -> SPI -> Enable
   
   # Add user to required groups
   sudo usermod -a -G gpio,i2c,spi $USER
   # Logout and login again for group changes to take effect
   ```

4. **Verify Installation**
   ```bash
   # Test MQTT broker
   mosquitto_pub -h localhost -t test -m "hello"
   mosquitto_sub -h localhost -t test
   
   # Run basic tests
   python run_tests.py
   
   # Run demo to verify setup
   python run_demo.py demo_mock_hal
   ```

5. **Start Core Services**
   ```bash
   # Terminal 1: Start HAL service
   python orchestrator_hal.py
   
   # Terminal 2: Start safety monitor
   python safety_monitor_service.py
   
   # Terminal 3: Start state manager
   python state_manager_service.py
   
   # Terminal 4: Start Node-RED (optional)
   node-red
   ```

6. **Access Web Interface**
   ```bash
   # Node-RED editor: http://localhost:1880
   # Dashboard: http://localhost:1880/ui
   ```

## Installation

### System Dependencies

**Raspberry Pi:**
```bash
sudo apt update
sudo apt install python3-pip mosquitto mosquitto-clients nodejs npm
sudo pip3 install RPi.GPIO
```

**Development Machine:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node-RED (optional)
npm install -g node-red
```

### Python Environment

**Using Virtual Environment (Recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Hardware Setup

1. **GPIO Configuration**: Ensure proper GPIO pin assignments in `configs/config.yaml`
2. **I2C/SPI**: Enable I2C and SPI interfaces via `raspi-config`
3. **Permissions**: Add user to `gpio` and `i2c` groups
4. **MQTT Broker**: Configure and start Mosquitto broker

## Core Components

### Hardware Abstraction Layer (HAL)

The HAL provides unified interfaces for all hardware components:

#### Sensors
- **Encoder Sensor** (`encoder_sensor.py`): Rotary encoder interface with position tracking
- **LIDAR Sensor** (`lidar_sensor.py`): Distance measurement and obstacle detection

#### Actuators
- **Motor Controller** (`motor_controller.py`): PWM motor control with safety limits

#### Communication
- **MQTT Client** (`mqtt_client.py`): Pub/sub messaging with automatic reconnection

#### Services
- **Logging Service** (`logging_service.py`): Centralized logging with rotation
- **Safety Monitor** (`safety_monitor.py`): Real-time safety checking
- **State Manager** (`state_manager.py`): State persistence and synchronization

### Safety System

Multi-layered safety architecture:

1. **Hardware Safety**: GPIO-based emergency stops and limit switches
2. **Software Safety**: Runtime monitoring of system parameters
3. **Communication Safety**: Watchdog timers and heartbeat monitoring
4. **State Safety**: Validation of state transitions and persistence

### State Management

Centralized state management with:

- **Persistence**: State saved to disk with atomic writes
- **Synchronization**: MQTT-based state distribution
- **Validation**: Schema-based state validation
- **Recovery**: Automatic state recovery on startup

### Communication Layer

MQTT-based communication providing:

- **Real-time Messaging**: Low-latency command and telemetry
- **Topic Organization**: Hierarchical topic structure
- **Quality of Service**: Configurable QoS levels
- **Retained Messages**: State persistence across connections

## Development Guide

### Developer Setup

#### Prerequisites for Development

- Python 3.8+ with pip
- Git
- Code editor (VS Code recommended)
- Hardware (Raspberry Pi 4 recommended for full testing)

#### Complete Development Environment Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd orchestrator-platform
   ```

2. **Setup Python Environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate     # Windows
   
   # Upgrade pip and install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r hal_service/requirements.txt
   
   # Install development dependencies
   pip install pytest pytest-cov flake8 black mypy
   ```

3. **Configure Development Environment**
   ```bash
   # Copy example configuration
   cp configs/example_config.yaml configs/config.yaml
   
   # Set Python path for imports
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   # Add to ~/.bashrc or ~/.zshrc for persistence
   echo 'export PYTHONPATH="${PYTHONPATH}:'$(pwd)'"' >> ~/.bashrc
   ```

4. **Install System Dependencies (Development Machine)**
   ```bash
   # Ubuntu/Debian
   sudo apt install mosquitto mosquitto-clients
   
   # macOS
   brew install mosquitto
   
   # Start MQTT broker
   sudo systemctl start mosquitto  # Linux
   brew services start mosquitto   # macOS
   ```

5. **Setup Node-RED (Optional)**
   ```bash
   # Install Node.js and npm if not already installed
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Install Node-RED
   sudo npm install -g --unsafe-perm node-red
   sudo npm install -g --unsafe-perm node-red-dashboard
   
   # Configure Node-RED
   mkdir -p ~/.node-red
   cp configs/node_red_config/settings.js ~/.node-red/
   ```

6. **Verify Development Setup**
   ```bash
   # Run all tests
   python run_tests.py
   
   # Run linting
   flake8 hal_service/ tests/
   
   # Run type checking
   mypy hal_service/
   
   # Run demo
   python run_demo.py demo_mock_hal
   ```

#### IDE Configuration

**VS Code Setup** (recommended):

1. Install Python extension
2. Configure settings.json:
   ```json
   {
     "python.defaultInterpreterPath": "./venv/bin/python",
     "python.linting.enabled": true,
     "python.linting.flake8Enabled": true,
     "python.formatting.provider": "black",
     "python.testing.pytestEnabled": true,
     "python.testing.pytestArgs": ["tests/"]
   }
   ```

3. Install recommended extensions:
   - Python
   - Python Docstring Generator
   - GitLens
   - YAML

### Code Organization

- **Base Classes**: Extend `hal_service.base.BaseComponent` for new components
- **Configuration**: Use `hal_service.config` for settings management
- **Logging**: Integrate with `hal_service.logging_service`
- **Testing**: Follow existing test patterns in `tests/`

### Adding New Components

1. **Create Component Class**:
   ```python
   from hal_service.base import BaseComponent
   
   class NewSensor(BaseComponent):
       def __init__(self, config):
           super().__init__(config)
           # Initialize hardware
   
       def read_data(self):
           # Implement data reading
           pass
   ```

2. **Add Configuration Schema**:
   ```python
   # In hal_service/config.py
   class NewSensorConfig(BaseModel):
       pin: int
       sample_rate: float = 10.0
   ```

3. **Create Tests**:
   ```python
   # In tests/test_new_sensor.py
   def test_new_sensor_initialization():
       # Test component initialization
       pass
   ```

4. **Add Documentation**:
   ```markdown
   # In docs/hal_service/README_NEW_SENSOR.md
   # New Sensor Component
   
   ## Overview
   Description of the new sensor...
   ```

### Development Workflow

1. **Feature Development**:
   - Create feature branch
   - Implement component in `hal_service/`
   - Add comprehensive tests in `tests/`
   - Update documentation in `docs/`

2. **Testing**:
   ```bash
   # Run all tests
   python run_tests.py
   
   # Run specific test
   python -m pytest tests/test_new_component.py -v
   ```

3. **Validation**:
   ```bash
   # Create demo script
   python run_demo.py new_component_demo
   
   # Validate functionality
   python run_demo.py validate_new_component
   ```

## Testing

### Test Organization

The test suite is organized by component and test type:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-component interaction testing
- **Functional Tests**: End-to-end workflow testing
- **Hardware Tests**: Hardware-in-the-loop testing (when available)

### Running Tests

**All Tests**:
```bash
python run_tests.py
```

**Specific Test Categories**:
```bash
# Unit tests only
python -m pytest tests/test_*_sensor.py tests/test_*_controller.py

# Integration tests
python -m pytest tests/test_*_integration.py

# Configuration tests
python -m pytest tests/test_config.py
```

**Test Coverage**:
```bash
python -m pytest --cov=hal_service tests/
```

### Test Configuration

Tests use `pytest` with configuration in `tests/conftest.py`:

- **Fixtures**: Common test setup and teardown
- **Mocking**: Hardware simulation for unit tests
- **Parametrization**: Multiple test scenarios
- **Markers**: Test categorization and selection

## Demos and Examples

### Available Demos

The `demos/` directory contains practical examples:

#### Component Demos
- `demo_logging.py` - Logging service demonstration
- `demo_safety_monitor.py` - Safety system showcase
- `encoder_example.py` - Encoder sensor usage
- `lidar_example.py` - LIDAR sensor integration
- `motor_example.py` - Motor control examples
- `mqtt_example.py` - MQTT communication patterns

#### Configuration Examples
- `config_example.py` - Configuration management
- `logging_example.py` - Logging setup and usage

#### Validation Scripts
- `validate_mqtt.py` - MQTT connectivity validation
- `validate_safety_monitor.py` - Safety system validation

### Running Demos

**List Available Demos**:
```bash
python run_demo.py
```

**Run Specific Demo**:
```bash
python run_demo.py demo_safety_monitor
python run_demo.py validate_mqtt
```

**Demo with Arguments**:
```bash
python demos/motor_example.py --speed 50 --duration 10
```

## Configuration

### Main Configuration

The primary configuration file is `configs/config.yaml`:

```yaml
# Hardware Configuration
gpio:
  motor_pins: [18, 19]
  encoder_pins: [20, 21]
  safety_pin: 22

# MQTT Configuration
mqtt:
  broker: "localhost"
  port: 1883
  topics:
    commands: "orchestrator/commands"
    telemetry: "orchestrator/telemetry"

# Safety Configuration
safety:
  max_speed: 100
  emergency_stop_pin: 22
  watchdog_timeout: 5.0

# Logging Configuration
logging:
  level: "INFO"
  file: "logs/orchestrator.log"
  max_size: "10MB"
  backup_count: 5
```

### Environment-Specific Configuration

- `configs/config.yaml` - Production configuration
- `configs/example_config.yaml` - Template and development settings
- Environment variables override file settings

### Service Configuration

SystemD service files in `configs/systemd/`:

- `orchestrator-safety.service` - Safety monitor service
- `state-manager.service` - State management service

## Documentation

### Complete Documentation Suite

The `docs/` directory contains comprehensive documentation:

#### User Documentation
- **[User Guide](docs/USER_GUIDE.md)** - Complete guide for operating the robot via dashboard
- **[MQTT Reference](docs/MQTT_REFERENCE.md)** - Complete MQTT communication protocol reference
- **[System Access Guide](docs/SYSTEM_ACCESS_GUIDE.md)** - System configuration and access
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Installation and deployment instructions

#### Component Documentation
- **[HAL Service Documentation](docs/hal_service/)** - Hardware abstraction layer components
  - Encoder sensor API and usage
  - LiDAR sensor integration guide
  - Logging service configuration
  - Motor controller interface
  - MQTT client usage patterns
  - Safety system architecture
  - State management guide

#### Implementation Documentation
- **[Node-RED Documentation](docs/node-red/)** - Control interface implementation
  - Command flow implementation
  - Telemetry flow implementation
  - Dashboard UI implementation
  - Mission sequencer implementation

#### Development Documentation
- **[Mock HAL Documentation](docs/mock-hal/)** - Development and testing tools
- **[Node-RED Configuration](docs/node_red_config.md)** - Node-RED integration setup

### Quick Documentation Access

```bash
# View main documentation index
cat docs/README.md

# Access user guide
cat docs/USER_GUIDE.md

# Review MQTT protocol
cat docs/MQTT_REFERENCE.md

# Check component documentation
ls docs/hal_service/
```

## Contributing

### Development Setup

1. **Fork and Clone**:
   ```bash
   git clone <your-fork-url>
   cd orchestrator-platform
   ```

2. **Create Development Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Development Tools**:
   ```bash
   pip install flake8 black pytest-cov
   ```

### Code Standards

- **Style**: Follow PEP 8, use `black` for formatting
- **Linting**: Use `flake8` for code quality
- **Testing**: Maintain >90% test coverage
- **Documentation**: Document all public APIs

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Update documentation
4. Run full test suite
5. Submit pull request with description

### Code Review Checklist

- [ ] Tests pass and coverage maintained
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
- [ ] Security considerations addressed

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure Python path includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**GPIO Permission Errors**:
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Logout and login again
```

**MQTT Connection Issues**:
```bash
# Check broker status
sudo systemctl status mosquitto

# Test connectivity
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test
```

**Hardware Not Detected**:
```bash
# Check I2C devices
sudo i2cdetect -y 1

# Check GPIO status
gpio readall
```

### Debug Mode

Enable debug logging:

```python
# In config.yaml
logging:
  level: "DEBUG"
```

Or via environment variable:
```bash
export ORCHESTRATOR_LOG_LEVEL=DEBUG
python orchestrator_hal.py
```

### Log Analysis

Check logs for issues:

```bash
# View recent logs
tail -f logs/orchestrator.log

# Search for errors
grep ERROR logs/orchestrator.log

# Analyze demo logs
cat demos/demo_logs/orchestrator.log
```

### Performance Monitoring

Monitor system performance:

```bash
# CPU and memory usage
htop

# GPIO activity
watch -n 1 gpio readall

# MQTT traffic
mosquitto_sub -h localhost -t "orchestrator/#" -v
```

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Check the documentation in `docs/`
- Review existing issues and demos
- Create an issue for bugs or feature requests
- Refer to component-specific README files for detailed usage

---

*The Orchestrator Platform provides a robust foundation for robotics applications with safety, reliability, and extensibility at its core.*