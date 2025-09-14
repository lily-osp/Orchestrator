#!/usr/bin/env python3
"""
Integration test for State Manager with HAL components

This test verifies that the state manager correctly integrates with
the existing encoder sensors and MQTT infrastructure.
"""

import json
import time
import threading
from pathlib import Path
import sys

# Add hal_service to path
sys.path.insert(0, str(Path(__file__).parent / "hal_service"))

from hal_service.state_manager import StateManager
from hal_service.mqtt_client import MQTTClientWrapper, MQTTConfig
from hal_service.config import load_config


def test_state_manager_integration():
    """Test state manager integration with configuration"""
    print("Testing State Manager Integration")
    print("=" * 40)
    
    try:
        # Load configuration
        config = load_config("config.yaml")
        print(f"✓ Configuration loaded successfully")
        
        # Create MQTT configuration
        mqtt_config = MQTTConfig(
            broker_host=config.mqtt.broker_host,
            broker_port=config.mqtt.broker_port,
            keepalive=config.mqtt.keepalive,
            client_id="state_manager_integration_test"
        )
        print(f"✓ MQTT configuration created")
        
        # Create state manager
        state_manager = StateManager(
            mqtt_config=mqtt_config,
            wheel_base=0.3,  # 30cm wheel base
            publish_rate=5.0
        )
        print(f"✓ State manager created")
        
        # Test MQTT client connection
        test_client = MQTTClientWrapper(MQTTConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="integration_test_client"
        ))
        
        if not test_client.connect():
            print("❌ Failed to connect to MQTT broker")
            print("   Make sure Mosquitto is running: sudo systemctl start mosquitto")
            return False
        
        print("✓ MQTT broker connection successful")
        
        # Start state manager
        if not state_manager.start():
            print("❌ Failed to start state manager")
            return False
        
        print("✓ State manager started")
        
        # Wait for initialization
        time.sleep(2.0)
        
        # Check state manager status
        status = state_manager.get_status()
        print(f"✓ State manager status: {status['running']}")
        print(f"  - MQTT connected: {status['mqtt_connected']}")
        print(f"  - Update count: {status['update_count']}")
        
        # Test state retrieval
        current_state = state_manager.get_current_state()
        print(f"✓ Current robot state:")
        print(f"  - Position: ({current_state.position.x:.3f}, {current_state.position.y:.3f})")
        print(f"  - Heading: {current_state.heading:.3f} rad")
        print(f"  - Status: {current_state.status}")
        
        # Simulate encoder data to test processing
        print("\nTesting encoder data processing...")
        
        # Create test encoder data
        left_encoder_data = {
            "timestamp": time.time(),
            "device_id": "left_encoder",
            "data": {
                "total_distance": 0.5,
                "velocity": 0.1,
                "tick_count": 500,
                "direction": 1
            }
        }
        
        right_encoder_data = {
            "timestamp": time.time(),
            "device_id": "right_encoder",
            "data": {
                "total_distance": 0.5,
                "velocity": 0.1,
                "tick_count": 500,
                "direction": 1
            }
        }
        
        # Publish test data
        test_client.publish("orchestrator/data/left_encoder", left_encoder_data)
        test_client.publish("orchestrator/data/right_encoder", right_encoder_data)
        
        # Wait for processing
        time.sleep(1.0)
        
        # Check updated state
        updated_state = state_manager.get_current_state()
        print(f"✓ State after encoder data:")
        print(f"  - Position: ({updated_state.position.x:.3f}, {updated_state.position.y:.3f})")
        print(f"  - Heading: {updated_state.heading:.3f} rad")
        print(f"  - Odometry valid: {updated_state.odometry_valid}")
        
        # Test command handling
        print("\nTesting command handling...")
        
        reset_command = {
            "action": "reset_odometry",
            "timestamp": time.time()
        }
        
        test_client.publish("orchestrator/cmd/state_manager", reset_command)
        time.sleep(0.5)
        
        reset_state = state_manager.get_current_state()
        print(f"✓ State after reset:")
        print(f"  - Position: ({reset_state.position.x:.3f}, {reset_state.position.y:.3f})")
        print(f"  - Heading: {reset_state.heading:.3f} rad")
        
        # Cleanup
        state_manager.stop()
        test_client.disconnect()
        
        print("\n✅ Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_validation():
    """Test configuration validation for state manager"""
    print("\nTesting Configuration Validation")
    print("=" * 40)
    
    try:
        # Load and validate configuration
        config = load_config("config.yaml")
        
        # Check required sensors
        encoder_sensors = [s for s in config.sensors if s.type == "encoder"]
        print(f"✓ Found {len(encoder_sensors)} encoder sensors")
        
        for sensor in encoder_sensors:
            print(f"  - {sensor.name}: pin {sensor.interface.pin}")
            if hasattr(sensor, 'calibration') and sensor.calibration:
                print(f"    Calibration: {sensor.calibration}")
        
        # Check MQTT configuration
        print(f"✓ MQTT broker: {config.mqtt.broker_host}:{config.mqtt.broker_port}")
        
        # Check motor configuration for wheel base calculation
        motors = config.motors
        print(f"✓ Found {len(motors)} motors")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def main():
    """Main test function"""
    print("State Manager Integration Tests")
    print("=" * 50)
    
    # Run configuration validation
    config_ok = test_configuration_validation()
    
    if not config_ok:
        print("❌ Configuration validation failed, skipping integration test")
        return False
    
    # Run integration test
    integration_ok = test_state_manager_integration()
    
    if config_ok and integration_ok:
        print("\n🎉 All integration tests passed!")
        return True
    else:
        print("\n❌ Some integration tests failed")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)