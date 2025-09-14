"""
Simple integration test to verify MQTT and mock device communication.
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


def test_simple_mqtt_publish_receive():
    """Test basic MQTT publish and receive functionality."""
    mqtt_config = MQTTConfig(
        broker_host="localhost",
        broker_port=1883,
        client_id="test_simple"
    )
    
    mqtt_client = MockMQTTClientWrapper(mqtt_config)
    mqtt_client.connect()
    
    received_messages = []
    
    def callback(message_data):
        received_messages.append(message_data)
    
    # Subscribe and publish
    mqtt_client.subscribe_with_callback("test/topic", callback)
    mqtt_client.publish("test/topic", {"test": "data"})
    
    time.sleep(0.1)
    
    assert len(received_messages) == 1
    assert received_messages[0]["payload"]["test"] == "data"


def test_motor_controller_direct_publish():
    """Test motor controller publishing directly."""
    mqtt_config = MQTTConfig(
        broker_host="localhost",
        broker_port=1883,
        client_id="test_motor_direct"
    )
    
    mqtt_client = MockMQTTClientWrapper(mqtt_config)
    mqtt_client.connect()
    
    motor_config = {
        "name": "test_motor",
        "type": "dc",
        "gpio_pins": {"enable": 18, "direction": 19},
        "encoder_pins": {"a": 20, "b": 21},
        "max_speed": 1.0,
        "acceleration": 0.5
    }
    
    received_messages = []
    
    def callback(message_data):
        received_messages.append(message_data)
    
    # Create motor controller
    motor = MockMotorController("test_motor", mqtt_client, motor_config)
    
    # Subscribe to telemetry
    mqtt_client.subscribe_with_callback("orchestrator/data/test_motor", callback)
    
    # Test direct publish from motor
    test_data = {"position": 100, "velocity": 0.5}
    mqtt_client.publish("orchestrator/data/test_motor", {
        "timestamp": datetime.now().isoformat(),
        "device_id": "test_motor",
        "data": test_data
    })
    
    time.sleep(0.1)
    
    assert len(received_messages) == 1
    assert received_messages[0]["payload"]["data"]["position"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])