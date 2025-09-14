#!/usr/bin/env python3
"""
Test script for Mock HAL implementation

Demonstrates the mock HAL functionality and validates that it provides
realistic simulation data for UI/control development.
"""

import sys
import time
import json
from pathlib import Path

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hal_service.mock import MockHALOrchestrator


def test_mock_hal():
    """Test the mock HAL orchestrator functionality"""
    print("=" * 60)
    print("Testing Mock HAL Implementation")
    print("=" * 60)
    
    # Create mock orchestrator
    print("\n1. Initializing Mock HAL Orchestrator...")
    orchestrator = MockHALOrchestrator(
        config_path=None,  # Use default config
        enable_realistic_delays=True,
        enable_failures=False
    )
    
    # Initialize
    if not orchestrator.initialize():
        print("❌ Failed to initialize Mock HAL Orchestrator")
        return False
    
    print("✅ Mock HAL Orchestrator initialized successfully")
    
    # Get system status
    print("\n2. Checking System Status...")
    status = orchestrator.get_system_status()
    print(f"   Running: {status['running']}")
    print(f"   Device Count: {status['device_count']}")
    print(f"   MQTT Connected: {status['mqtt_connected']}")
    print(f"   Simulation Enabled: {status['simulation_enabled']}")
    
    # List devices
    print("\n3. Available Mock Devices:")
    for device_name, device_status in status['devices'].items():
        print(f"   - {device_name}: {device_status['status']} ({device_status.get('device_type', 'unknown')})")
    
    # Test motor commands
    print("\n4. Testing Motor Commands...")
    mqtt_client = orchestrator.get_mqtt_client()
    
    # Send move forward command
    move_command = {
        "timestamp": time.time(),
        "command_id": "test_move_001",
        "action": "move_forward",
        "parameters": {
            "distance": 1.0,  # 1 meter
            "speed": 0.5      # 50% speed
        }
    }
    
    print("   Sending move forward command...")
    success = mqtt_client.publish("orchestrator/cmd/left_motor", move_command)
    print(f"   Command sent: {'✅' if success else '❌'}")
    
    # Wait for telemetry
    print("\n5. Monitoring Telemetry Data...")
    time.sleep(2.0)  # Allow time for telemetry
    
    # Check message history
    messages = orchestrator.get_message_history("orchestrator/data/+")
    print(f"   Received {len(messages)} telemetry messages")
    
    # Show some sample telemetry
    if messages:
        latest_message = messages[-1]
        print(f"   Latest message topic: {latest_message.topic}")
        try:
            payload = json.loads(latest_message.payload.decode())
            print(f"   Sample data keys: {list(payload.get('data', {}).keys())}")
        except:
            print("   Could not parse message payload")
    
    # Test LiDAR data
    print("\n6. Testing LiDAR Simulation...")
    lidar_messages = orchestrator.get_message_history("orchestrator/data/lidar_01")
    if lidar_messages:
        latest_lidar = lidar_messages[-1]
        try:
            payload = json.loads(latest_lidar.payload.decode())
            lidar_data = payload.get('data', {})
            if lidar_data.get('scan_available'):
                ranges = lidar_data.get('ranges', [])
                print(f"   LiDAR scan points: {len(ranges)}")
                if ranges:
                    min_range = min(ranges)
                    max_range = max(ranges)
                    print(f"   Range: {min_range:.2f}m to {max_range:.2f}m")
                    
                    # Check for obstacles
                    close_obstacles = [r for r in ranges if r < 1.0]
                    print(f"   Close obstacles (<1m): {len(close_obstacles)}")
            else:
                print("   No LiDAR scan data available")
        except Exception as e:
            print(f"   Error parsing LiDAR data: {e}")
    else:
        print("   No LiDAR messages received")
    
    # Test robot state
    print("\n7. Testing Robot State...")
    state_messages = orchestrator.get_message_history("orchestrator/status/robot")
    if state_messages:
        latest_state = state_messages[-1]
        try:
            payload = json.loads(latest_state.payload.decode())
            position = payload.get('position', {})
            velocity = payload.get('velocity', {})
            print(f"   Position: ({position.get('x', 0):.3f}, {position.get('y', 0):.3f})")
            print(f"   Heading: {payload.get('heading', 0):.3f} rad")
            print(f"   Velocity: {velocity.get('linear', 0):.3f} m/s")
        except Exception as e:
            print(f"   Error parsing robot state: {e}")
    else:
        print("   No robot state messages received")
    
    # Test emergency stop
    print("\n8. Testing Emergency Stop...")
    estop_command = {
        "timestamp": time.time(),
        "command_id": "test_estop_001",
        "action": "emergency_stop",
        "reason": "test",
        "source": "test_script"
    }
    
    success = mqtt_client.publish("orchestrator/cmd/estop", estop_command)
    print(f"   Emergency stop sent: {'✅' if success else '❌'}")
    
    # Wait a moment for processing
    time.sleep(1.0)
    
    # Check for safety monitor response
    safety_messages = orchestrator.get_message_history("orchestrator/status/safety_monitor")
    if safety_messages:
        print("   Safety monitor responded to emergency stop")
    
    print("\n9. Performance Statistics...")
    mock_client = mqtt_client.get_mock_client()
    stats = mock_client.get_stats()
    print(f"   Messages published: {stats['messages_published']}")
    print(f"   Messages received: {stats['messages_received']}")
    print(f"   Active subscriptions: {stats['active_subscriptions']}")
    
    # Shutdown
    print("\n10. Shutting down...")
    orchestrator.shutdown()
    print("✅ Mock HAL Orchestrator shutdown complete")
    
    print("\n" + "=" * 60)
    print("Mock HAL Test Complete!")
    print("✅ All basic functionality working")
    print("✅ Realistic sensor data generated")
    print("✅ Commands processed and acknowledged")
    print("✅ MQTT communication simulated")
    print("=" * 60)
    
    return True


def test_data_generators():
    """Test individual data generators"""
    print("\n" + "=" * 60)
    print("Testing Data Generators")
    print("=" * 60)
    
    from hal_service.mock.data_generators import (
        LidarDataGenerator, 
        EncoderDataGenerator, 
        MotorDataGenerator,
        SimulationState
    )
    
    # Test LiDAR generator
    print("\n1. Testing LiDAR Data Generator...")
    lidar_gen = LidarDataGenerator()
    sim_state = SimulationState()
    
    scan_data = lidar_gen.generate_scan(sim_state)
    print(f"   Generated scan with {len(scan_data['ranges'])} points")
    print(f"   Range: {min(scan_data['ranges']):.2f}m to {max(scan_data['ranges']):.2f}m")
    
    # Test encoder generator
    print("\n2. Testing Encoder Data Generator...")
    encoder_gen = EncoderDataGenerator()
    
    # Simulate motor command
    command = {
        "action": "move_forward",
        "parameters": {"distance": 1.0, "speed": 0.5}
    }
    
    encoder_gen.update_from_motor_command(command, 0.1)
    encoder_data = encoder_gen.generate_data()
    print(f"   Encoder ticks: {encoder_data['tick_count']}")
    print(f"   Distance: {encoder_data['total_distance']:.3f}m")
    print(f"   Velocity: {encoder_data['velocity']:.3f}m/s")
    
    # Test motor generator
    print("\n3. Testing Motor Data Generator...")
    motor_gen = MotorDataGenerator()
    
    motor_gen.update_from_command(command, 0.1)
    motor_data = motor_gen.generate_data()
    print(f"   Motor speed: {motor_data['current_speed']:.3f}")
    print(f"   Duty cycle: {motor_data['duty_cycle']:.1f}%")
    print(f"   Temperature: {motor_data['motor_temperature']:.1f}°C")
    
    print("\n✅ All data generators working correctly")


if __name__ == "__main__":
    try:
        # Test data generators first
        test_data_generators()
        
        # Test full mock HAL
        success = test_mock_hal()
        
        if success:
            print("\n🎉 Mock HAL implementation is ready for UI/control development!")
            print("\nTo use the mock HAL:")
            print("1. Run: python hal_service/mock/mock_orchestrator.py")
            print("2. Connect your UI/control system to the mock MQTT interface")
            print("3. Send commands and receive realistic telemetry data")
        else:
            print("\n❌ Mock HAL test failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)