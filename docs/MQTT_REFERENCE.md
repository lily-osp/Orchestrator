# MQTT Communication Reference

This document provides a complete reference for the MQTT communication protocol used in the Orchestrator Platform.

## Table of Contents

- [Overview](#overview)
- [Topic Structure](#topic-structure)
- [Message Schemas](#message-schemas)
- [Command Messages](#command-messages)
- [Telemetry Messages](#telemetry-messages)
- [Status Messages](#status-messages)
- [Quality of Service](#quality-of-service)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview

The Orchestrator Platform uses MQTT as the primary communication protocol between the Hardware Abstraction Layer (HAL), Node-RED control flows, and external systems. All messages use JSON formatting for structured data exchange.

### MQTT Broker Configuration

- **Broker**: Mosquitto (default)
- **Host**: localhost (configurable)
- **Port**: 1883 (standard MQTT)
- **Authentication**: Optional (configurable)
- **Encryption**: Optional TLS support

### Message Format Standards

All MQTT messages follow these conventions:

- **Encoding**: UTF-8
- **Format**: JSON
- **Timestamps**: ISO 8601 format (UTC)
- **Units**: Metric system (meters, seconds, degrees)
- **Coordinate System**: Right-hand coordinate system (X: forward, Y: left, Z: up)

## Topic Structure

The topic hierarchy follows a structured naming convention:

```
orchestrator/
├── cmd/                    # Command topics (QoS 1)
│   ├── motors             # Motor control commands
│   ├── sensors            # Sensor configuration commands
│   ├── safety             # Safety system commands
│   ├── mission            # Mission control commands
│   └── system             # System-level commands
├── data/                  # Telemetry data topics (QoS 0)
│   ├── lidar              # LiDAR sensor data
│   ├── encoders           # Encoder sensor data
│   ├── motors             # Motor status data
│   ├── sensors            # General sensor data
│   └── system             # System telemetry
├── status/                # Status update topics (QoS 1)
│   ├── robot              # Overall robot status
│   ├── mission            # Mission execution status
│   ├── safety             # Safety system status
│   ├── services           # Service health status
│   └── system             # System health status
├── events/                # Event notification topics (QoS 1)
│   ├── alerts             # System alerts and warnings
│   ├── errors             # Error notifications
│   ├── safety             # Safety events
│   └── mission            # Mission events
└── config/                # Configuration topics (QoS 1)
    ├── hardware           # Hardware configuration
    ├── safety             # Safety parameters
    ├── mission            # Mission parameters
    └── system             # System configuration
```

### Topic Naming Conventions

- **Lowercase**: All topic names use lowercase letters
- **Underscores**: Use underscores for multi-word topics
- **Hierarchical**: Logical grouping with forward slashes
- **Descriptive**: Clear, meaningful topic names
- **Consistent**: Standardized naming across all components

## Message Schemas

### Base Message Schema

All messages include common fields:

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "component_name",
  "version": "1.0"
}
```

**Field Descriptions**:
- `timestamp`: Message creation time (ISO 8601 UTC)
- `message_id`: Unique identifier for message tracking
- `source`: Component that generated the message
- `version`: Message schema version

### Error Message Schema

Error messages follow a standardized format:

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "component_name",
  "version": "1.0",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error description",
    "details": {
      "component": "specific_component",
      "operation": "failed_operation",
      "parameters": {}
    },
    "severity": "low|medium|high|critical",
    "recoverable": true
  }
}
```

## Command Messages

Commands are sent to control robot behavior and configure system parameters.

### Motor Control Commands

**Topic**: `orchestrator/cmd/motors`

#### Move Forward Command
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "node_red_dashboard",
  "version": "1.0",
  "command": {
    "action": "move_forward",
    "parameters": {
      "distance": 1.5,
      "speed": 0.5,
      "acceleration": 0.2,
      "timeout": 30.0
    }
  }
}
```

#### Rotate Command
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "node_red_dashboard",
  "version": "1.0",
  "command": {
    "action": "rotate",
    "parameters": {
      "angle": 90.0,
      "angular_speed": 0.3,
      "direction": "clockwise",
      "timeout": 15.0
    }
  }
}
```

#### Stop Command
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "safety_monitor",
  "version": "1.0",
  "command": {
    "action": "stop",
    "parameters": {
      "emergency": false,
      "deceleration": 0.5
    }
  }
}
```

#### Emergency Stop Command
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "safety_monitor",
  "version": "1.0",
  "command": {
    "action": "emergency_stop",
    "parameters": {
      "reason": "obstacle_detected",
      "immediate": true
    }
  }
}
```

### Mission Control Commands

**Topic**: `orchestrator/cmd/mission`

#### Start Mission Command
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "node_red_dashboard",
  "version": "1.0",
  "command": {
    "action": "start_mission",
    "parameters": {
      "mission_id": "waypoint_navigation_001",
      "mission_name": "Warehouse Survey",
      "waypoints": [
        {"x": 0.0, "y": 0.0, "heading": 0.0},
        {"x": 2.0, "y": 0.0, "heading": 90.0},
        {"x": 2.0, "y": 2.0, "heading": 180.0},
        {"x": 0.0, "y": 2.0, "heading": 270.0}
      ],
      "speed": 0.3,
      "safety_margin": 0.5,
      "timeout": 300.0
    }
  }
}
```

#### Pause Mission Command
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "node_red_dashboard",
  "version": "1.0",
  "command": {
    "action": "pause_mission",
    "parameters": {
      "mission_id": "waypoint_navigation_001",
      "reason": "user_request"
    }
  }
}
```

### Safety System Commands

**Topic**: `orchestrator/cmd/safety`

#### Configure Safety Parameters
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "node_red_dashboard",
  "version": "1.0",
  "command": {
    "action": "configure_safety",
    "parameters": {
      "stop_distance": 0.3,
      "slow_distance": 0.5,
      "warning_distance": 1.0,
      "max_speed": 1.0,
      "emergency_deceleration": 2.0
    }
  }
}
```

### Sensor Configuration Commands

**Topic**: `orchestrator/cmd/sensors`

#### Configure LiDAR
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "node_red_dashboard",
  "version": "1.0",
  "command": {
    "action": "configure_lidar",
    "parameters": {
      "scan_rate": 10.0,
      "angle_min": -180.0,
      "angle_max": 180.0,
      "range_min": 0.1,
      "range_max": 10.0,
      "filter_enabled": true
    }
  }
}
```

## Telemetry Messages

Telemetry messages provide real-time sensor data and system information.

### LiDAR Data

**Topic**: `orchestrator/data/lidar`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "lidar_sensor",
  "version": "1.0",
  "data": {
    "scan_id": 12345,
    "scan_time": 0.1,
    "angle_min": -180.0,
    "angle_max": 180.0,
    "angle_increment": 1.0,
    "range_min": 0.1,
    "range_max": 10.0,
    "ranges": [1.2, 1.5, 0.8, 2.1, 3.4, 1.9],
    "intensities": [100, 95, 120, 85, 75, 110],
    "quality": "good",
    "obstacles_detected": [
      {
        "angle": 45.0,
        "distance": 0.8,
        "size": 0.2,
        "confidence": 0.95
      }
    ]
  }
}
```

### Encoder Data

**Topic**: `orchestrator/data/encoders`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "encoder_sensor",
  "version": "1.0",
  "data": {
    "left_encoder": {
      "count": 1234,
      "delta": 5,
      "velocity": 0.5,
      "direction": "forward"
    },
    "right_encoder": {
      "count": 1230,
      "delta": 4,
      "velocity": 0.48,
      "direction": "forward"
    },
    "odometry": {
      "distance_traveled": 2.45,
      "heading_change": 2.3,
      "linear_velocity": 0.49,
      "angular_velocity": 0.02
    }
  }
}
```

### Motor Status Data

**Topic**: `orchestrator/data/motors`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "motor_controller",
  "version": "1.0",
  "data": {
    "left_motor": {
      "speed": 0.5,
      "direction": "forward",
      "current": 1.2,
      "temperature": 35.5,
      "status": "running"
    },
    "right_motor": {
      "speed": 0.48,
      "direction": "forward",
      "current": 1.1,
      "temperature": 34.8,
      "status": "running"
    },
    "power": {
      "voltage": 12.1,
      "total_current": 2.3,
      "power_consumption": 27.8
    }
  }
}
```

### System Telemetry

**Topic**: `orchestrator/data/system`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "system_monitor",
  "version": "1.0",
  "data": {
    "cpu": {
      "usage_percent": 25.3,
      "temperature": 45.2,
      "frequency": 1500
    },
    "memory": {
      "total": 4096,
      "used": 1024,
      "available": 3072,
      "usage_percent": 25.0
    },
    "disk": {
      "total": 32768,
      "used": 8192,
      "available": 24576,
      "usage_percent": 25.0
    },
    "network": {
      "interface": "wlan0",
      "ip_address": "192.168.1.100",
      "signal_strength": -45,
      "bytes_sent": 1048576,
      "bytes_received": 2097152
    }
  }
}
```

## Status Messages

Status messages provide information about system state and component health.

### Robot Status

**Topic**: `orchestrator/status/robot`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "state_manager",
  "version": "1.0",
  "status": {
    "state": "active",
    "mode": "autonomous",
    "position": {
      "x": 1.25,
      "y": 0.75,
      "heading": 45.0,
      "confidence": 0.95
    },
    "velocity": {
      "linear": 0.5,
      "angular": 0.1
    },
    "battery": {
      "voltage": 12.1,
      "percentage": 85,
      "estimated_runtime": 3600
    },
    "health": {
      "overall": "good",
      "components": {
        "motors": "good",
        "sensors": "good",
        "communication": "good",
        "safety": "good"
      }
    }
  }
}
```

### Mission Status

**Topic**: `orchestrator/status/mission`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "mission_controller",
  "version": "1.0",
  "status": {
    "mission_id": "waypoint_navigation_001",
    "mission_name": "Warehouse Survey",
    "state": "in_progress",
    "progress": {
      "current_step": 2,
      "total_steps": 4,
      "percentage": 50.0,
      "estimated_completion": "2024-01-15T10:35:00.000Z"
    },
    "current_waypoint": {
      "index": 1,
      "target": {"x": 2.0, "y": 0.0, "heading": 90.0},
      "distance_remaining": 0.3,
      "eta": 15.0
    },
    "performance": {
      "start_time": "2024-01-15T10:28:00.000Z",
      "elapsed_time": 120.0,
      "average_speed": 0.4,
      "distance_traveled": 1.8
    }
  }
}
```

### Safety Status

**Topic**: `orchestrator/status/safety`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "safety_monitor",
  "version": "1.0",
  "status": {
    "state": "monitoring",
    "emergency_stop": false,
    "obstacles": [
      {
        "id": "obs_001",
        "angle": 45.0,
        "distance": 0.8,
        "severity": "warning",
        "action": "slow_down"
      }
    ],
    "safety_zones": {
      "stop_zone": false,
      "slow_zone": true,
      "warning_zone": true
    },
    "watchdog": {
      "communication": "active",
      "sensors": "active",
      "motors": "active",
      "last_heartbeat": "2024-01-15T10:29:59.000Z"
    }
  }
}
```

### Service Health Status

**Topic**: `orchestrator/status/services`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "service_monitor",
  "version": "1.0",
  "status": {
    "services": {
      "hal_service": {
        "status": "running",
        "pid": 1234,
        "uptime": 3600,
        "cpu_usage": 15.2,
        "memory_usage": 128,
        "last_heartbeat": "2024-01-15T10:29:59.000Z"
      },
      "safety_monitor": {
        "status": "running",
        "pid": 1235,
        "uptime": 3598,
        "cpu_usage": 8.5,
        "memory_usage": 64,
        "last_heartbeat": "2024-01-15T10:29:59.500Z"
      },
      "state_manager": {
        "status": "running",
        "pid": 1236,
        "uptime": 3595,
        "cpu_usage": 5.1,
        "memory_usage": 48,
        "last_heartbeat": "2024-01-15T10:29:58.800Z"
      }
    },
    "overall_health": "good"
  }
}
```

## Quality of Service

### QoS Level Guidelines

**QoS 0 (At most once)**:
- Telemetry data (`orchestrator/data/*`)
- High-frequency sensor readings
- Non-critical status updates

**QoS 1 (At least once)**:
- Commands (`orchestrator/cmd/*`)
- Status updates (`orchestrator/status/*`)
- Event notifications (`orchestrator/events/*`)
- Configuration changes (`orchestrator/config/*`)

**QoS 2 (Exactly once)**:
- Not typically used (performance overhead)
- Reserved for critical safety commands if needed

### Retained Messages

Certain topics use retained messages for state persistence:

- `orchestrator/status/robot` - Last known robot state
- `orchestrator/status/mission` - Current mission status
- `orchestrator/config/*` - Configuration parameters

## Error Handling

### Command Acknowledgment

Commands should be acknowledged with response messages:

**Topic**: `orchestrator/status/command_ack`

```json
{
  "timestamp": "2024-01-15T10:30:01.000Z",
  "message_id": "uuid-v4-string",
  "source": "motor_controller",
  "version": "1.0",
  "acknowledgment": {
    "original_message_id": "original-uuid-v4-string",
    "command": "move_forward",
    "status": "accepted|rejected|completed|failed",
    "result": {
      "success": true,
      "message": "Command executed successfully",
      "execution_time": 2.5
    },
    "error": {
      "code": "INVALID_PARAMETER",
      "message": "Speed parameter out of range",
      "details": {"parameter": "speed", "value": 1.5, "max": 1.0}
    }
  }
}
```

### Error Notifications

**Topic**: `orchestrator/events/errors`

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "message_id": "uuid-v4-string",
  "source": "lidar_sensor",
  "version": "1.0",
  "error": {
    "code": "SENSOR_TIMEOUT",
    "message": "LiDAR sensor communication timeout",
    "severity": "high",
    "component": "lidar_sensor",
    "operation": "read_scan",
    "details": {
      "timeout_duration": 5.0,
      "last_successful_read": "2024-01-15T10:29:55.000Z",
      "retry_count": 3
    },
    "recovery_action": "restart_sensor",
    "user_action_required": false
  }
}
```

## Examples

### Complete Command Flow Example

1. **User clicks "Move Forward" in dashboard**
2. **Node-RED publishes command**:
   ```bash
   mosquitto_pub -h localhost -t orchestrator/cmd/motors -m '{
     "timestamp": "2024-01-15T10:30:00.123Z",
     "message_id": "cmd-001",
     "source": "node_red_dashboard",
     "version": "1.0",
     "command": {
       "action": "move_forward",
       "parameters": {"distance": 1.0, "speed": 0.5}
     }
   }'
   ```

3. **HAL acknowledges command**:
   ```bash
   # Published to: orchestrator/status/command_ack
   {
     "timestamp": "2024-01-15T10:30:00.200Z",
     "message_id": "ack-001",
     "source": "motor_controller",
     "version": "1.0",
     "acknowledgment": {
       "original_message_id": "cmd-001",
       "command": "move_forward",
       "status": "accepted"
     }
   }
   ```

4. **HAL publishes telemetry during execution**:
   ```bash
   # Published to: orchestrator/data/encoders (continuous)
   {
     "timestamp": "2024-01-15T10:30:01.000Z",
     "data": {
       "odometry": {"distance_traveled": 0.1, "linear_velocity": 0.5}
     }
   }
   ```

5. **HAL publishes completion status**:
   ```bash
   # Published to: orchestrator/status/command_ack
   {
     "acknowledgment": {
       "original_message_id": "cmd-001",
       "status": "completed",
       "result": {"success": true, "execution_time": 2.0}
     }
   }
   ```

### Testing MQTT Communication

#### Subscribe to All Topics
```bash
mosquitto_sub -h localhost -t "orchestrator/#" -v
```

#### Test Command Publishing
```bash
# Test motor command
mosquitto_pub -h localhost -t orchestrator/cmd/motors -m '{
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
  "message_id": "test-001",
  "source": "test_client",
  "version": "1.0",
  "command": {
    "action": "stop",
    "parameters": {}
  }
}'
```

#### Monitor Specific Data Stream
```bash
# Monitor LiDAR data
mosquitto_sub -h localhost -t orchestrator/data/lidar -v

# Monitor robot status
mosquitto_sub -h localhost -t orchestrator/status/robot -v
```

### Message Validation

All messages should be validated against their schemas. Example validation tools:

#### Python Validation
```python
import json
import jsonschema

# Load message schema
with open('schemas/motor_command.json', 'r') as f:
    schema = json.load(f)

# Validate message
try:
    jsonschema.validate(message, schema)
    print("Message is valid")
except jsonschema.ValidationError as e:
    print(f"Validation error: {e.message}")
```

#### Node-RED Validation
Use JSON schema validation nodes in Node-RED flows to ensure message integrity.

---

## Best Practices

### Message Design
- Keep messages concise but complete
- Use consistent field names across message types
- Include sufficient metadata for debugging
- Implement proper error handling

### Topic Organization
- Use hierarchical topic structure
- Group related topics logically
- Avoid deep nesting (max 4 levels)
- Use descriptive topic names

### Performance Optimization
- Use appropriate QoS levels
- Implement message batching for high-frequency data
- Use retained messages for state information
- Monitor message throughput and latency

### Security Considerations
- Implement MQTT authentication when needed
- Use TLS encryption for sensitive data
- Validate all incoming messages
- Implement access control for topic publishing

---

*This reference document covers the complete MQTT communication protocol for the Orchestrator Platform. For implementation examples, see the component documentation in `docs/hal_service/`.*