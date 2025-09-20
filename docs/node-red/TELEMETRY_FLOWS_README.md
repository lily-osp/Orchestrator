# Node-RED Telemetry Flows Implementation

## Overview

This document describes the comprehensive telemetry flows implementation for the Orchestrator robotics platform. The telemetry flows subscribe to all `orchestrator/data/*` and `orchestrator/status/*` MQTT topics, process incoming sensor and status data, and format it for display in various dashboard widgets.

## Architecture

### Flow Organization

The telemetry system is organized into several key components:

1. **MQTT Subscribers**: Listen to data and status topics
2. **Data Routers**: Route messages to appropriate processors based on topic
3. **Data Processors**: Process and format specific sensor/status data types
4. **UI Widgets**: Display processed data in the dashboard
5. **Debug Nodes**: Provide debugging and monitoring capabilities

### MQTT Topic Structure

#### Data Topics (`orchestrator/data/+`)
- `orchestrator/data/lidar` - LiDAR scan data
- `orchestrator/data/encoders` - Wheel encoder readings
- `orchestrator/data/*` - Generic sensor data (extensible)

#### Status Topics (`orchestrator/status/+`)
- `orchestrator/status/robot` - Robot position, heading, and operational status
- `orchestrator/status/safety` - Safety system status and obstacle detection
- `orchestrator/status/system` - System health, resource usage, and component status
- `orchestrator/status/*` - Generic status data (extensible)

## Data Processing Components

### 1. LiDAR Data Processor

**Input**: LiDAR scan data with ranges and angles arrays
**Processing**:
- Calculates min/max/average ranges
- Identifies closest obstacle and its angle
- Prepares data for visualization canvas
- Stores processed data in flow context

**Outputs**:
1. Minimum range value → LiDAR Min Range gauge
2. Average range value → LiDAR Avg Range gauge  
3. Closest obstacle info → Closest Obstacle display
4. Full processed data → LiDAR visualization canvas

**Expected Data Format**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "ranges": [1.2, 1.5, 0.8, 2.1, ...],
  "angles": [0, 1, 2, 3, ...],
  "min_range": 0.1,
  "max_range": 10.0
}
```

### 2. Encoder Data Processor

**Input**: Wheel encoder readings and odometry data
**Processing**:
- Extracts left/right encoder counts
- Calculates total distance traveled
- Processes linear and angular velocities
- Computes tick differences for debugging

**Outputs**:
1. Distance traveled → Distance display
2. Linear velocity → Linear velocity gauge
3. Angular velocity → Angular velocity gauge
4. Full encoder data → Debug output

**Expected Data Format**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "left_count": 1250,
  "right_count": 1248,
  "distance_traveled": 5.2,
  "velocity": {
    "linear": 0.5,
    "angular": 0.1
  }
}
```

### 3. Robot Status Processor

**Input**: Robot operational status and position data
**Processing**:
- Extracts robot status (active, idle, error, emergency_stop)
- Processes position coordinates and heading
- Handles mission status and completion reasons
- Applies color coding based on status

**Outputs**:
1. Robot status → Status display with color coding
2. Position coordinates → Position display (X, Y)
3. Heading angle → Compass gauge
4. Mission status → Mission status display with color coding
5. Full status data → Debug output

**Expected Data Format**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "status": "active",
  "position": {
    "x": 10.5,
    "y": 5.2,
    "heading": 90.0
  },
  "mission": "in_progress",
  "reason": "executing_waypoint"
}
```

### 4. Safety Status Processor

**Input**: Safety system status and obstacle detection data
**Processing**:
- Monitors obstacle detection status
- Tracks minimum distances to obstacles
- Compares against safety thresholds
- Generates alert levels (SAFE, WARNING, DANGER)

**Outputs**:
1. Alert level → Safety alert display with color coding
2. Minimum distance → Safety distance display
3. Obstacle status → Obstacle status display (CLEAR/OBSTACLE)
4. Full safety data → Debug output

**Expected Data Format**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "status": "active",
  "obstacle_detected": false,
  "min_distance": 1.5,
  "safety_threshold": 0.5,
  "last_trigger": null
}
```

### 5. System Status Processor

**Input**: System health and resource usage data
**Processing**:
- Monitors component status (HAL, Node-RED, safety monitor)
- Tracks system resource usage (CPU, memory)
- Maintains system log history (last 50 entries)
- Applies status color coding

**Outputs**:
1. Component status → System status display with color coding
2. Memory usage → Memory usage gauge
3. CPU usage → CPU usage gauge
4. Log entries → System logs display
5. Full system data → Debug output

**Expected Data Format**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "status": "active",
  "component": "hal_service",
  "uptime": 3600,
  "memory_usage": 45.2,
  "cpu_usage": 12.8
}
```

## Dashboard UI Components

### System Monitoring Tab

The telemetry flows create a new "System Monitoring" tab in the dashboard with the following groups:

#### Robot Status Group
- **Distance Traveled**: Text display showing cumulative distance
- **Linear Velocity**: Gauge showing current linear velocity (0-2 m/s)
- **Angular Velocity**: Gauge showing current angular velocity (-2 to 2 rad/s)
- **Robot Status**: Text display with color-coded status
- **Robot Position**: Text display showing X,Y coordinates
- **Robot Heading**: Compass gauge showing current heading (0-360°)
- **Mission Status**: Text display with color-coded mission state

#### Sensor Data Group
- **LiDAR Min Range**: Gauge showing minimum detected range (0-10m)
- **LiDAR Avg Range**: Gauge showing average scan range (0-10m)
- **Closest Obstacle**: Text display showing distance and angle to closest obstacle
- **Safety Alert**: Text display with color-coded safety status
- **Safety Distance**: Text display showing minimum safety distance
- **Obstacle Status**: Text display showing CLEAR/OBSTACLE status

#### LiDAR Visualization Group
- **LiDAR Canvas**: Real-time 2D visualization of LiDAR scan data
  - Shows robot at center (green dot)
  - Displays scan points as red dots
  - Includes range rings and crosshairs
  - Shows scan statistics (point count, min/max range)

#### System Logs Group
- **System Status**: Text display showing current system component status
- **Memory Usage**: Gauge showing system memory usage (0-100%)
- **CPU Usage**: Gauge showing system CPU usage (0-100%)
- **System Logs**: Scrollable log display with:
  - Timestamp formatting
  - Log level color coding (ERROR=red, WARN=orange, INFO=green)
  - Component identification
  - Message content

## Color Coding System

### Status Colors
- **Green**: Active, online, normal operation
- **Blue**: Idle, standby states
- **Orange**: Warning, pause states
- **Red**: Error, emergency stop, critical alerts
- **Gray**: Unknown, disconnected states

### Gauge Color Segments
- **LiDAR Ranges**: Red (0-0.5m), Yellow (0.5-2m), Green (2m+)
- **Velocities**: Green (normal), Yellow (moderate), Red (high)
- **System Resources**: Green (0-60%), Yellow (60-80%), Red (80-100%)

## Data Flow Architecture

```
MQTT Topics → Subscribers → Routers → Processors → UI Widgets
                                   ↓
                              Flow Context Storage
                                   ↓
                              Debug Outputs
```

### Flow Context Storage

Processed data is stored in Node-RED flow context for:
- Dashboard widget access
- Cross-flow data sharing
- Historical data retention (system logs)
- Debugging and monitoring

### Error Handling

Each processor includes comprehensive error handling:
- Input data validation
- Graceful degradation for missing fields
- Error logging with context
- Default value substitution

## Testing and Validation

### Automated Testing

The implementation includes a comprehensive validation script (`validate_telemetry_flows.js`) that tests:
- Flow structure and organization
- Node connections and wiring
- MQTT topic subscriptions
- UI widget configuration
- Function logic validation
- Template content verification

### Manual Testing

To test the telemetry flows:

1. **Start Node-RED**: `./start-nodered.sh`
2. **Access Dashboard**: Navigate to `http://localhost:1880/ui`
3. **View Monitoring Tab**: Click "System Monitoring" tab
4. **Publish Test Data**: Use MQTT client to publish to telemetry topics
5. **Verify Display**: Check that data appears in appropriate widgets
6. **Check Debug**: Monitor debug tab for data processing logs

### Test Data Examples

#### LiDAR Test Data
```bash
mosquitto_pub -h localhost -t "orchestrator/data/lidar" -m '{
  "timestamp": "2025-01-15T10:30:00Z",
  "ranges": [1.2, 1.5, 0.8, 2.1, 3.0, 1.8],
  "angles": [0, 60, 120, 180, 240, 300],
  "min_range": 0.1,
  "max_range": 10.0
}'
```

#### Robot Status Test Data
```bash
mosquitto_pub -h localhost -t "orchestrator/status/robot" -m '{
  "timestamp": "2025-01-15T10:30:00Z",
  "status": "active",
  "position": {"x": 10.5, "y": 5.2, "heading": 90.0},
  "mission": "in_progress"
}'
```

## Integration with HAL Services

The telemetry flows are designed to integrate seamlessly with the HAL services:

- **Motor Controller**: Publishes encoder data to `orchestrator/data/encoders`
- **LiDAR Sensor**: Publishes scan data to `orchestrator/data/lidar`
- **State Manager**: Publishes robot status to `orchestrator/status/robot`
- **Safety Monitor**: Publishes safety status to `orchestrator/status/safety`
- **System Services**: Publish health data to `orchestrator/status/system`

## Performance Considerations

### Data Rate Management
- LiDAR data: Processed at sensor rate (typically 10-20 Hz)
- Encoder data: Processed at 10 Hz for smooth velocity display
- Status updates: Processed as received (typically 1-5 Hz)
- System logs: Refreshed every 5 seconds

### Memory Management
- System logs limited to 50 most recent entries
- Flow context data automatically cleaned up
- Large data objects (LiDAR scans) processed and discarded

### Network Efficiency
- QoS 0 for high-frequency sensor data (fire-and-forget)
- QoS 1 for status updates (at-least-once delivery)
- JSON message compression through efficient data structures

## Extensibility

The telemetry system is designed for easy extension:

### Adding New Sensors
1. Sensor publishes to `orchestrator/data/{sensor_name}`
2. Generic sensor processor handles unknown sensor types
3. Add specific processor if custom formatting needed
4. Create UI widgets for sensor-specific display

### Adding New Status Sources
1. Component publishes to `orchestrator/status/{component_name}`
2. Generic status processor handles unknown status types
3. Add specific processor for complex status data
4. Create UI displays for component-specific status

### Custom Visualizations
1. Create new UI template nodes
2. Access processed data from flow context
3. Implement custom JavaScript for visualization
4. Connect to appropriate data processors

## Troubleshooting

### Common Issues

1. **No Data in Widgets**
   - Check MQTT broker connection
   - Verify topic names match expected format
   - Check debug tab for processing errors

2. **LiDAR Visualization Not Working**
   - Verify canvas element loads properly
   - Check browser JavaScript console for errors
   - Ensure data includes ranges and angles arrays

3. **System Logs Not Updating**
   - Check log refresh timer is running
   - Verify system status messages are being received
   - Check flow context storage

### Debug Tools

- **Debug Tab**: Monitor all data processing in real-time
- **Flow Context**: Inspect stored data using Node-RED context viewer
- **MQTT Debug**: Use `mosquitto_sub` to monitor raw MQTT messages
- **Browser Console**: Check for JavaScript errors in UI templates

## Requirements Compliance

This implementation satisfies the following requirements:

### Requirement 3.4 (Flow Telemetry Processing)
✅ **"WHEN flows receive telemetry data THEN they SHALL process and respond to sensor information in real-time"**

- Real-time processing of LiDAR, encoder, and status data
- Immediate dashboard updates upon data receipt
- Responsive UI widgets with live data display

### Requirement 4.4 (Dashboard Telemetry Display)
✅ **"WHEN viewing telemetry THEN the dashboard SHALL provide real-time visualization of LiDAR scans and robot state"**

- Real-time LiDAR visualization canvas with 2D scan display
- Live robot state display (position, heading, status)
- Continuous sensor data monitoring and display

### Requirement 2.2 (MQTT Telemetry Communication)
✅ **"WHEN the HAL generates telemetry data THEN it SHALL publish to topics like orchestrator/data/lidar with structured JSON payloads"**

- Comprehensive subscription to all `orchestrator/data/*` topics
- Structured processing of JSON telemetry payloads
- Proper handling of all expected data formats

## Conclusion

The telemetry flows implementation provides a comprehensive, real-time monitoring and visualization system for the Orchestrator robotics platform. It successfully processes all sensor and status data, presents it through an intuitive dashboard interface, and maintains extensibility for future enhancements.

The system is fully tested, documented, and ready for integration with the HAL services and dashboard UI components.