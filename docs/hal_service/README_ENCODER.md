# Encoder Sensor Implementation

This document describes the EncoderSensor class implementation for the Orchestrator platform, providing wheel encoder reading capabilities with GPIO interrupts for precise distance and velocity measurement.

## Overview

The EncoderSensor class inherits from the base Sensor class and provides:

- **GPIO Interrupt-based Counting**: Uses hardware interrupts for accurate pulse counting
- **Quadrature Encoding Support**: Supports both single-channel and dual-channel (A/B) encoders
- **Real-time Velocity Calculation**: Calculates velocity based on recent tick history
- **Distance Tracking**: Maintains cumulative distance traveled
- **MQTT Telemetry**: Publishes encoder data via MQTT at configurable rates
- **Direction Detection**: Automatically detects rotation direction (quadrature) or allows manual setting

## Requirements Covered

- **1.1**: Modular hardware abstraction through inheritance from base Sensor class
- **1.2**: Simple standardized interface with read_data() method
- **1.3**: Encapsulates GPIO interrupt handling within the class
- **2.2**: Publishes structured telemetry data via MQTT

## Configuration

### Single-Channel Encoder Configuration

```yaml
sensors:
  - name: "wheel_encoder"
    type: "encoder"
    interface:
      pin: 20
      mode: "IN"
      pull_up_down: "PUD_UP"
    publish_rate: 20.0
    calibration:
      resolution: 1000        # Pulses per revolution
      wheel_diameter: 0.1     # Wheel diameter in meters
      gear_ratio: 1.0         # Motor to wheel gear ratio
```

### Quadrature Encoder Configuration

```yaml
sensors:
  - name: "left_encoder"
    type: "encoder"
    interface:
      pin: 20  # Primary pin (used for interface)
      mode: "IN"
      pull_up_down: "PUD_UP"
    publish_rate: 20.0
    calibration:
      pin_a: 20               # Channel A pin
      pin_b: 21               # Channel B pin
      resolution: 1000        # Pulses per revolution
      wheel_diameter: 0.1     # Wheel diameter in meters
      gear_ratio: 1.0         # Motor to wheel gear ratio
      pull_up_down: "PUD_UP"  # Pull-up/down configuration
```

## Usage Example

```python
from hal_service.encoder_sensor import EncoderSensor
from hal_service.config import SensorConfig, GPIOConfig
from hal_service.mqtt_client import MQTTClientService

# Setup MQTT client
mqtt_client = MQTTClientService("localhost", 1883)
mqtt_client.connect()

# Create encoder configuration
config = SensorConfig(
    name="left_encoder",
    type="encoder",
    interface=GPIOConfig(pin=20, mode="IN", pull_up_down="PUD_UP"),
    publish_rate=20.0,
    calibration={
        "pin_a": 20,
        "pin_b": 21,
        "resolution": 1000,
        "wheel_diameter": 0.1,
        "gear_ratio": 1.0
    }
)

# Create and initialize encoder
encoder = EncoderSensor("left_encoder", mqtt_client, config)
if encoder.initialize():
    print("Encoder initialized successfully")
    
    # Read current data
    data = encoder.read_data()
    print(f"Ticks: {data['tick_count']}")
    print(f"Distance: {data['total_distance']:.3f} m")
    print(f"Velocity: {data['velocity']:.3f} m/s")
    print(f"RPM: {data['rpm']:.1f}")
```

## Data Output

The encoder publishes the following data structure via MQTT:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "device_id": "left_encoder",
  "data": {
    "tick_count": 1500,
    "total_distance": 0.471,
    "velocity": 0.25,
    "direction": 1,
    "rpm": 15.9,
    "distance_per_tick": 0.000314,
    "wheel_diameter": 0.1,
    "encoder_resolution": 1000,
    "gear_ratio": 1.0,
    "interrupt_count": 1500,
    "last_interrupt_time": 1642248600.123,
    "pins": {
      "encoder_a": 20,
      "encoder_b": 21
    }
  }
}
```

## MQTT Topics

### Telemetry Data
- **Topic**: `orchestrator/data/{encoder_id}`
- **QoS**: 0 (fire-and-forget)
- **Rate**: Configurable (default 20 Hz)

### Status Updates
- **Topic**: `orchestrator/status/{encoder_id}`
- **QoS**: 1 (at-least-once)
- **Content**: Device status, initialization state, error conditions

## Technical Details

### Interrupt Handling

The encoder uses GPIO interrupts on both rising and falling edges for maximum accuracy:

```python
GPIO.add_event_detect(
    encoder_pin_a,
    GPIO.BOTH,  # Both rising and falling edges
    callback=self._encoder_interrupt_a,
    bouncetime=1  # 1ms debounce
)
```

### Quadrature Decoding

For dual-channel encoders, direction is determined by the phase relationship between channels A and B:

- **Forward**: Channel A leads Channel B
- **Reverse**: Channel B leads Channel A

### Velocity Calculation

Velocity is calculated using a sliding window approach:

1. Store recent tick timestamps in a circular buffer
2. Calculate distance change over time window (default 100ms)
3. Smooth velocity using recent measurements

### Distance Calculation

Distance is calculated based on encoder resolution and wheel parameters:

```python
wheel_circumference = π × wheel_diameter
distance_per_tick = (wheel_circumference / encoder_resolution) / gear_ratio
total_distance = tick_count × distance_per_tick
```

## Error Handling

### GPIO Errors
- Graceful handling of GPIO setup failures
- Automatic cleanup of interrupt handlers
- Fallback to mock GPIO for development environments

### Interrupt Errors
- Exception handling within interrupt callbacks
- Logging of interrupt processing errors
- Continued operation despite occasional interrupt failures

### Timing Errors
- Protection against division by zero in velocity calculations
- Handling of system clock changes
- Timeout protection for velocity calculations

## Performance Considerations

### Interrupt Frequency
- Designed to handle up to 10kHz interrupt rates
- Minimal processing in interrupt handlers
- Thread-safe data structures for concurrent access

### Memory Usage
- Circular buffer for velocity calculation (limited size)
- Efficient data structures for tick tracking
- Automatic cleanup of old velocity data

### CPU Usage
- Lightweight interrupt processing
- Configurable publishing rates to balance accuracy vs. CPU usage
- Efficient MQTT message formatting

## Testing

### Unit Tests
Run the encoder sensor tests:

```bash
python -m pytest tests/test_encoder_sensor.py -v
```

### Hardware Testing
Use the example script for hardware validation:

```bash
python hal_service/encoder_example.py
```

### Integration Testing
Test with motor controller for complete motion feedback:

```bash
python tests/test_motor_encoder_integration.py
```

## Troubleshooting

### Common Issues

1. **No Encoder Counts**
   - Check GPIO pin connections
   - Verify pull-up/pull-down configuration
   - Ensure encoder power supply is stable
   - Check for proper grounding

2. **Incorrect Direction**
   - Verify channel A and B pin assignments
   - Check encoder wiring (may need to swap A/B)
   - For single-channel encoders, use `set_direction()` method

3. **Erratic Velocity Readings**
   - Check for electrical noise on encoder lines
   - Increase debounce time if necessary
   - Verify encoder resolution matches configuration
   - Check for loose connections

4. **MQTT Publishing Issues**
   - Verify MQTT broker connection
   - Check topic permissions
   - Monitor MQTT logs for connection errors
   - Validate JSON message format

### Debug Mode

Enable debug logging for detailed encoder information:

```python
import logging
logging.getLogger('hal_service.encoder_sensor').setLevel(logging.DEBUG)
```

### Performance Monitoring

Monitor encoder performance metrics:

```python
status = encoder.get_status()
print(f"Interrupt count: {status['interrupt_count']}")
print(f"Last interrupt: {status['last_interrupt_time']}")
```

## Hardware Compatibility

### Supported Encoders
- Incremental rotary encoders
- Quadrature encoders (A/B channels)
- Single-channel pulse encoders
- Magnetic encoders
- Optical encoders

### GPIO Requirements
- Raspberry Pi GPIO pins
- 3.3V or 5V logic levels (with appropriate level shifting)
- Pull-up resistors (internal or external)
- Debouncing capability (hardware or software)

### Recommended Hardware
- **Encoders**: 1000+ PPR for good resolution
- **Connectors**: Shielded cables for noise immunity
- **Power**: Stable 5V supply for encoder electronics
- **Grounding**: Common ground between encoder and Raspberry Pi

## Future Enhancements

### Planned Features
- Absolute encoder support
- Multi-turn counting with overflow protection
- Advanced filtering for noisy environments
- Calibration wizard for automatic setup
- Web-based configuration interface

### Performance Improvements
- Hardware-accelerated counting (using dedicated counter chips)
- DMA-based data collection for high-frequency encoders
- Real-time priority interrupt handling
- Optimized data structures for memory efficiency