# Safety Monitor Subsystem

## Overview

The Safety Monitor is a standalone, high-priority subsystem that provides real-time safety monitoring for the Orchestrator robotics platform. It operates as an independent process that continuously monitors sensor data and triggers emergency stops when hazardous conditions are detected.

## Features

- **Real-time Obstacle Detection**: Continuously monitors LiDAR sensor data for obstacles
- **Configurable Safety Zones**: Supports multiple safety zones with different priorities and actions
- **Emergency Stop Triggering**: Automatically publishes emergency stop commands when critical obstacles are detected
- **High-Priority Operation**: Runs as a high-priority process for safety-critical response times
- **Independent Operation**: Operates independently of the main HAL service for maximum reliability
- **Performance Monitoring**: Tracks processing times and system health
- **Comprehensive Logging**: Detailed logging of all safety events and system status

## Architecture

### Components

1. **SafetyMonitor Class**: Main safety monitoring logic
2. **SafetyZone Class**: Defines configurable safety zones
3. **ObstacleDetection Class**: Represents detected obstacles
4. **Standalone Service**: Independent process for running the safety monitor

### Safety Zones

The system supports configurable safety zones with the following properties:

- **Name**: Unique identifier for the zone
- **Angular Range**: Min/max angles defining the zone coverage
- **Distance Threshold**: Minimum safe distance for the zone
- **Priority**: Zone priority (1=highest, 5=lowest)
- **Action**: Action to take when obstacles detected ("stop", "slow", "warn")

#### Default Safety Zones

1. **Critical Front Zone** (-45° to +45°)
   - Distance: 0.5m (configurable)
   - Action: Emergency stop
   - Priority: 1 (highest)

2. **Warning Left Zone** (45° to 135°)
   - Distance: 0.35m (70% of critical threshold)
   - Action: Warning only
   - Priority: 2

3. **Warning Right Zone** (225° to 315°)
   - Distance: 0.35m (70% of critical threshold)
   - Action: Warning only
   - Priority: 2

## Configuration

The safety monitor is configured through the main `config.yaml` file:

```yaml
safety:
  enabled: true
  obstacle_threshold: 0.5  # meters
  emergency_stop_timeout: 0.1  # seconds
  safety_zones:
    - name: "custom_zone"
      min_angle: 0.0
      max_angle: 90.0
      min_distance: 1.0
      priority: 3
      action: "warn"
```

## MQTT Communication

### Subscribed Topics

- `orchestrator/data/lidar_01`: LiDAR sensor data
- `orchestrator/status/+`: System status updates

### Published Topics

- `orchestrator/cmd/estop`: Emergency stop commands
- `orchestrator/status/safety_monitor`: Safety system status

### Message Formats

#### Emergency Stop Command

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "command_id": "safety_estop_1642248600",
  "action": "emergency_stop",
  "reason": "obstacle_detected",
  "source": "safety_monitor",
  "obstacle_info": {
    "distance": 0.3,
    "angle": 0.0,
    "zone": "critical_front",
    "total_obstacles": 1
  },
  "parameters": {
    "immediate": true,
    "timeout": 0.1
  }
}
```

#### Safety Status

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "device_id": "safety_monitor",
  "status": "monitoring",
  "message": "Safety monitor active",
  "statistics": {
    "uptime_seconds": 3600,
    "emergency_stops_triggered": 0,
    "total_detections": 5,
    "avg_processing_time_ms": 2.5,
    "max_processing_time_ms": 8.1
  },
  "configuration": {
    "obstacle_threshold": 0.5,
    "emergency_stop_timeout": 0.1,
    "zones_configured": 3
  }
}
```

## Usage

### Running as Standalone Service

```bash
# Basic usage
python safety_monitor_service.py

# With custom configuration
python safety_monitor_service.py --config /path/to/config.yaml

# With high priority and logging
python safety_monitor_service.py --priority high --log-level DEBUG

# As daemon process
python safety_monitor_service.py --daemon --pid-file /var/run/safety-monitor.pid
```

### Running as System Service

1. Install the systemd service file:
```bash
sudo cp systemd/orchestrator-safety.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. Enable and start the service:
```bash
sudo systemctl enable orchestrator-safety
sudo systemctl start orchestrator-safety
```

3. Check service status:
```bash
sudo systemctl status orchestrator-safety
sudo journalctl -u orchestrator-safety -f
```

### Integration with Main HAL

The safety monitor operates independently but coordinates with the main HAL service:

1. **Start safety monitor first** to ensure safety coverage
2. **Main HAL subscribes** to emergency stop commands
3. **Safety monitor publishes** emergency stops when needed
4. **All components respect** emergency stop commands

## Testing

### Unit Tests

```bash
# Run unit tests
python -m pytest tests/test_safety_monitor.py -v

# Run with coverage
python -m pytest tests/test_safety_monitor.py --cov=hal_service.safety_monitor
```

### Integration Tests

```bash
# Run integration test (requires running MQTT broker)
python test_safety_integration.py
```

The integration test verifies:
- Safe LiDAR data handling
- Critical obstacle detection
- Warning obstacle handling
- Invalid data resilience
- Emergency stop command format

### Manual Testing

1. **Start MQTT broker**:
```bash
mosquitto -v
```

2. **Start safety monitor**:
```bash
python safety_monitor_service.py --log-level DEBUG
```

3. **Publish test LiDAR data**:
```bash
# Safe data
mosquitto_pub -t "orchestrator/data/lidar_01" -m '{"data": {"ranges": [2.0, 2.0, 2.0], "angles": [0, 90, 180], "timestamp": "2024-01-15T10:30:00Z"}}'

# Critical obstacle
mosquitto_pub -t "orchestrator/data/lidar_01" -m '{"data": {"ranges": [0.3, 2.0, 2.0], "angles": [0, 90, 180], "timestamp": "2024-01-15T10:30:00Z"}}'
```

4. **Monitor emergency stops**:
```bash
mosquitto_sub -t "orchestrator/cmd/estop"
```

## Performance Considerations

### Response Time Requirements

- **Target Response Time**: < 100ms from obstacle detection to emergency stop command
- **Maximum Processing Time**: < 50ms per LiDAR scan
- **MQTT Publish Time**: < 10ms for emergency stop commands

### System Resources

- **CPU Priority**: High priority (nice -10) for safety-critical operation
- **Memory Usage**: ~10-20MB typical, ~50MB maximum
- **Network**: Minimal bandwidth usage, QoS 1 for emergency stops

### Monitoring

The safety monitor tracks its own performance:

- Processing times for each LiDAR scan
- MQTT communication latency
- Memory and CPU usage (if psutil available)
- Emergency stop trigger frequency

## Troubleshooting

### Common Issues

1. **Safety monitor not starting**
   - Check MQTT broker connectivity
   - Verify configuration file format
   - Check permissions for high priority

2. **No emergency stops triggered**
   - Verify LiDAR data is being received
   - Check safety zone configuration
   - Monitor processing times

3. **False positive emergency stops**
   - Adjust obstacle threshold in configuration
   - Review safety zone definitions
   - Check LiDAR data quality

### Debugging

Enable debug logging for detailed information:

```bash
python safety_monitor_service.py --log-level DEBUG
```

Monitor MQTT traffic:

```bash
# Subscribe to all orchestrator topics
mosquitto_sub -t "orchestrator/+/+"

# Monitor safety-specific topics
mosquitto_sub -t "orchestrator/cmd/estop"
mosquitto_sub -t "orchestrator/status/safety_monitor"
```

Check system logs:

```bash
# For systemd service
sudo journalctl -u orchestrator-safety -f

# For standalone process
tail -f logs/safety_monitor.log
```

## Safety Considerations

### Fail-Safe Design

- **Independent Operation**: Safety monitor operates independently of main system
- **High Priority**: Runs at high system priority for guaranteed response time
- **Redundant Monitoring**: Multiple safety zones provide overlapping coverage
- **Graceful Degradation**: Continues operating even with partial sensor failures

### Limitations

- **Single Point of Failure**: Relies on single LiDAR sensor
- **Processing Delays**: Subject to system load and processing delays
- **False Positives**: May trigger on non-threatening objects (dust, insects)
- **Blind Spots**: Limited to LiDAR field of view and resolution

### Recommendations

1. **Regular Testing**: Test safety system regularly with known obstacles
2. **Sensor Maintenance**: Keep LiDAR sensor clean and properly calibrated
3. **Configuration Review**: Periodically review and adjust safety zone settings
4. **Backup Systems**: Consider additional safety sensors for redundancy
5. **Operator Training**: Ensure operators understand safety system behavior

## Requirements Compliance

This implementation satisfies the following requirements:

- **5.1**: Continuous LiDAR monitoring for proximity threats
- **5.2**: Immediate stop commands when obstacles detected within thresholds
- **5.3**: Safety overrides halt operations and report events
- **5.4**: Mission status updates indicate completion reason and final state

## Future Enhancements

Potential improvements for the safety monitor:

1. **Multi-Sensor Fusion**: Integrate additional sensors (cameras, ultrasonic)
2. **Machine Learning**: Use ML for better obstacle classification
3. **Predictive Safety**: Anticipate potential collisions based on trajectory
4. **Dynamic Zones**: Adjust safety zones based on robot speed and direction
5. **Remote Monitoring**: Web interface for safety system status and configuration