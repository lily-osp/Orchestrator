"""
Hardware Abstraction Layer (HAL) Service

This package provides the hardware abstraction layer for the Orchestrator platform,
enabling modular control of robotic hardware components through standardized interfaces.
"""

from .base import Device, Sensor, Actuator
from .config import (
    ConfigurationService, 
    OrchestratorConfig,
    MotorConfig,
    SensorConfig,
    LoggingConfig,
    get_config_service,
    load_config
)
from .logging_service import (
    LoggingService,
    StructuredLogger,
    get_logging_service,
    get_logger,
    configure_logging,
    log_startup,
    log_shutdown
)
from .encoder_sensor import EncoderSensor

__version__ = "0.1.0"
__all__ = [
    "Device", 
    "Sensor", 
    "Actuator",
    "ConfigurationService",
    "OrchestratorConfig", 
    "MotorConfig",
    "SensorConfig",
    "LoggingConfig",
    "get_config_service",
    "load_config",
    "LoggingService",
    "StructuredLogger",
    "get_logging_service",
    "get_logger",
    "configure_logging",
    "log_startup",
    "log_shutdown",
    "EncoderSensor"
]