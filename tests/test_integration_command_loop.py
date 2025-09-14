"""
Integration tests for the full command loop (MQTT -> HAL -> MQTT).

These tests validate the complete flow from command reception through
hardware execution to telemetry publication.
"""

import pytest
import json
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime

# Add hal_service to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hal_service'))

from hal_service.mock.mock_mqtt_client import MockMQTTClient, MockMQTTClientWrapper
from hal_service.mock.mock_devices import MockMotorController, MockEncoderSensor, MockLidarSensor
from hal_service.config import MQTTConfig


@pytest.mark.integration
class TestCommandLoopIntegration:
    """Test the complete command loop integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mqtt_config = MQTTConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="test_integration"
        )
        
        self.motor_config = {
            "name": "test_motor",
            "type": "dc",
            "gpio_pins": {"enable": 18, "direction": 19},
            "encoder_pins": {"a": 20, "b": 21},
            "max_speed": 1.0,
            "acceleration": 0.5
        }
        
        # Create mock MQTT client
        self.mqtt_client = MockMQTTClientWrapper(self.mqtt_config)
        self.mqtt_client.connect()
        
        # Track received messages
        self.received_messages = []
        
    def message_callback(self, message_data):
        """Callback to track received messages."""
        self.received_messages.append(message_data)
    
    def test_motor_command_to_telemetry_loop(self):
        """Test complete motor command to telemetry loop."""
        # Create mock motor controller
        motor = MockMotorController("test_motor", self.mqtt_client, self.motor_config)
        motor.initialize()  # Initialize the motor controller
        
        # Subscribe to telemetry
        self.mqtt_client.subscribe_with_callback("orchestrator/data/test_motor", self.message_callback)
        
        # Send motor command
        command = {
            "timestamp": datetime.now().isoformat(),
            "command_id": "test_cmd_001",
            "action": "move_forward",
            "parameters": {
                "distance": 100,
                "speed": 0.5
            }
        }
        
        # Execute command
        motor.execute_command(command)
        
        # Allow time for processing
        time.sleep(0.1)
        
        # Verify command was processed
        assert motor.get_status()["status"] == "moving"
        
        # The motor controller automatically starts telemetry publishing when initialized
        # Allow time for telemetry
        time.sleep(0.3)
        
        # Verify telemetry was published
        assert len(self.received_messages) > 0
        
        telemetry = self.received_messages[-1]
        assert telemetry["topic"] == "orchestrator/data/test_motor"
        assert "data" in telemetry["payload"]
        
        motor.stop()


@pytest.mark.integration
class TestMQTTCommunicationReliability:
    """Test MQTT communication reliability and error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mqtt_config = MQTTConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="test_reliability"
        )
        
        self.mqtt_client = MockMQTTClientWrapper(self.mqtt_config)
        self.received_messages = []
    
    def message_callback(self, message_data):
        """Callback to track received messages."""
        self.received_messages.append(message_data)
    
    def test_connection_recovery(self):
        """Test MQTT connection recovery."""
        # Connect initially
        assert self.mqtt_client.connect() is True
        assert self.mqtt_client.is_connected is True
        
        # Simulate disconnection
        self.mqtt_client.disconnect()
        assert self.mqtt_client.is_connected is False
        
        # Reconnect
        assert self.mqtt_client.connect() is True
        assert self.mqtt_client.is_connected is True
    
    def test_message_delivery_confirmation(self):
        """Test message delivery confirmation."""
        self.mqtt_client.connect()
        
        # Subscribe to test topic
        self.mqtt_client.subscribe_with_callback("test/topic", self.message_callback)
        
        # Publish message
        test_payload = {"test": "data", "timestamp": datetime.now().isoformat()}
        result = self.mqtt_client.publish("test/topic", test_payload)
        
        assert result is True
        
        # Allow time for message delivery
        time.sleep(0.1)
        
        # Verify message was received
        assert len(self.received_messages) > 0
        assert self.received_messages[-1]["payload"]["test"] == "data"
    
    def test_topic_pattern_matching(self):
        """Test MQTT topic pattern matching with wildcards."""
        self.mqtt_client.connect()
        
        # Subscribe with wildcard patterns
        self.mqtt_client.subscribe_with_callback("orchestrator/+/motors", self.message_callback)
        self.mqtt_client.subscribe_with_callback("orchestrator/data/+", self.message_callback)
        
        # Publish to matching topics
        self.mqtt_client.publish("orchestrator/cmd/motors", {"action": "stop"})
        self.mqtt_client.publish("orchestrator/data/lidar", {"ranges": [1.0, 2.0]})
        self.mqtt_client.publish("orchestrator/status/system", {"status": "ok"})
        
        time.sleep(0.1)
        
        # Verify pattern matching
        cmd_messages = [msg for msg in self.received_messages if "cmd" in msg["topic"]]
        data_messages = [msg for msg in self.received_messages if "data" in msg["topic"]]
        status_messages = [msg for msg in self.received_messages if "status" in msg["topic"]]
        
        assert len(cmd_messages) > 0  # Should match orchestrator/+/motors
        assert len(data_messages) > 0  # Should match orchestrator/data/+
        assert len(status_messages) == 0  # Should not match either pattern
    
    def test_json_serialization_deserialization(self):
        """Test JSON serialization and deserialization."""
        self.mqtt_client.connect()
        self.mqtt_client.subscribe_with_callback("test/json", self.message_callback)
        
        # Test various data types
        test_data = {
            "string": "test_value",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {
                "key": "value",
                "number": 123
            }
        }
        
        # Publish and receive
        self.mqtt_client.publish("test/json", test_data)
        time.sleep(0.1)
        
        # Verify data integrity
        assert len(self.received_messages) > 0
        received_data = self.received_messages[-1]["payload"]
        
        assert received_data["string"] == "test_value"
        assert received_data["integer"] == 42
        assert received_data["float"] == 3.14159
        assert received_data["boolean"] is True
        assert received_data["null"] is None
        assert received_data["array"] == [1, 2, 3]
        assert received_data["nested"]["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])