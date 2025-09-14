"""
Mock Hardware Abstraction Layer for Orchestrator Platform

This module provides mock implementations of all HAL components for testing
and development without physical hardware. It simulates realistic sensor data
and acknowledges commands through MQTT interface.

Requirements covered: 1.4, 6.2
"""

from .mock_orchestrator import MockHALOrchestrator
from .mock_devices import (
    MockMotorController,
    MockEncoderSensor, 
    MockLidarSensor,
    MockSafetyMonitor,
    MockStateManager
)
from .mock_mqtt_client import MockMQTTClient
from .data_generators import (
    LidarDataGenerator,
    EncoderDataGenerator,
    MotorDataGenerator
)

__all__ = [
    'MockHALOrchestrator',
    'MockMotorController',
    'MockEncoderSensor',
    'MockLidarSensor', 
    'MockSafetyMonitor',
    'MockStateManager',
    'MockMQTTClient',
    'LidarDataGenerator',
    'EncoderDataGenerator',
    'MotorDataGenerator'
]