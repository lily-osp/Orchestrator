"""
Unit tests for the Safety Monitor subsystem.

Tests the standalone safety monitoring functionality including obstacle detection,
emergency stop triggering, and MQTT communication.
"""

import json
import time
import threading
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hal_service"))

from hal_service.safety_monitor import SafetyMonitor, SafetyZone, ObstacleDetection
from hal_service.config import OrchestratorConfig, SafetyConfig, MQTTConfig


class TestSafetyMonitor(unittest.TestCase):
    """Test cases for the SafetyMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock configuration
        self.mock_config = Mock(spec=OrchestratorConfig)
        self.mock_config.safety = Mock(spec=SafetyConfig)
        self.mock_config.safety.enabled = True
        self.mock_config.safety.obstacle_threshold = 0.5
        self.mock_config.safety.emergency_stop_timeout = 0.1
        
        self.mock_config.mqtt = Mock(spec=MQTTConfig)
        self.mock_config.mqtt.broker_host = "localhost"
        self.mock_config.mqtt.broker_port = 1883
        self.mock_config.mqtt.keepalive = 60
        
        # Mock MQTT client
        self.mock_mqtt_client = Mock()
        self.mock_mqtt_client.connect.return_value = True
        self.mock_mqtt_client.subscribe.return_value = True
        self.mock_mqtt_client.publish.return_value = True
        self.mock_mqtt_client.is_connected = True
        
        # Patch dependencies
        self.config_patcher = patch('hal_service.safety_monitor.load_config')
        self.mqtt_patcher = patch('hal_service.safety_monitor.MQTTClientWrapper')
        self.logging_patcher = patch('hal_service.safety_monitor.get_logging_service')
        
        self.mock_load_config = self.config_patcher.start()
        self.mock_mqtt_class = self.mqtt_patcher.start()
        self.mock_logging_service = self.logging_patcher.start()
        
        self.mock_load_config.return_value = self.mock_config
        self.mock_mqtt_class.return_value = self.mock_mqtt_client
        
        # Mock logger
        self.mock_logger = Mock()
        self.mock_logging_service.return_value.get_device_logger.return_value = self.mock_logger
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.config_patcher.stop()
        self.mqtt_patcher.stop()
        self.logging_patcher.stop()
    
    def test_safety_monitor_initialization(self):
        """Test SafetyMonitor initialization."""
        monitor = SafetyMonitor()
        
        self.assertFalse(monitor.running)
        self.assertFalse(monitor.emergency_stop_active)
        self.assertEqual(monitor.emergency_stops_triggered, 0)
        self.assertIsNotNone(monitor.safety_zones)
        self.assertGreater(len(monitor.safety_zones), 0)
    
    def test_safety_zones_initialization(self):
        """Test safety zones are properly initialized."""
        monitor = SafetyMonitor()
        
        # Should have at least the default zones
        zone_names = [zone.name for zone in monitor.safety_zones]
        self.assertIn("critical_front", zone_names)
        self.assertIn("warning_left", zone_names)
        self.assertIn("warning_right", zone_names)
        
        # Check critical front zone configuration
        critical_zone = next(z for z in monitor.safety_zones if z.name == "critical_front")
        self.assertEqual(critical_zone.action, "stop")
        self.assertEqual(critical_zone.priority, 1)
        self.assertEqual(critical_zone.min_distance, 0.5)
    
    def test_start_safety_monitor(self):
        """Test starting the safety monitor."""
        monitor = SafetyMonitor()
        
        result = monitor.start()
        
        self.assertTrue(result)
        self.assertTrue(monitor.running)
        self.mock_mqtt_client.connect.assert_called_once()
        self.mock_mqtt_client.subscribe.assert_called()
    
    def test_stop_safety_monitor(self):
        """Test stopping the safety monitor."""
        monitor = SafetyMonitor()
        monitor.start()
        
        monitor.stop()
        
        self.assertFalse(monitor.running)
        self.mock_mqtt_client.disconnect.assert_called_once()
    
    def test_lidar_data_processing_no_obstacles(self):
        """Test processing LiDAR data with no obstacles."""
        monitor = SafetyMonitor()
        
        # Create safe LiDAR data (all distances > threshold)
        lidar_data = {
            "timestamp": datetime.now().isoformat(),
            "ranges": [2.0, 2.5, 3.0, 2.8, 2.2] * 72,  # 360 points
            "angles": list(range(0, 360, 5))  # 5-degree resolution
        }
        
        # Process data - should not trigger emergency stop
        monitor._process_lidar_data(lidar_data)
        
        self.assertFalse(monitor.emergency_stop_active)
        self.assertEqual(monitor.emergency_stops_triggered, 0)
    
    def test_lidar_data_processing_with_critical_obstacle(self):
        """Test processing LiDAR data with critical obstacle in front."""
        monitor = SafetyMonitor()
        
        # Create LiDAR data with obstacle in critical front zone
        ranges = [2.0] * 72  # Safe distances
        ranges[0] = 0.3  # Critical obstacle at 0 degrees (front)
        
        lidar_data = {
            "timestamp": datetime.now().isoformat(),
            "ranges": ranges,
            "angles": list(range(0, 360, 5))
        }
        
        # Process data - should trigger emergency stop
        monitor._process_lidar_data(lidar_data)
        
        self.assertTrue(monitor.emergency_stop_active)
        self.assertEqual(monitor.emergency_stops_triggered, 1)
        self.mock_mqtt_client.publish.assert_called()
        
        # Check that emergency stop command was published
        publish_calls = self.mock_mqtt_client.publish.call_args_list
        estop_call = None
        for call in publish_calls:
            if "orchestrator/cmd/estop" in str(call):
                estop_call = call
                break
        
        self.assertIsNotNone(estop_call)
    
    def test_lidar_data_processing_with_warning_obstacle(self):
        """Test processing LiDAR data with warning-level obstacle."""
        monitor = SafetyMonitor()
        
        # Create LiDAR data with obstacle in warning zone (side)
        ranges = [2.0] * 72  # Safe distances
        ranges[18] = 0.3  # Warning obstacle at 90 degrees (left side)
        
        lidar_data = {
            "timestamp": datetime.now().isoformat(),
            "ranges": ranges,
            "angles": list(range(0, 360, 5))
        }
        
        # Process data - should not trigger emergency stop
        monitor._process_lidar_data(lidar_data)
        
        self.assertFalse(monitor.emergency_stop_active)
        self.assertEqual(monitor.emergency_stops_triggered, 0)
        
        # Should have logged warning
        self.mock_logger.warning.assert_called()
    
    def test_check_zone_for_obstacles(self):
        """Test obstacle detection within specific zones."""
        monitor = SafetyMonitor()
        
        # Create test zone
        test_zone = SafetyZone(
            name="test_zone",
            min_angle=350.0,  # Zone crossing 0 degrees
            max_angle=10.0,
            min_distance=1.0,
            priority=1,
            action="stop"
        )
        
        # Test data with obstacles in and out of zone
        ranges = [0.5, 2.0, 0.8, 2.0, 0.6]  # Some close, some far
        angles = [355.0, 45.0, 5.0, 180.0, 2.0]  # Some in zone, some out
        
        obstacles = monitor._check_zone_for_obstacles(test_zone, ranges, angles)
        
        # Should detect obstacles at 355°, 5°, and 2° (all within zone and distance)
        expected_obstacles = [(0.5, 355.0), (0.8, 5.0), (0.6, 2.0)]
        self.assertEqual(len(obstacles), 3)
        
        for expected in expected_obstacles:
            self.assertIn(expected, obstacles)
    
    def test_handle_lidar_data_message(self):
        """Test handling MQTT LiDAR data messages."""
        monitor = SafetyMonitor()
        
        # Create mock MQTT message
        message_data = {
            "topic": "orchestrator/data/lidar_01",
            "payload": {
                "timestamp": datetime.now().isoformat(),
                "device_id": "lidar_01",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "ranges": [2.0] * 72,
                    "angles": list(range(0, 360, 5))
                }
            }
        }
        
        # Handle message
        monitor._handle_lidar_data(message_data)
        
        # Check that data was stored
        self.assertIsNotNone(monitor.last_lidar_data)
        self.assertIsNotNone(monitor.last_lidar_timestamp)
    
    def test_handle_invalid_lidar_data(self):
        """Test handling invalid LiDAR data messages."""
        monitor = SafetyMonitor()
        
        # Test message without data field
        invalid_message = {
            "topic": "orchestrator/data/lidar_01",
            "payload": {
                "timestamp": datetime.now().isoformat(),
                "device_id": "lidar_01"
                # Missing 'data' field
            }
        }
        
        # Should handle gracefully without crashing
        monitor._handle_lidar_data(invalid_message)
        
        self.mock_logger.warning.assert_called()
    
    def test_emergency_stop_command_format(self):
        """Test that emergency stop commands have correct format."""
        monitor = SafetyMonitor()
        
        # Create obstacle detection
        obstacle = ObstacleDetection(
            timestamp=datetime.now(),
            distance=0.3,
            angle=0.0,
            zone="critical_front",
            severity="critical"
        )
        
        # Trigger emergency stop
        monitor._trigger_emergency_stop([obstacle])
        
        # Check published command format
        self.mock_mqtt_client.publish.assert_called()
        
        # Get the published command
        publish_calls = self.mock_mqtt_client.publish.call_args_list
        estop_call = None
        for call in publish_calls:
            args, kwargs = call
            if args[0] == "orchestrator/cmd/estop":
                estop_call = args[1]  # The command payload
                break
        
        self.assertIsNotNone(estop_call)
        
        # Verify command structure
        self.assertIn("timestamp", estop_call)
        self.assertIn("command_id", estop_call)
        self.assertEqual(estop_call["action"], "emergency_stop")
        self.assertEqual(estop_call["reason"], "obstacle_detected")
        self.assertEqual(estop_call["source"], "safety_monitor")
        self.assertIn("obstacle_info", estop_call)
        self.assertIn("parameters", estop_call)
    
    def test_data_timeout_detection(self):
        """Test detection of LiDAR data timeouts."""
        monitor = SafetyMonitor()
        
        # Set old timestamp
        with monitor._data_lock:
            monitor.last_lidar_timestamp = datetime.now() - timedelta(seconds=10)
        
        # Check for timeout
        monitor._check_data_timeout()
        
        # Should log warning about timeout
        self.mock_logger.warning.assert_called()
    
    def test_emergency_stop_reset(self):
        """Test emergency stop reset when conditions clear."""
        monitor = SafetyMonitor()
        
        # Set emergency stop active
        monitor.emergency_stop_active = True
        
        # Clear recent detections
        monitor.obstacle_detections = []
        
        # Check for reset
        monitor._check_emergency_stop_reset()
        
        # Should reset emergency stop
        self.assertFalse(monitor.emergency_stop_active)
    
    def test_performance_monitoring(self):
        """Test performance monitoring of processing times."""
        monitor = SafetyMonitor()
        
        # Process some data to generate performance metrics
        lidar_data = {
            "timestamp": datetime.now().isoformat(),
            "ranges": [2.0] * 72,
            "angles": list(range(0, 360, 5))
        }
        
        monitor._process_lidar_data(lidar_data)
        
        # Check that performance metrics were recorded
        self.assertGreater(len(monitor.processing_times), 0)
        self.assertGreater(monitor.avg_processing_time, 0)
        self.assertGreater(monitor.max_processing_time, 0)
    
    def test_safety_status_publishing(self):
        """Test publishing of safety status messages."""
        monitor = SafetyMonitor()
        
        # Publish status
        monitor._publish_safety_status("active", "Test status message")
        
        # Check that status was published
        self.mock_mqtt_client.publish.assert_called()
        
        # Verify status message format
        publish_calls = self.mock_mqtt_client.publish.call_args_list
        status_call = None
        for call in publish_calls:
            args, kwargs = call
            if args[0] == "orchestrator/status/safety_monitor":
                status_call = args[1]
                break
        
        self.assertIsNotNone(status_call)
        self.assertIn("timestamp", status_call)
        self.assertIn("device_id", status_call)
        self.assertIn("status", status_call)
        self.assertIn("statistics", status_call)
        self.assertIn("configuration", status_call)


class TestSafetyZone(unittest.TestCase):
    """Test cases for the SafetyZone class."""
    
    def test_safety_zone_creation(self):
        """Test creating a SafetyZone."""
        zone = SafetyZone(
            name="test_zone",
            min_angle=0.0,
            max_angle=90.0,
            min_distance=1.0,
            priority=1,
            action="stop"
        )
        
        self.assertEqual(zone.name, "test_zone")
        self.assertEqual(zone.min_angle, 0.0)
        self.assertEqual(zone.max_angle, 90.0)
        self.assertEqual(zone.min_distance, 1.0)
        self.assertEqual(zone.priority, 1)
        self.assertEqual(zone.action, "stop")


class TestObstacleDetection(unittest.TestCase):
    """Test cases for the ObstacleDetection class."""
    
    def test_obstacle_detection_creation(self):
        """Test creating an ObstacleDetection."""
        timestamp = datetime.now()
        detection = ObstacleDetection(
            timestamp=timestamp,
            distance=0.5,
            angle=45.0,
            zone="test_zone",
            severity="critical"
        )
        
        self.assertEqual(detection.timestamp, timestamp)
        self.assertEqual(detection.distance, 0.5)
        self.assertEqual(detection.angle, 45.0)
        self.assertEqual(detection.zone, "test_zone")
        self.assertEqual(detection.severity, "critical")


if __name__ == "__main__":
    unittest.main()