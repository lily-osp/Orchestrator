# Orchestrator Platform User Guide

This guide explains how to operate the robot using the web-based dashboard interface.

## Table of Contents

- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Basic Operations](#basic-operations)
- [Mission Control](#mission-control)
- [Monitoring and Telemetry](#monitoring-and-telemetry)
- [Safety Features](#safety-features)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Before operating the robot, ensure:

1. **System is Running**: All core services are active
   - HAL service (`orchestrator_hal.py`)
   - Safety monitor (`safety_monitor_service.py`)
   - State manager (`state_manager_service.py`)
   - Node-RED interface

2. **Hardware is Connected**: All sensors and actuators are properly connected and configured

3. **Network Access**: You can access the robot's network (WiFi or Ethernet)

### Accessing the Dashboard

1. **Open Web Browser**: Use any modern web browser (Chrome, Firefox, Safari, Edge)

2. **Navigate to Dashboard**: 
   - URL: `http://[ROBOT_IP]:1880/ui`
   - Local access: `http://localhost:1880/ui`
   - Example: `http://192.168.1.100:1880/ui`

3. **Verify Connection**: You should see the Orchestrator dashboard load with real-time status indicators

## Dashboard Overview

The dashboard is organized into several main sections:

### Control Panel
- **Start/Stop Buttons**: Primary robot control
- **Emergency Stop**: Immediate safety override
- **Mode Selection**: Manual vs. Autonomous operation
- **Speed Control**: Adjustable speed settings

### Status Display
- **Robot Position**: Current X/Y coordinates and heading
- **System Status**: Overall system health indicators
- **Connection Status**: MQTT and service connectivity
- **Battery/Power**: Power system monitoring (if configured)

### Telemetry Section
- **Sensor Data**: Real-time sensor readings
- **LiDAR Visualization**: Live obstacle detection display
- **Motor Status**: Current motor speeds and encoder readings
- **System Logs**: Recent system events and messages

### Mission Control
- **Mission Selection**: Choose from predefined missions
- **Mission Parameters**: Configure mission-specific settings
- **Mission Progress**: Track current mission execution
- **Mission History**: Review completed missions

## Basic Operations

### Starting the Robot

1. **System Check**: Verify all status indicators are green
   - HAL Service: ✅ Connected
   - Safety Monitor: ✅ Active
   - State Manager: ✅ Running
   - MQTT Broker: ✅ Connected

2. **Clear Area**: Ensure the robot's path is clear of obstacles

3. **Select Mode**: Choose operation mode
   - **Manual**: Direct control via dashboard
   - **Autonomous**: Mission-based operation

4. **Start Robot**: Click the **START** button
   - Status should change to "Active"
   - Motors should initialize
   - Sensors should begin publishing data

### Manual Control

When in Manual mode, you can directly control the robot:

#### Movement Controls
- **Forward**: Click "Move Forward" or use arrow keys
- **Backward**: Click "Move Backward" 
- **Turn Left**: Click "Turn Left" or use arrow keys
- **Turn Right**: Click "Turn Right" or use arrow keys
- **Stop**: Click "Stop" to halt all movement

#### Speed Control
- **Speed Slider**: Adjust movement speed (0-100%)
- **Fine Control**: Use +/- buttons for precise speed adjustment
- **Speed Presets**: Quick selection buttons (Slow, Medium, Fast)

#### Distance Control
- **Distance Input**: Specify exact movement distance
- **Unit Selection**: Choose units (cm, inches, meters)
- **Execute**: Click "Execute Movement" to perform precise movement

### Stopping the Robot

#### Normal Stop
1. Click the **STOP** button
2. Robot will decelerate smoothly
3. Status changes to "Idle"
4. All motors stop

#### Emergency Stop
1. Click the **EMERGENCY STOP** button (red)
2. Robot stops immediately
3. All systems enter safe state
4. Manual reset required to resume operation

## Mission Control

### Creating a Mission

1. **Access Mission Panel**: Click on "Mission Control" tab

2. **Select Mission Type**:
   - **Waypoint Navigation**: Move to specific coordinates
   - **Area Survey**: Systematic area coverage
   - **Object Search**: Search for specific objects
   - **Custom Sequence**: User-defined command sequence

3. **Configure Parameters**:
   - **Start Position**: Set starting coordinates
   - **Target Positions**: Define waypoints or target areas
   - **Speed Settings**: Set movement speeds
   - **Safety Margins**: Configure obstacle avoidance distances
   - **Timeout Settings**: Set maximum execution time

4. **Validate Mission**: Click "Validate" to check mission parameters

5. **Save Mission**: Click "Save" to store mission for future use

### Executing a Mission

1. **Select Mission**: Choose from saved missions dropdown

2. **Review Parameters**: Verify mission settings are correct

3. **Pre-flight Check**:
   - System status: All green
   - Battery level: Sufficient for mission
   - Area clear: No obstacles in initial path
   - Safety systems: Active and responsive

4. **Start Mission**: Click "Start Mission"
   - Mission status changes to "In Progress"
   - Progress bar shows completion percentage
   - Current step displays in status panel

5. **Monitor Progress**:
   - Watch real-time position updates
   - Monitor sensor data for obstacles
   - Check mission step progression
   - Review any warnings or alerts

### Mission Management

#### Pausing a Mission
- Click "Pause Mission" to temporarily halt execution
- Robot stops at current position
- Mission can be resumed from pause point
- Click "Resume Mission" to continue

#### Aborting a Mission
- Click "Abort Mission" to cancel execution
- Robot returns to safe state
- Mission marked as "Aborted"
- Manual control restored

#### Mission History
- View completed missions in "History" tab
- Review mission performance metrics
- Access mission logs and telemetry data
- Export mission data for analysis

## Monitoring and Telemetry

### Real-time Data Display

#### Position and Navigation
- **Current Position**: X/Y coordinates in configured units
- **Heading**: Current orientation (0-360 degrees)
- **Velocity**: Current linear and angular speeds
- **Path Tracking**: Visual representation of robot path

#### Sensor Data
- **LiDAR Readings**: Distance measurements and obstacle detection
- **Encoder Data**: Wheel rotation counts and calculated distances
- **System Sensors**: Temperature, voltage, current draw
- **Timestamp**: Data collection timestamps

#### System Health
- **CPU Usage**: Processor utilization percentage
- **Memory Usage**: RAM consumption
- **Network Status**: Connection quality and latency
- **Service Status**: Individual service health indicators

### Data Visualization

#### LiDAR Display
- **Polar Plot**: 360-degree distance measurements
- **Obstacle Overlay**: Highlighted obstacles and safe zones
- **Range Indicators**: Minimum and maximum detection ranges
- **Update Rate**: Real-time refresh (typically 10Hz)

#### Position Plot
- **Robot Position**: Current location marker
- **Path History**: Trail showing recent movement
- **Waypoints**: Mission targets and checkpoints
- **Grid Overlay**: Coordinate reference system

#### Sensor Graphs
- **Time Series**: Historical sensor data plots
- **Multi-channel**: Multiple sensors on same graph
- **Zoom/Pan**: Interactive graph navigation
- **Export**: Save graph data to file

### Alerts and Notifications

#### System Alerts
- **Low Battery**: Power level warnings
- **High Temperature**: Thermal protection alerts
- **Communication Loss**: Network connectivity issues
- **Sensor Failure**: Hardware malfunction detection

#### Safety Alerts
- **Obstacle Detected**: Immediate obstacle warnings
- **Safety Zone Breach**: Boundary violation alerts
- **Emergency Stop**: Safety system activation
- **System Fault**: Critical system errors

#### Mission Alerts
- **Mission Complete**: Successful completion notification
- **Mission Failed**: Failure reason and recovery options
- **Waypoint Reached**: Progress milestone notifications
- **Parameter Exceeded**: Limit violation warnings

## Safety Features

### Emergency Stop System

The emergency stop system provides multiple layers of protection:

#### Hardware Emergency Stop
- **Physical Button**: Red emergency stop button on robot
- **GPIO Integration**: Direct hardware interrupt
- **Immediate Response**: <100ms stop time
- **Power Cutoff**: Motor power disconnection

#### Software Emergency Stop
- **Dashboard Button**: Web interface emergency stop
- **MQTT Command**: Remote emergency stop capability
- **Automatic Triggers**: Sensor-based emergency stops
- **Graceful Shutdown**: Controlled system shutdown

### Obstacle Avoidance

#### LiDAR-based Detection
- **360° Coverage**: Full perimeter monitoring
- **Configurable Zones**: Multiple detection zones
- **Dynamic Response**: Speed-based safety margins
- **Obstacle Classification**: Size and distance analysis

#### Safety Zones
- **Stop Zone**: Immediate stop distance (default: 30cm)
- **Slow Zone**: Reduced speed distance (default: 50cm)
- **Warning Zone**: Alert-only distance (default: 100cm)
- **Custom Zones**: User-configurable safety areas

### System Monitoring

#### Watchdog Systems
- **Communication Watchdog**: MQTT heartbeat monitoring
- **Service Watchdog**: Process health checking
- **Hardware Watchdog**: Sensor responsiveness
- **Mission Watchdog**: Execution timeout protection

#### Fail-safe Behaviors
- **Communication Loss**: Return to safe position
- **Sensor Failure**: Graceful degradation
- **Power Issues**: Emergency shutdown sequence
- **Software Crash**: Automatic service restart

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
**Symptoms**: Browser shows connection error or blank page

**Solutions**:
1. Check robot network connection
2. Verify Node-RED service is running: `systemctl status node-red`
3. Check firewall settings on robot
4. Try different browser or clear browser cache
5. Verify correct IP address and port (1880)

#### Robot Not Responding to Commands
**Symptoms**: Commands sent but robot doesn't move

**Solutions**:
1. Check HAL service status in dashboard
2. Verify MQTT broker connection
3. Check motor controller status
4. Ensure robot is not in emergency stop state
5. Verify configuration file settings

#### Sensor Data Not Updating
**Symptoms**: Sensor displays show old or no data

**Solutions**:
1. Check sensor hardware connections
2. Verify sensor service status
3. Check MQTT topic subscriptions
4. Restart sensor services
5. Check sensor configuration parameters

#### Mission Execution Failures
**Symptoms**: Missions start but fail to complete

**Solutions**:
1. Check mission parameters for validity
2. Verify sufficient battery/power
3. Ensure clear path to targets
4. Check safety system settings
5. Review mission logs for error details

### Diagnostic Tools

#### System Status Check
1. Navigate to "System" tab in dashboard
2. Review all service status indicators
3. Check system resource usage
4. Verify network connectivity
5. Review recent error logs

#### MQTT Message Monitor
1. Open "Debug" tab in dashboard
2. Monitor MQTT message traffic
3. Check command/response patterns
4. Verify message formatting
5. Look for communication errors

#### Log Analysis
1. Access "Logs" section in dashboard
2. Filter by severity level (Error, Warning, Info)
3. Search for specific error messages
4. Export logs for detailed analysis
5. Check timestamp patterns for issues

### Getting Help

#### Documentation Resources
- **Component Guides**: `docs/hal_service/` directory
- **API Documentation**: Inline code documentation
- **Configuration Guide**: `configs/example_config.yaml`
- **Troubleshooting**: This user guide

#### Support Channels
- **System Logs**: Check `logs/orchestrator.log`
- **Demo Scripts**: Run validation demos in `demos/`
- **Test Suite**: Execute `python run_tests.py`
- **Issue Tracking**: Create detailed issue reports

#### Emergency Procedures
1. **Immediate Safety**: Use emergency stop button
2. **System Shutdown**: Power off robot safely
3. **Service Restart**: Restart individual services
4. **Full Reset**: Reboot entire system
5. **Recovery Mode**: Boot with minimal services

---

## Best Practices

### Daily Operation
- Always perform system check before operation
- Keep dashboard open during robot operation
- Monitor battery/power levels regularly
- Review mission parameters before execution
- Maintain clear communication with robot

### Maintenance
- Regular sensor cleaning and calibration
- Periodic system log review
- Software update management
- Hardware connection inspection
- Configuration backup maintenance

### Safety Guidelines
- Never operate robot without supervision
- Maintain clear emergency stop access
- Keep operating area clear of people
- Regular safety system testing
- Emergency procedure training

---

*For technical support and advanced configuration, refer to the developer documentation in the `docs/` directory.*