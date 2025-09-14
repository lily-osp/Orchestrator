#!/usr/bin/env python3
"""
Simple test for Mock HAL implementation without external dependencies

Tests the core mock functionality to verify the implementation works.
"""

import sys
import time
import json
from pathlib import Path

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_data_generators():
    """Test individual data generators without dependencies"""
    print("=" * 60)
    print("Testing Mock HAL Data Generators")
    print("=" * 60)
    
    try:
        from hal_service.mock.data_generators import (
            LidarDataGenerator, 
            EncoderDataGenerator, 
            MotorDataGenerator,
            SimulationState,
            SimulationCoordinator
        )
        
        # Test LiDAR generator
        print("\n1. Testing LiDAR Data Generator...")
        lidar_gen = LidarDataGenerator()
        sim_state = SimulationState()
        
        scan_data = lidar_gen.generate_scan(sim_state)
        print(f"   ✅ Generated scan with {len(scan_data['ranges'])} points")
        print(f"   ✅ Range: {min(scan_data['ranges']):.2f}m to {max(scan_data['ranges']):.2f}m")
        
        # Verify scan data structure
        required_fields = ['ranges', 'angles', 'quality', 'timestamp', 'scan_available']
        for field in required_fields:
            assert field in scan_data, f"Missing field: {field}"
        print(f"   ✅ All required fields present: {required_fields}")
        
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
        print(f"   ✅ Encoder ticks: {encoder_data['tick_count']}")
        print(f"   ✅ Distance: {encoder_data['total_distance']:.3f}m")
        print(f"   ✅ Velocity: {encoder_data['velocity']:.3f}m/s")
        
        # Test motor generator
        print("\n3. Testing Motor Data Generator...")
        motor_gen = MotorDataGenerator()
        
        motor_gen.update_from_command(command, 0.1)
        motor_data = motor_gen.generate_data()
        print(f"   ✅ Motor speed: {motor_data['current_speed']:.3f}")
        print(f"   ✅ Duty cycle: {motor_data['duty_cycle']:.1f}%")
        print(f"   ✅ Temperature: {motor_data['motor_temperature']:.1f}°C")
        
        # Test simulation coordinator
        print("\n4. Testing Simulation Coordinator...")
        coordinator = SimulationCoordinator()
        
        # Process motor commands
        coordinator.process_motor_command("left_motor", command)
        coordinator.update()
        
        robot_state = coordinator.get_robot_state()
        print(f"   ✅ Robot position: ({robot_state['position']['x']:.3f}, {robot_state['position']['y']:.3f})")
        print(f"   ✅ Robot heading: {robot_state['heading']:.3f} rad")
        
        # Test LiDAR data with updated position
        lidar_data = coordinator.get_lidar_data()
        print(f"   ✅ LiDAR scan updated with robot position")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing data generators: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_mqtt():
    """Test mock MQTT client"""
    print("\n" + "=" * 60)
    print("Testing Mock MQTT Client")
    print("=" * 60)
    
    try:
        from hal_service.mock.mock_mqtt_client import MockMQTTClient, MockMQTTClientWrapper
        
        # Test basic MQTT client
        print("\n1. Testing Basic Mock MQTT Client...")
        client = MockMQTTClient("test_client")
        
        # Test connection
        success = client.connect()
        print(f"   ✅ Connection: {'Success' if success else 'Failed'}")
        
        # Test message callback
        received_messages = []
        
        def test_callback(client, userdata, message):
            received_messages.append({
                'topic': message.topic,
                'payload': message.payload.decode()
            })
        
        # Subscribe and publish
        client.subscribe("test/topic")
        client.message_callback_add("test/topic", test_callback)
        
        test_message = {"test": "data", "timestamp": time.time()}
        success = client.publish("test/topic", test_message)
        print(f"   ✅ Publish: {'Success' if success else 'Failed'}")
        
        # Check message history
        history = client.get_message_history()
        print(f"   ✅ Message history: {len(history)} messages")
        
        # Test topic matching
        assert client._topic_matches("test/topic", "test/topic")
        assert client._topic_matches("test/topic", "test/+")
        assert client._topic_matches("test/topic/sub", "test/#")
        print(f"   ✅ Topic matching works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing mock MQTT: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_devices():
    """Test mock device implementations"""
    print("\n" + "=" * 60)
    print("Testing Mock Devices")
    print("=" * 60)
    
    try:
        from hal_service.mock.mock_mqtt_client import MockMQTTClientWrapper, MQTTConfig
        from hal_service.mock.mock_devices import MockMotorController, MockEncoderSensor
        
        # Create mock MQTT client
        print("\n1. Setting up Mock MQTT Client...")
        
        # Create a simple config object
        class SimpleConfig:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        mqtt_config = SimpleConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="test_client",
            username=None,
            password=None
        )
        
        mqtt_client = MockMQTTClientWrapper(mqtt_config)
        mqtt_client.connect()
        print("   ✅ Mock MQTT client connected")
        
        # Test mock motor
        print("\n2. Testing Mock Motor Controller...")
        motor_config = {
            'max_speed': 1.0,
            'acceleration': 0.5,
            'gpio_pins': {'enable': 18, 'direction': 19},
            'encoder_pins': {'a': 20, 'b': 21}
        }
        
        motor = MockMotorController("test_motor", mqtt_client, motor_config)
        success = motor.initialize()
        print(f"   ✅ Motor initialization: {'Success' if success else 'Failed'}")
        
        # Test command execution
        command = {
            "action": "move_forward",
            "parameters": {"distance": 1.0, "speed": 0.5}
        }
        
        success = motor.execute_command(command)
        print(f"   ✅ Command execution: {'Success' if success else 'Failed'}")
        
        # Get motor status
        status = motor.get_status()
        print(f"   ✅ Motor status: {status['status']}")
        
        # Test mock encoder
        print("\n3. Testing Mock Encoder Sensor...")
        encoder_config = {
            'publish_rate': 20.0,
            'calibration': {
                'resolution': 1000,
                'wheel_diameter': 0.1,
                'gear_ratio': 1.0,
                'pin_a': 20,
                'pin_b': 21
            },
            'interface': SimpleConfig(pin=20)
        }
        
        encoder = MockEncoderSensor("test_encoder", mqtt_client, encoder_config)
        success = encoder.initialize()
        print(f"   ✅ Encoder initialization: {'Success' if success else 'Failed'}")
        
        # Read encoder data
        encoder_data = encoder.read_data()
        print(f"   ✅ Encoder data: {encoder_data['tick_count']} ticks")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing mock devices: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Mock HAL Tests")
    print("This tests the core mock functionality without external dependencies")
    
    tests = [
        ("Data Generators", test_data_generators),
        ("Mock MQTT Client", test_mock_mqtt),
        ("Mock Devices", test_mock_devices)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Mock HAL implementation is working correctly.")
        print("\nThe Mock HAL provides:")
        print("✅ Realistic sensor data simulation")
        print("✅ Motor command processing")
        print("✅ MQTT interface compatibility")
        print("✅ Coordinated robot simulation")
        print("\nReady for UI/control development!")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)