# Orchestrator Platform - System Access Guide

## System Status: READY!

The complete Mock Hardware Abstraction Layer (HAL) system has been successfully implemented and is ready for use. This guide provides all the information needed to access and interact with the system.

## Access Points & URLs

### 1. **Main Dashboard** (Static HTML)

- **URL**: `file:///path/to/orchestrator_dashboard.html`
- **Description**: Static HTML dashboard with system overview and quick links
- **Status**: ✅ Available (open the HTML file in any browser)

### 2. **Node-RED Dashboard** (if Node-RED is installed)

- **URL**: http://localhost:1880/ui
- **Description**: Full-featured web dashboard with controls and real-time data
- **Features**: Robot controls, telemetry visualization, LiDAR display
- **Status**: ⚠️ Requires Node-RED installation

### 3. **Node-RED Flow Editor** (if Node-RED is installed)

- **URL**: http://localhost:1880
- **Description**: Visual programming interface for creating robot behaviors
- **Features**: Drag-and-drop flow creation, MQTT integration
- **Status**: ⚠️ Requires Node-RED installation

### 4. **Simple Web Dashboard** (Python Flask)

- **URL**: http://localhost:5000
- **Description**: Lightweight web interface for basic robot control
- **Features**: Motor controls, status display, telemetry log
- **Status**: ⚠️ Requires Flask installation (`pip install flask flask-socketio`)

### 5. **MQTT Broker**

- **Host**: localhost
- **Port**: 1883
- **Description**: Message broker for system communication
- **Status**: ✅ Simulated (built into Mock HAL)

## Quick Start Options

### Option 1: View Static Dashboard (Immediate)

```bash
# Open the HTML dashboard in your browser
open orchestrator_dashboard.html
# or
firefox orchestrator_dashboard.html
# or
chrome orchestrator_dashboard.html
```

### Option 2: Run Standalone Demo (No Dependencies)

```bash
# Run the complete mock system demo
python3 demos/standalone_demo.py
```

### Option 3: Run Mock HAL with Simple Tests

```bash
# Test core functionality
python3 tests/test_mock_standalone.py
```

### Option 4: Complete System (Requires Dependencies)

```bash
# Install dependencies first
pip3 install flask flask-socketio paho-mqtt

# Run complete system
python3 demos/run_complete_system.py
```

### Option 5: Quick Setup Script

```bash
# Automated setup and launch
chmod +x quick_start.sh
./quick_start.sh
```

## MQTT Interface

### Command Topics (Send Commands)

```
orchestrator/cmd/left_motor     - Left motor commands
orchestrator/cmd/right_motor    - Right motor commands
orchestrator/cmd/estop          - Emergency stop
orchestrator/cmd/state_manager  - State management
```

### Data Topics (Receive Telemetry)

```
orchestrator/data/left_encoder   - Left wheel encoder data
orchestrator/data/right_encoder  - Right wheel encoder data
orchestrator/data/lidar_01       - LiDAR scan data
orchestrator/data/left_motor     - Left motor telemetry
orchestrator/data/right_motor    - Right motor telemetry
```

### Status Topics (System Status)

```
orchestrator/status/robot        - Robot state (position, heading, velocity)
orchestrator/status/safety_monitor - Safety system status
orchestrator/status/system       - Overall system health
orchestrator/status/hal          - HAL orchestrator status
```

### Acknowledgment Topics (Command Responses)

```
orchestrator/ack/left_motor      - Left motor command acknowledgments
orchestrator/ack/right_motor     - Right motor command acknowledgments
orchestrator/ack/estop           - Emergency stop acknowledgments
```

## Example Commands

### Motor Control via MQTT

```bash
# Move forward 1 meter at 50% speed
mosquitto_pub -h localhost -t 'orchestrator/cmd/left_motor' \
  -m '{"action":"move_forward","parameters":{"distance":1.0,"speed":0.5}}'

# Rotate right 90 degrees
mosquitto_pub -h localhost -t 'orchestrator/cmd/right_motor' \
  -m '{"action":"rotate_right","parameters":{"angle":90,"speed":0.3}}'

# Emergency stop
mosquitto_pub -h localhost -t 'orchestrator/cmd/estop' \
  -m '{"action":"emergency_stop","reason":"user_request"}'

# Stop all motors
mosquitto_pub -h localhost -t 'orchestrator/cmd/left_motor' \
  -m '{"action":"stop"}'
```

### Monitor Telemetry

```bash
# Subscribe to all telemetry data
mosquitto_sub -h localhost -t 'orchestrator/data/+'

# Subscribe to robot state
mosquitto_sub -h localhost -t 'orchestrator/status/robot'

# Subscribe to LiDAR data
mosquitto_sub -h localhost -t 'orchestrator/data/lidar_01'
```

### Python Integration

```python
import paho.mqtt.client as mqtt
import json
import time

# Connect to mock MQTT broker
client = mqtt.Client()
client.connect("localhost", 1883, 60)

# Send motor command
command = {
    "timestamp": time.time(),
    "command_id": "python_001",
    "action": "move_forward",
    "parameters": {"distance": 2.0, "speed": 0.7}
}

client.publish("orchestrator/cmd/left_motor", json.dumps(command))

# Subscribe to telemetry
def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print(f"Received: {msg.topic} -> {data}")

client.on_message = on_message
client.subscribe("orchestrator/data/+")
client.loop_forever()
```

## Development Setup

### For UI Development

1. **Start Mock HAL**: `python3 demos/standalone_demo.py`
2. **Connect your UI** to MQTT topics listed above
3. **Send commands** and **receive telemetry** in real-time
4. **Test safety features** with emergency stop commands

### For Node-RED Development

1. **Install Node-RED**: `npm install -g node-red`
2. **Start Node-RED**: `node-red --userDir configs/node_red_config`
3. **Access Flow Editor**: http://localhost:1880
4. **Access Dashboard**: http://localhost:1880/ui

### For Python Development

1. **Import mock components**: `from hal_service.mock import MockHALOrchestrator`
2. **Create orchestrator**: `orchestrator = MockHALOrchestrator()`
3. **Initialize system**: `orchestrator.initialize()`
4. **Send commands**: `orchestrator.inject_command(device, command)`

## System Features

### What's Working

- **Mock Motor Controllers** - Realistic motor behavior simulation
- **Encoder Simulation** - Tick counting with noise and backlash
- **LiDAR Scanning** - 360° obstacle detection with ray-casting
- **Safety Monitoring** - Emergency stop and obstacle detection
- **State Management** - Robot position and heading tracking
- **MQTT Communication** - Complete message routing and callbacks
- **Real-time Telemetry** - Live sensor data streaming
- **Command Processing** - Motor commands with acknowledgments

### Use Cases

- **UI Development** - Build dashboards without hardware
- **Control Logic Testing** - Test algorithms with realistic data
- **Integration Testing** - Validate MQTT communication
- **Demonstration** - Show system capabilities
- **Training** - Learn the system safely
- **Continuous Integration** - Automated testing

## 🔧 Troubleshooting

### Common Issues

1. **"No module named 'pydantic'" Error**

   - **Solution**: Use `demos/standalone_demo.py` instead of full system
   - **Alternative**: Install in virtual environment
2. **MQTT Connection Failed**

   - **Check**: Mock HAL is running
   - **Solution**: Use built-in mock MQTT (no external broker needed)
3. **Node-RED Not Found**

   - **Install**: `npm install -g node-red`
   - **Alternative**: Use simple web dashboard or static HTML
4. **Port Already in Use**

   - **Check**: `netstat -tulpn | grep :1880`
   - **Solution**: Kill existing process or use different port

### Getting Help

1. **Check logs** in the terminal output
2. **Verify system status** with `python3 tests/test_mock_standalone.py`
3. **Test MQTT** with `mosquitto_pub` and `mosquitto_sub`
4. **Review documentation** in `hal_service/mock/README.md`

## File Structure

```
orchestrator-platform/
├── docs/orchestrator_dashboard.html # Static HTML dashboard
├── demos/standalone_demo.py         # Complete demo (no dependencies)
├── tests/test_mock_standalone.py    # Core functionality tests
├── demos/run_complete_system.py     # Full system launcher
├── demos/simple_web_dashboard.py    # Flask web interface
├── quick_start.sh                  # Automated setup script
├── hal_service/mock/               # Mock HAL implementation
│   ├── mock_orchestrator.py        # Main orchestrator
│   ├── mock_devices.py             # Device implementations
│   ├── mock_mqtt_client.py         # MQTT simulation
│   └── data_generators.py          # Realistic data generation
└── configs/node_red_config/        # Node-RED configuration
    ├── flows.json                  # Node-RED flows
    ├── settings.js                 # Node-RED settings
    └── start-nodered.sh            # Node-RED startup script
```

## Success! System Ready

The Orchestrator Platform Mock HAL is now fully operational and ready for:

- ✅ **UI/Dashboard Development**
- ✅ **Control Algorithm Testing**
- ✅ **MQTT Integration**
- ✅ **System Demonstration**
- ✅ **Training and Education**

**Next Steps:**

1. Open `docs/orchestrator_dashboard.html` in your browser
2. Run `python3 demos/standalone_demo.py` to see the system in action
3. Start building your UI using the MQTT interface
4. Explore Node-RED flows for visual programming

**Happy Developing! 🚀**
