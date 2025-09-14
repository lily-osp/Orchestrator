"""
Integration tests for the full command loop (MQTT -> HAL -> MQTT).

These tests validate the complete flow from command reception through
hardware execution to telemetry publication.
"""

import pytest
import time
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hal_service'))

from hal_service.mock.mock_mqtt_client import MockMQTTClientWrapper
from hal_service.mock.mock_devices import MockMotorController
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
        
        # Allow time for telemetry
        time.sleep(0.3)
        
        # Verify telemetry was published
        assert len(self.received_messages) > 0
        
        telemetry = self.received_messages[-1]
        assert telemetry["topic"] == "orchestrator/data/test_motor"
        assert "data" in telemetry["payload"]
        
        motor.stop()
    
    def test_mqtt_message_format_validation(self):
        """Test MQTT message format validation."""
        # Create mock motor controller
        motor = MockMotorController("test_motor", self.mqtt_client, self.motor_config)
        motor.initialize()
        
        # Subscribe to telemetry
        self.mqtt_client.subscribe_with_callback("orchestrator/data/test_motor", self.message_callback)
        
        # Allow time for telemetry
        time.sleep(0.3)
        
        # Verify message format
        assert len(self.received_messages) > 0
        
        message = self.received_messages[-1]
        
        # Validate message structure
        assert "topic" in message
        assert "payload" in message
        assert "received_at" in message
        
        payload = message["payload"]
        assert "timestamp" in payload
        assert "device_id" in payload
        assert "data" in payload
        
        # Validate timestamp format
        timestamp = payload["timestamp"]
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise
        
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])