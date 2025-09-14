# LiDAR Sensor Implementation

This document describes the LiDAR sensor implementation for the Orchestrator platform, providing 2D scanning capabilities for obstacle detection and navigation.

## Overview

The `LidarSensor` class provides a complete implementation for 2D LiDAR devices with the following features:

- **UART/USB Communication**: Configurable serial communication with LiDAR devices
- **Real-time Scanning**: Continuous 360-degree scanning with configurable rates
- **Obstacle Detection**: Built-in obstacle detection with zone-based monitoring
- **MQTT Integration**: Automatic publishing of scan data to MQTT topics
- **Safety Monitoring**: Real-time proximity detection for safety systems
- **Performance Tracking**: Comprehensive metrics and error tracking

## Requirements Covered

This implementation satisfies the following requirements:

- **1.1**: Modular hardware abstraction through inheritance from `Sensor` base class
- **1.2**: Encapsulated UART/USB protocol communication within the LiDAR class
- **1.3**: Standardized interface with methods like `get_current_scan()` and `is_obstacle_detected()`
- **5.1**: Continuous LiDAR data monitoring for proximity threats
- **5.2**: Immediate obstacle detection within configurable safety thresholds

## Architecture

### Class Hierarchy

```
Device (base.py)
└── Sensor (base.py)
    └── LidarSensor (lidar_sensor.py)
```

### Data Structures

#### LidarScan
```python
@dataclass
class LidarScan:
    timestamp: datetime
    ranges: List[float]      # Distance measurements in meters
    angles: List[float]      # Angle measurements in degrees
    min_range: float         # Minimum valid range
    max_range: float         # Maximum valid range
    scan_time: float         # Scan duration in seconds
    quality: List[int]       # Signal quality (0-255)
```

## Configuration

### YAML Configuration Example

```yaml
sensors:
  - name: lidar_01
    type: lidar
    interface:
      port: /dev/ttyUSB0
      baudrate: 115200
      timeout: 1.0
      bytesize: 8
      parity: N
      stopbits: 1
    publish_rate: 10.0
    calibration:
      min_range: 0.15        # Minimum detection range (meters)
      max_range: 12.0        # Maximum detection range (meters)
      angle_resolution: 1.0   # Angular resolution (degrees)
      scan_frequency: 10.0    # Scan rate (Hz)
      quality_threshold: 10   # Minimum signal quality
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | string | `/dev/ttyUSB0` | Serial port path |
| `baudrate` | int | `115200` | Serial communication speed |
| `timeout` | float | `1.0` | Read timeout in seconds |
| `min_range` | float | `0.15` | Minimum valid range in meters |
| `max_range` | float | `12.0` | Maximum valid range in meters |
| `scan_frequency` | float | `10.0` | Scan rate in Hz |
| `publish_rate` | float | `10.0` | MQTT publish rate in Hz |

## Usage

### Basic Usage

```python
from hal_service.lidar_sensor import LidarSensor
from hal_service.config import ConfigurationService

# Load configuration
config_service = ConfigurationService()
config = config_service.load_config()
lidar_config = config_service.get_sensor_config("lidar_01")

# Create and initialize sensor
lidar = LidarSensor("lidar_01", mqtt_client, lidar_config)
if lidar.initialize():
    print("LiDAR initialized successfully")
    
    # Get current scan data
    scan_data = lidar.read_data()
    if scan_data["scan_available"]:
        print(f"Scan has {scan_data['num_points']} points")
        print(f"Closest obstacle: {scan_data['closest_obstacle']['distance']:.2f}m")
    
    # Check for obstacles
    obstacle_detected = lidar.is_obstacle_detected(
        min_distance=0.5,
        angle_range=(-30, 30)  # Front zone
    )
    
    if obstacle_detected:
        print("Obstacle detected in front zone!")
```

### Advanced Usage

```python
# Get raw scan object
current_scan = lidar.get_current_scan()
if current_scan:
    # Find closest obstacle
    closest_dist, closest_angle = current_scan.get_closest_obstacle()
    
    # Get obstacles in specific zones
    front_obstacles = current_scan.get_obstacles_in_zone(-45, 45, 2.0)
    left_obstacles = current_scan.get_obstacles_in_zone(60, 120, 2.0)
    
    print(f"Front zone has {len(front_obstacles)} obstacles")
    print(f"Left zone has {len(left_obstacles)} obstacles")

# Monitor sensor status
status = lidar.get_status()
print(f"Scan count: {status['scan_count']}")
print(f"Error rate: {status['scan_errors']}/{status['scan_count']}")
```

## MQTT Integration

### Published Topics

The LiDAR sensor publishes data to the following MQTT topics:

#### Data Topic: `orchestrator/data/{device_id}`

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "device_id": "lidar_01",
  "data": {
    "scan_available": true,
    "ranges": [1.2, 1.5, 0.8, 2.1, ...],
    "angles": [0, 1, 2, 3, ...],
    "quality": [200, 180, 150, 220, ...],
    "min_range": 0.15,
    "max_range": 12.0,
    "scan_time": 0.1,
    "num_points": 360,
    "closest_obstacle": {
      "distance": 0.8,
      "angle": 270
    },
    "obstacle_zones": {
      "front": 2,
      "left": 0,
      "right": 1,
      "rear": 0
    },
    "scan_statistics": {
      "scan_count": 1250,
      "scan_errors": 3,
      "communication_errors": 1,
      "last_scan_time": 1642248600.123,
      "last_successful_scan": 1642248600.125
    }
  }
}
```

#### Status Topic: `orchestrator/status/{device_id}`

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "device_id": "lidar_01",
  "status": "ready",
  "initialized": true,
  "scanning": true,
  "scan_count": 1250,
  "connection": {
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "connected": true
  }
}
```

## Obstacle Detection

### Zone-Based Detection

The LiDAR sensor supports zone-based obstacle detection:

```python
# Define safety zones (angles in degrees)
FRONT_ZONE = (-30, 30)
LEFT_ZONE = (60, 120)
RIGHT_ZONE = (240, 300)
REAR_ZONE = (150, 210)

# Check for obstacles in each zone
safety_distance = 0.5  # meters

front_clear = not lidar.is_obstacle_detected(safety_distance, FRONT_ZONE)
left_clear = not lidar.is_obstacle_detected(safety_distance, LEFT_ZONE)
right_clear = not lidar.is_obstacle_detected(safety_distance, RIGHT_ZONE)
rear_clear = not lidar.is_obstacle_detected(safety_distance, REAR_ZONE)
```

### Safety Integration

For safety systems, the LiDAR can be used for real-time monitoring:

```python
def safety_monitor_loop():
    while running:
        # Check for immediate threats
        emergency_distance = 0.3  # meters
        emergency_zone = (-45, 45)  # degrees
        
        if lidar.is_obstacle_detected(emergency_distance, emergency_zone):
            # Publish emergency stop command
            mqtt_client.publish("orchestrator/cmd/estop", {
                "action": "emergency_stop",
                "reason": "obstacle_detected",
                "distance": lidar.get_current_scan().get_closest_obstacle()[0]
            })
        
        time.sleep(0.1)  # 10Hz monitoring
```

## Performance Monitoring

### Metrics Tracked

The LiDAR sensor tracks several performance metrics:

- **Scan Count**: Total number of completed scans
- **Scan Errors**: Failed scan attempts
- **Communication Errors**: Serial communication failures
- **Scan Time**: Time taken for each complete scan
- **Error Rate**: Percentage of failed operations

### Performance Optimization

```python
# Monitor performance
status = lidar.get_status()
scan_count = status['scan_count']
scan_errors = status['scan_errors']
comm_errors = status['communication_errors']

error_rate = (scan_errors + comm_errors) / max(scan_count, 1) * 100

if error_rate > 5.0:  # 5% error threshold
    logger.warning(f"High LiDAR error rate: {error_rate:.1f}%")
    
    # Check connection
    if not status['connection']['connected']:
        logger.error("LiDAR connection lost - attempting reconnection")
        lidar.stop()
        time.sleep(1.0)
        lidar.initialize()
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
python -m pytest tests/test_lidar_sensor.py -v
```

### Basic Tests (No Dependencies)

For environments without pytest:

```bash
python test_lidar_basic.py
```

### Example Application

Run the interactive example:

```bash
python hal_service/lidar_example.py config.yaml --interactive
```

Available commands in interactive mode:
- `status` - Show sensor status
- `scan` - Display current scan data
- `obstacles` - Show obstacle detection info
- `config` - Show sensor configuration
- `help` - Show available commands

## Troubleshooting

### Common Issues

#### Serial Connection Problems

```
Error: Failed to initialize LiDAR sensor
```

**Solutions:**
1. Check device permissions: `sudo chmod 666 /dev/ttyUSB0`
2. Verify device exists: `ls -la /dev/ttyUSB*`
3. Check if device is in use: `lsof /dev/ttyUSB0`
4. Try different baud rates: 9600, 57600, 115200, 230400

#### No Scan Data

```
Warning: No scan data available
```

**Solutions:**
1. Check if LiDAR is spinning (for mechanical LiDARs)
2. Verify power supply is adequate
3. Check serial communication settings
4. Review LiDAR-specific protocol documentation

#### High Error Rate

```
Warning: High LiDAR error rate: 15.2%
```

**Solutions:**
1. Check serial cable quality and connections
2. Reduce scan frequency if CPU is overloaded
3. Verify power supply stability
4. Check for electromagnetic interference

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('hal_service.lidar_sensor').setLevel(logging.DEBUG)
```

### Hardware Compatibility

This implementation provides a generic LiDAR interface. For specific LiDAR models, you may need to:

1. Modify the protocol constants (`START_BYTE`, `SCAN_COMMAND`, etc.)
2. Update the `_parse_scan_data()` method for device-specific data formats
3. Adjust timing parameters for device-specific requirements

## Integration Examples

### With Safety System

```python
class SafetyMonitor:
    def __init__(self, lidar_sensor, mqtt_client):
        self.lidar = lidar_sensor
        self.mqtt = mqtt_client
        self.safety_distance = 0.5  # meters
        
    def monitor_loop(self):
        while self.running:
            if self.lidar.is_obstacle_detected(self.safety_distance, (-45, 45)):
                self.trigger_emergency_stop()
            time.sleep(0.05)  # 20Hz monitoring
    
    def trigger_emergency_stop(self):
        self.mqtt.publish("orchestrator/cmd/estop", {
            "action": "emergency_stop",
            "reason": "lidar_obstacle_detected",
            "timestamp": datetime.now().isoformat()
        })
```

### With Navigation System

```python
class NavigationPlanner:
    def __init__(self, lidar_sensor):
        self.lidar = lidar_sensor
        
    def plan_path(self):
        scan = self.lidar.get_current_scan()
        if not scan:
            return None
            
        # Find clear corridors
        clear_zones = []
        for angle in range(0, 360, 10):
            obstacles = scan.get_obstacles_in_zone(angle-5, angle+5, 2.0)
            if len(obstacles) == 0:
                clear_zones.append(angle)
        
        return clear_zones
```

## API Reference

### LidarSensor Class

#### Methods

- `initialize() -> bool`: Initialize the LiDAR sensor
- `start_scanning() -> bool`: Start continuous scanning
- `stop_scanning() -> None`: Stop scanning
- `read_data() -> Dict[str, Any]`: Get current scan data
- `get_current_scan() -> Optional[LidarScan]`: Get raw scan object
- `is_obstacle_detected(min_distance, angle_range) -> bool`: Check for obstacles
- `get_status() -> Dict[str, Any]`: Get sensor status
- `stop() -> None`: Stop sensor and cleanup

#### Properties

- `device_id`: Unique sensor identifier
- `scanning`: Whether sensor is currently scanning
- `scan_count`: Total number of scans completed
- `scan_errors`: Number of scan errors
- `min_range`: Minimum detection range in meters
- `max_range`: Maximum detection range in meters

### LidarScan Class

#### Methods

- `get_closest_obstacle() -> Tuple[float, float]`: Get closest obstacle distance and angle
- `get_obstacles_in_zone(min_angle, max_angle, max_distance) -> List[Tuple[float, float]]`: Get obstacles in zone

#### Properties

- `ranges`: List of distance measurements
- `angles`: List of angle measurements  
- `quality`: List of signal quality values
- `timestamp`: Scan timestamp
- `scan_time`: Time taken for scan

## Future Enhancements

1. **Multi-LiDAR Support**: Coordinate multiple LiDAR sensors
2. **Point Cloud Generation**: Generate 3D point clouds from 2D scans
3. **SLAM Integration**: Support for simultaneous localization and mapping
4. **Advanced Filtering**: Kalman filtering for noise reduction
5. **Calibration Tools**: Automatic calibration and alignment tools