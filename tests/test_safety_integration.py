#!/usr/bin/env python3
"""
Integration test for the Safety Monitor subsystem.

This script tests the safety monitor integration with the existing HAL system,
including MQTT communication and emergency stop functionality.
"""

import json
import time
import threading
import sys
from pathlib import Path
from datetime import datetime

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent / "hal_service"))

from hal_service.mqtt_client import MQTTClientWrapper, MQTTConfig
from hal_service.safety_monitor import SafetyMonitor


class SafetyIntegrationTest:
    """Integration test for safety monitor functionality."""
    
    def __init__(self):
        """Initialize the integration test."""
        self.mqtt_config = MQTTConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="safety_test_client"
        )
        
        self.test_client = MQTTClientWrapper(self.mqtt_config)
        self.safety_monitor = None
        self.test_results = []
        self.emergency_stop_received = False
        
    def setup(self):
        """Set up the test environment."""
        print("Setting up safety monitor integration test...")
        
        # Connect test MQTT client
        if not self.test_client.connect():
            print("ERROR: Failed to connect test MQTT client")
            return False
        
        # Subscribe to emergency stop commands
        if not self.test_client.subscribe("orchestrator/cmd/estop", self._handle_emergency_stop):
            print("ERROR: Failed to subscribe to emergency stop topic")
            return False
        
        # Subscribe to safety status
        if not self.test_client.subscribe("orchestrator/status/safety_monitor", self._handle_safety_status):
            print("ERROR: Failed to subscribe to safety status topic")
            return False
        
        # Create and start safety monitor
        try:
            self.safety_monitor = SafetyMonitor()
            if not self.safety_monitor.start():
                print("ERROR: Failed to start safety monitor")
                return False
        except Exception as e:
            print(f"ERROR: Exception starting safety monitor: {e}")
            return False
        
        print("Test setup completed successfully")
        return True
    
    def teardown(self):
        """Clean up the test environment."""
        print("Cleaning up test environment...")
        
        if self.safety_monitor:
            self.safety_monitor.stop()
        
        if self.test_client:
            self.test_client.disconnect()
        
        print("Cleanup completed")
    
    def _handle_emergency_stop(self, message_data):
        """Handle emergency stop command received during test."""
        try:
            payload = message_data['payload']
            print(f"EMERGENCY STOP RECEIVED: {payload}")
            
            self.emergency_stop_received = True
            
            # Validate emergency stop command format
            required_fields = ['timestamp', 'command_id', 'action', 'reason', 'source']
            for field in required_fields:
                if field not in payload:
                    self.test_results.append(f"FAIL: Missing field in emergency stop: {field}")
                    return
            
            if payload['action'] != 'emergency_stop':
                self.test_results.append(f"FAIL: Wrong action in emergency stop: {payload['action']}")
                return
            
            if payload['source'] != 'safety_monitor':
                self.test_results.append(f"FAIL: Wrong source in emergency stop: {payload['source']}")
                return
            
            self.test_results.append("PASS: Emergency stop command format valid")
            
        except Exception as e:
            self.test_results.append(f"FAIL: Error handling emergency stop: {e}")
    
    def _handle_safety_status(self, message_data):
        """Handle safety status messages during test."""
        try:
            payload = message_data['payload']
            print(f"Safety status: {payload.get('status', 'unknown')} - {payload.get('message', '')}")
            
        except Exception as e:
            print(f"Error handling safety status: {e}")
    
    def test_safe_lidar_data(self):
        """Test that safe LiDAR data doesn't trigger emergency stop."""
        print("\nTest 1: Safe LiDAR data (no obstacles)")
        
        # Create safe LiDAR data
        safe_data = {
            "timestamp": datetime.now().isoformat(),
            "device_id": "lidar_01",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "ranges": [2.0, 2.5, 3.0, 2.8, 2.2] * 72,  # All safe distances
                "angles": list(range(0, 360, 5)),  # 5-degree resolution
                "scan_available": True
            }
        }
        
        # Reset emergency stop flag
        self.emergency_stop_received = False
        
        # Publish safe LiDAR data
        topic = "orchestrator/data/lidar_01"
        if self.test_client.publish(topic, safe_data):
            print("Published safe LiDAR data")
        else:
            self.test_results.append("FAIL: Could not publish safe LiDAR data")
            return
        
        # Wait for processing
        time.sleep(1.0)
        
        # Check that no emergency stop was triggered
        if self.emergency_stop_received:
            self.test_results.append("FAIL: Emergency stop triggered for safe data")
        else:
            self.test_results.append("PASS: No emergency stop for safe data")
    
    def test_critical_obstacle_detection(self):
        """Test that critical obstacles trigger emergency stop."""
        print("\nTest 2: Critical obstacle detection")
        
        # Create LiDAR data with critical obstacle in front
        ranges = [2.0] * 72  # Start with safe distances
        ranges[0] = 0.3  # Critical obstacle at 0 degrees (front)
        ranges[1] = 0.25  # Another close point
        
        critical_data = {
            "timestamp": datetime.now().isoformat(),
            "device_id": "lidar_01",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "ranges": ranges,
                "angles": list(range(0, 360, 5)),
                "scan_available": True
            }
        }
        
        # Reset emergency stop flag
        self.emergency_stop_received = False
        
        # Publish critical LiDAR data
        topic = "orchestrator/data/lidar_01"
        if self.test_client.publish(topic, critical_data):
            print("Published critical LiDAR data (obstacle at 0.3m)")
        else:
            self.test_results.append("FAIL: Could not publish critical LiDAR data")
            return
        
        # Wait for processing
        time.sleep(2.0)
        
        # Check that emergency stop was triggered
        if self.emergency_stop_received:
            self.test_results.append("PASS: Emergency stop triggered for critical obstacle")
        else:
            self.test_results.append("FAIL: No emergency stop for critical obstacle")
    
    def test_warning_obstacle_detection(self):
        """Test that warning-level obstacles don't trigger emergency stop."""
        print("\nTest 3: Warning obstacle detection (side zones)")
        
        # Create LiDAR data with obstacle in warning zone (side)
        ranges = [2.0] * 72  # Start with safe distances
        ranges[18] = 0.3  # Warning obstacle at 90 degrees (left side)
        
        warning_data = {
            "timestamp": datetime.now().isoformat(),
            "device_id": "lidar_01",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "ranges": ranges,
                "angles": list(range(0, 360, 5)),
                "scan_available": True
            }
        }
        
        # Reset emergency stop flag
        self.emergency_stop_received = False
        
        # Publish warning LiDAR data
        topic = "orchestrator/data/lidar_01"
        if self.test_client.publish(topic, warning_data):
            print("Published warning LiDAR data (obstacle at side)")
        else:
            self.test_results.append("FAIL: Could not publish warning LiDAR data")
            return
        
        # Wait for processing
        time.sleep(1.0)
        
        # Check that no emergency stop was triggered
        if self.emergency_stop_received:
            self.test_results.append("FAIL: Emergency stop triggered for warning obstacle")
        else:
            self.test_results.append("PASS: No emergency stop for warning obstacle")
    
    def test_invalid_lidar_data(self):
        """Test handling of invalid LiDAR data."""
        print("\nTest 4: Invalid LiDAR data handling")
        
        # Test various invalid data formats
        invalid_data_sets = [
            # Missing data field
            {
                "timestamp": datetime.now().isoformat(),
                "device_id": "lidar_01"
            },
            # Missing ranges
            {
                "timestamp": datetime.now().isoformat(),
                "device_id": "lidar_01",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "angles": list(range(0, 360, 5))
                }
            },
            # Mismatched ranges and angles
            {
                "timestamp": datetime.now().isoformat(),
                "device_id": "lidar_01",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "ranges": [1.0, 2.0, 3.0],
                    "angles": [0, 90]  # Different length
                }
            }
        ]
        
        topic = "orchestrator/data/lidar_01"
        
        for i, invalid_data in enumerate(invalid_data_sets):
            print(f"  Testing invalid data set {i+1}")
            
            if self.test_client.publish(topic, invalid_data):
                time.sleep(0.5)  # Allow processing
            else:
                self.test_results.append(f"FAIL: Could not publish invalid data set {i+1}")
        
        # System should still be running after invalid data
        if self.safety_monitor and self.safety_monitor.running:
            self.test_results.append("PASS: Safety monitor handles invalid data gracefully")
        else:
            self.test_results.append("FAIL: Safety monitor crashed on invalid data")
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("Starting Safety Monitor Integration Tests")
        print("=" * 50)
        
        if not self.setup():
            print("ABORT: Test setup failed")
            return False
        
        try:
            # Wait for safety monitor to fully start
            time.sleep(2.0)
            
            # Run individual tests
            self.test_safe_lidar_data()
            self.test_critical_obstacle_detection()
            self.test_warning_obstacle_detection()
            self.test_invalid_lidar_data()
            
            # Wait for final processing
            time.sleep(2.0)
            
        finally:
            self.teardown()
        
        # Print results
        print("\n" + "=" * 50)
        print("TEST RESULTS:")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for result in self.test_results:
            print(result)
            if result.startswith("PASS"):
                passed += 1
            elif result.startswith("FAIL"):
                failed += 1
        
        print(f"\nSummary: {passed} passed, {failed} failed")
        
        return failed == 0


def main():
    """Main entry point for integration test."""
    print("Orchestrator Safety Monitor Integration Test")
    print("This test requires a running MQTT broker (mosquitto)")
    print()
    
    # Check if we should proceed
    try:
        response = input("Continue with integration test? (y/N): ")
        if response.lower() != 'y':
            print("Test cancelled by user")
            return
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        return
    
    # Run tests
    test_runner = SafetyIntegrationTest()
    
    try:
        success = test_runner.run_all_tests()
        
        if success:
            print("\nAll tests PASSED! Safety monitor integration is working correctly.")
            sys.exit(0)
        else:
            print("\nSome tests FAILED! Check the safety monitor implementation.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        test_runner.teardown()
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        test_runner.teardown()
        sys.exit(1)


if __name__ == "__main__":
    main()