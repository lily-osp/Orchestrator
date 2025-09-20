# Node-RED Command Flows Implementation

## Overview

This document describes the implementation of Node-RED command flows that translate UI actions (button clicks, slider inputs) into formatted MQTT JSON commands for the Orchestrator robotics platform.

## Architecture

The command flows are organized into three main categories:

### 1. Motor Control Commands
- **Location**: Command Flows tab
- **UI Group**: Motor Control
- **MQTT Topic**: `orchestrator/cmd/motors`
- **QoS Level**: 1 (at-least-once delivery)

#### Available Actions:
- `move_forward` - Move robot forward by specified distance
- `move_backward` - Move robot backward by specified distance  
- `rotate_left` - Rotate robot left by specified angle
- `rotate_right` - Rotate robot right by specified angle
- `stop` - Immediately stop all motor movement

#### Parameters:
- **Distance**: 1-200 cm (for movement commands)
- **Angle**: 1-360 degrees (for rotation commands)
- **Speed**: 0.1-1.0 (fraction of maximum speed)

### 2. Mission Control Commands
- **Location**: Command Flows tab
- **UI Group**: Mission Control
- **MQTT Topic**: `orchestrator/cmd/mission`
- **QoS Level**: 1 (at-least-once delivery)

#### Available Actions:
- `start_mission` - Begin mission execution
- `pause_mission` - Pause current mission
- `stop_mission` - Stop current mission
- `reset_mission` - Reset mission to beginning

### 3. Emergency Stop Commands
- **Location**: Command Flows tab
- **UI Group**: Emergency Controls
- **MQTT Topic**: `orchestrator/cmd/estop`
- **QoS Level**: 2 (exactly-once delivery)

#### Action:
- `emergency_stop` - Immediately halt all robot operations

## Flow Architecture

### Parameter Management
1. **UI Sliders**: Distance, Angle, and Speed sliders provide parameter input
2. **Parameter Storage**: Function nodes store slider values in flow context
3. **Parameter Injection**: Command functions retrieve stored parameters and add them to commands

### Command Validation
Each command type has a dedicated validator function that:
- Validates action names against allowed values
- Checks parameter ranges and types
- Adds metadata (timestamp, command_id)
- Sets appropriate MQTT topic
- Logs validation results

### MQTT Publishing
Validated commands are published to appropriate MQTT topics with:
- Proper QoS levels for reliability
- JSON payload formatting
- Topic routing based on command type

## Message Format

All commands follow a standardized JSON format:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "command_id": "unique-message-id",
  "action": "move_forward",
  "parameters": {
    "distance": 100,
    "speed": 0.5
  },
  "priority": "normal"
}
```

### Emergency Stop Format:
```json
{
  "timestamp": "2025-01-15T10:30:00Z", 
  "command_id": "unique-message-id",
  "action": "emergency_stop",
  "reason": "user_initiated",
  "priority": "critical"
}
```

## Validation Rules

### Motor Commands
- **Action**: Must be one of the valid motor actions
- **Distance**: Number between 1-200 cm
- **Angle**: Number between 1-360 degrees
- **Speed**: Number between 0.1-1.0

### Mission Commands
- **Action**: Must be one of the valid mission actions
- No additional parameters required

### Emergency Commands
- **Action**: Always set to "emergency_stop"
- **Reason**: String describing the emergency cause
- **Priority**: Always set to "critical"

## Testing

The implementation includes a dedicated "Command Testing" tab with:
- Test injection nodes for each command type
- Validation test cases including invalid commands
- Debug output for verification
- Documentation comments explaining test scenarios

### Test Cases:
1. **Valid Motor Command**: Tests proper parameter validation
2. **Invalid Command**: Tests error handling for bad parameters
3. **Mission Command**: Tests mission control validation
4. **Emergency Stop**: Tests emergency command formatting

## Dashboard Integration

The flows integrate with Node-RED Dashboard to provide:
- **Dark Theme**: Professional appearance with glassmorphism elements
- **Responsive Layout**: Organized into logical control groups
- **Visual Feedback**: Color-coded buttons (green=start, red=stop/emergency, orange=pause)
- **Parameter Controls**: Sliders for distance, angle, and speed settings
- **Emergency Prominence**: Large, prominent emergency stop button

## Error Handling

The implementation includes comprehensive error handling:
- **Parameter Validation**: Range and type checking with error messages
- **Action Validation**: Verification against allowed action lists
- **Graceful Degradation**: Invalid commands are logged but don't crash flows
- **User Feedback**: Error messages appear in Node-RED debug sidebar

## Requirements Compliance

This implementation satisfies the following requirements:

### Requirement 3.1 (Visual Flow Editor)
✅ Provides drag-and-drop Node-RED interface for command creation

### Requirement 3.3 (Flow Execution)
✅ Flows publish appropriate MQTT commands to control robot behavior

### Requirement 7.1 (Standardized Communication)
✅ Uses consistent JSON message formats with defined schemas

## Usage Instructions

1. **Access Dashboard**: Navigate to `http://localhost:1880/ui`
2. **Set Parameters**: Use sliders to set distance, angle, and speed
3. **Execute Commands**: Click buttons to send commands to robot
4. **Monitor Output**: Check debug tab for command validation results
5. **Emergency Stop**: Use large red button for immediate halt

## File Structure

```
configs/node_red_config/
├── flows.json                    # Main flow definitions
├── settings.js                   # Node-RED configuration
├── COMMAND_FLOWS_README.md       # This documentation
└── package.json                  # Node dependencies
```

## Dependencies

The command flows require the following Node-RED nodes:
- `node-red-dashboard` - UI components
- `node-red-contrib-mqtt-broker` - MQTT communication (built-in)
- Standard Node-RED nodes (function, inject, debug)

## Future Enhancements

Potential improvements for future iterations:
1. **Command History**: Log and display recent commands
2. **Parameter Presets**: Save/load common parameter combinations
3. **Batch Commands**: Queue multiple commands for execution
4. **Visual Feedback**: Real-time status indicators
5. **Command Scheduling**: Time-based command execution