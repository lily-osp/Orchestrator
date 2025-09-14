"""
Pytest configuration and shared fixtures for the test suite.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client for testing."""
    client = MagicMock()
    client.publish.return_value = MagicMock()
    client.subscribe.return_value = MagicMock()
    return client


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "mqtt": {
            "broker": "localhost",
            "port": 1883,
            "keepalive": 60
        },
        "devices": {
            "motor_controller": {
                "type": "MotorController",
                "gpio_pins": {"left_motor": 18, "right_motor": 19}
            }
        }
    }