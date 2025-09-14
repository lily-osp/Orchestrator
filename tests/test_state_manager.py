#!/usr/bin/env python3
"""
Test script for State Manager Service

This script tests the state management functionality by simulating
encoder data and verifying odometry calculations.
"""

import json
import math
import time
import threading
from pathlib import Path
import sys

# Add hal_service to path
sys.path.insert(0, str(Path(__file__).parent / "hal_service"))

from hal_service.state_manager import StateManager, Position, Velocity, RobotState
from hal_service.mqtt_client import MQTTClientWrapper, MQTTConfig


class StateManagerTester:
    """Test harness for State Manager"""
    
    def __init__(self):
        self.mqtt_config = MQTTConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="state_manager_tester"
        )
        
        self.test_client = MQTTClientWrapper(self.mqtt_config)
        self.state_manager = None
        self.received_states = []
        
    def setup(self):
        """Setup test environment"""
        print("Setting up test environment...")
        
        # Connect test client
        if not self.test_client.connect():
            print("Failed to connect test MQTT client")
            return False
        
        # Subscribe to robot state updates
        self.test_client.subscribe(
            "orchestrator/status/robot",
            self._handle_state_update
        )
        
        # Create state manager
        self.state_manager = StateManager(
            mqtt_config=MQTTConfig(
                broker_host="localhost",
                broker_port=1883,
                client_id="state_manager_test"
            ),
            wheel_base=0.3,  # 30cm wheel base
            publish_rate=5.0  # 5 Hz for testing
        )
        
        return True
    
    def _handle_state_update(self, message_data):
        """Handle received robot state updates"""
        try:
            payload = message_data['payload']
            self.received_states.append(payload)
            print(f"Received state update: pos=({payload['position']['x']:.3f}, {payload['position']['y']:.3f}), "
                  f"heading={payload['heading']:.3f}, status={payload['status']}")
        except Exception as e:
            print(f"Error handling state update: {e}")
    
    def simulate_encoder_data(self, left_distance, right_distance, duration=1.0):
        """Simulate encoder data for testing"""
        print(f"Simulating encoder data: left={left_distance}m, right={right_distance}m")
        
        # Simulate left encoder
        left_data = {
            "timestamp": time.time(),
            "device_id": "left_encoder",
            "data": {
                "total_distance": left_distance,
                "velocity": left_distance / duration,
                "tick_count": int(left_distance * 1000),  # Assume 1000 ticks per meter
                "direction": 1
            }
        }
        
        # Simulate right encoder
        right_data = {
            "timestamp": time.time(),
            "device_id": "right_encoder", 
            "data": {
                "total_distance": right_distance,
                "velocity": right_distance / duration,
                "tick_count": int(right_distance * 1000),
                "direction": 1
            }
        }
        
        # Publish encoder data
        self.test_client.publish("orchestrator/data/left_encoder", left_data)
        self.test_client.publish("orchestrator/data/right_encoder", right_data)
        
        # Wait for processing
        time.sleep(0.5)
    
    def test_straight_line_motion(self):
        """Test straight line motion odometry"""
        print("\n=== Testing Straight Line Motion ===")
        
        # Reset odometry
        reset_cmd = {
            "action": "reset_odometry",
            "timestamp": time.time()
        }
        self.test_client.publish("orchestrator/cmd/state_manager", reset_cmd)
        time.sleep(0.5)
        
        # Simulate moving forward 1 meter
        self.simulate_encoder_data(1.0, 1.0)
        
        # Check result
        current_state = self.state_manager.get_current_state()
        expected_x = 1.0
        expected_y = 0.0
        
        print(f"Expected position: ({expected_x}, {expected_y})")
        print(f"Actual position: ({current_state.position.x:.3f}, {current_state.position.y:.3f})")
        
        # Verify within tolerance
        tolerance = 0.01
        if (abs(current_state.position.x - expected_x) < tolerance and 
            abs(current_state.position.y - expected_y) < tolerance):
            print("✓ Straight line motion test PASSED")
            return True
        else:
            print("✗ Straight line motion test FAILED")
            return False
    
    def test_rotation_motion(self):
        """Test rotation motion odometry"""
        print("\n=== Testing Rotation Motion ===")
        
        # Reset odometry
        reset_cmd = {
            "action": "reset_odometry",
            "timestamp": time.time()
        }
        self.test_client.publish("orchestrator/cmd/state_manager", reset_cmd)
        time.sleep(0.5)
        
        # Simulate 90-degree turn (right wheel moves forward, left wheel backward)
        # For 90-degree turn: arc_length = wheel_base * pi/2
        wheel_base = 0.3
        arc_length = wheel_base * math.pi / 2
        
        self.simulate_encoder_data(-arc_length/2, arc_length/2)
        
        # Check result
        current_state = self.state_manager.get_current_state()
        expected_heading = math.pi / 2  # 90 degrees in radians
        
        print(f"Expected heading: {expected_heading:.3f} rad ({math.degrees(expected_heading):.1f}°)")
        print(f"Actual heading: {current_state.heading:.3f} rad ({math.degrees(current_state.heading):.1f}°)")
        
        # Verify within tolerance
        tolerance = 0.1  # 0.1 radian tolerance
        if abs(current_state.heading - expected_heading) < tolerance:
            print("✓ Rotation motion test PASSED")
            return True
        else:
            print("✗ Rotation motion test FAILED")
            return False
    
    def test_curved_motion(self):
        """Test curved motion odometry"""
        print("\n=== Testing Curved Motion ===")
        
        # Reset odometry
        reset_cmd = {
            "action": "reset_odometry",
            "timestamp": time.time()
        }
        self.test_client.publish("orchestrator/cmd/state_manager", reset_cmd)
        time.sleep(0.5)
        
        # Simulate curved motion (right wheel moves faster than left)
        left_distance = 0.8
        right_distance = 1.2
        
        self.simulate_encoder_data(left_distance, right_distance)
        
        # Check that robot moved and turned
        current_state = self.state_manager.get_current_state()
        
        print(f"Position: ({current_state.position.x:.3f}, {current_state.position.y:.3f})")
        print(f"Heading: {current_state.heading:.3f} rad ({math.degrees(current_state.heading):.1f}°)")
        
        # Verify robot moved forward and turned
        if (current_state.position.x > 0.5 and  # Moved forward significantly
            abs(current_state.heading) > 0.1):   # Turned significantly
            print("✓ Curved motion test PASSED")
            return True
        else:
            print("✗ Curved motion test FAILED")
            return False
    
    def test_command_handling(self):
        """Test command handling"""
        print("\n=== Testing Command Handling ===")
        
        # Test position setting
        set_pos_cmd = {
            "action": "set_position",
            "x": 5.0,
            "y": 3.0,
            "heading": 1.57,  # 90 degrees
            "timestamp": time.time()
        }
        self.test_client.publish("orchestrator/cmd/state_manager", set_pos_cmd)
        time.sleep(0.5)
        
        current_state = self.state_manager.get_current_state()
        
        print(f"Set position to: (5.0, 3.0), heading=1.57")
        print(f"Actual position: ({current_state.position.x:.3f}, {current_state.position.y:.3f}), "
              f"heading={current_state.heading:.3f}")
        
        tolerance = 0.01
        if (abs(current_state.position.x - 5.0) < tolerance and
            abs(current_state.position.y - 3.0) < tolerance and
            abs(current_state.heading - 1.57) < tolerance):
            print("✓ Command handling test PASSED")
            return True
        else:
            print("✗ Command handling test FAILED")
            return False
    
    def test_emergency_stop(self):
        """Test emergency stop handling"""
        print("\n=== Testing Emergency Stop ===")
        
        # Send emergency stop
        estop_cmd = {
            "action": "emergency_stop",
            "timestamp": time.time()
        }
        self.test_client.publish("orchestrator/cmd/estop", estop_cmd)
        time.sleep(0.5)
        
        current_state = self.state_manager.get_current_state()
        
        print(f"Status after emergency stop: {current_state.status}")
        print(f"Velocity after emergency stop: linear={current_state.velocity.linear}, "
              f"angular={current_state.velocity.angular}")
        
        if (current_state.status == "emergency_stop" and
            current_state.velocity.linear == 0.0 and
            current_state.velocity.angular == 0.0):
            print("✓ Emergency stop test PASSED")
            return True
        else:
            print("✗ Emergency stop test FAILED")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting State Manager Tests")
        print("=" * 50)
        
        if not self.setup():
            print("Failed to setup test environment")
            return False
        
        # Start state manager
        if not self.state_manager.start():
            print("Failed to start state manager")
            return False
        
        # Wait for initialization
        time.sleep(1.0)
        
        # Run tests
        tests = [
            self.test_straight_line_motion,
            self.test_rotation_motion,
            self.test_curved_motion,
            self.test_command_handling,
            self.test_emergency_stop
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                time.sleep(1.0)  # Wait between tests
            except Exception as e:
                print(f"Test failed with exception: {e}")
        
        # Cleanup
        self.state_manager.stop()
        self.test_client.disconnect()
        
        # Results
        print("\n" + "=" * 50)
        print(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests PASSED!")
            return True
        else:
            print("❌ Some tests FAILED")
            return False


def main():
    """Main test function"""
    tester = StateManagerTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()