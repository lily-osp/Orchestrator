"""
Configuration Service for the Orchestrator HAL.

This module provides configuration loading and validation for hardware devices,
supporting YAML configuration files with Pydantic schema validation.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, ValidationError


class GPIOConfig(BaseModel):
    """Configuration for GPIO-based devices."""
    pin: int = Field(..., ge=1, le=40, description="GPIO pin number (1-40)")
    mode: str = Field("OUT", pattern="^(IN|OUT|PWM)$", description="GPIO mode")
    pull_up_down: Optional[str] = Field(None, pattern="^(PUD_UP|PUD_DOWN|PUD_OFF)$")
    initial_value: Optional[int] = Field(None, ge=0, le=1)


class I2CConfig(BaseModel):
    """Configuration for I2C devices."""
    address: str = Field(..., pattern="^0x[0-9A-Fa-f]{2}$", description="I2C address in hex format")
    bus: int = Field(1, ge=0, le=1, description="I2C bus number")
    frequency: Optional[int] = Field(400000, ge=100000, le=1000000, description="I2C frequency in Hz")


class SPIConfig(BaseModel):
    """Configuration for SPI devices."""
    bus: int = Field(0, ge=0, le=1, description="SPI bus number")
    device: int = Field(0, ge=0, le=1, description="SPI device number")
    speed: int = Field(1000000, ge=1000, le=32000000, description="SPI speed in Hz")
    mode: int = Field(0, ge=0, le=3, description="SPI mode (0-3)")


class UARTConfig(BaseModel):
    """Configuration for UART/Serial devices."""
    port: str = Field(..., description="Serial port path")
    baudrate: int = Field(9600, ge=300, le=4000000, description="Baud rate")
    timeout: float = Field(1.0, ge=0.1, le=10.0, description="Read timeout in seconds")
    bytesize: int = Field(8, ge=5, le=8, description="Number of data bits")
    parity: str = Field("N", pattern="^(N|E|O|M|S)$", description="Parity setting")
    stopbits: int = Field(1, ge=1, le=2, description="Number of stop bits")


class MotorConfig(BaseModel):
    """Configuration for motor controllers."""
    name: str = Field(..., description="Motor name/identifier")
    type: str = Field(..., pattern="^(dc|servo|stepper)$", description="Motor type")
    gpio_pins: Dict[str, int] = Field(..., description="GPIO pin assignments")
    encoder_pins: Optional[Dict[str, int]] = Field(None, description="Encoder pin assignments")
    max_speed: float = Field(1.0, ge=0.1, le=10.0, description="Maximum speed")
    acceleration: float = Field(0.5, ge=0.1, le=5.0, description="Acceleration rate")
    
    @field_validator('gpio_pins')
    @classmethod
    def validate_gpio_pins(cls, v):
        required_pins = ['enable', 'direction']
        for pin in required_pins:
            if pin not in v:
                raise ValueError(f"Missing required GPIO pin: {pin}")
            if not isinstance(v[pin], int) or v[pin] < 1 or v[pin] > 40:
                raise ValueError(f"Invalid GPIO pin number for {pin}: {v[pin]}")
        return v


class SensorConfig(BaseModel):
    """Configuration for sensor devices."""
    name: str = Field(..., description="Sensor name/identifier")
    type: str = Field(..., pattern="^(lidar|encoder|imu|camera|ultrasonic)$", description="Sensor type")
    interface: Union[I2CConfig, SPIConfig, UARTConfig, GPIOConfig] = Field(..., description="Interface configuration")
    publish_rate: float = Field(1.0, ge=0.1, le=100.0, description="Data publishing rate in Hz")
    calibration: Optional[Dict[str, float]] = Field(None, description="Calibration parameters")


class SafetyConfig(BaseModel):
    """Configuration for safety systems."""
    enabled: bool = Field(True, description="Enable safety monitoring")
    obstacle_threshold: float = Field(0.5, ge=0.1, le=5.0, description="Obstacle detection threshold in meters")
    emergency_stop_timeout: float = Field(0.1, ge=0.05, le=1.0, description="Emergency stop response timeout")
    safety_zones: List[Dict[str, float]] = Field(default_factory=list, description="Defined safety zones")


class MQTTConfig(BaseModel):
    """Configuration for MQTT communication."""
    broker_host: str = Field("localhost", description="MQTT broker hostname")
    broker_port: int = Field(1883, ge=1, le=65535, description="MQTT broker port")
    username: Optional[str] = Field(None, description="MQTT username")
    password: Optional[str] = Field(None, description="MQTT password")
    keepalive: int = Field(60, ge=10, le=300, description="MQTT keepalive interval")
    qos_commands: int = Field(1, ge=0, le=2, description="QoS level for commands")
    qos_telemetry: int = Field(0, ge=0, le=2, description="QoS level for telemetry")
    client_id: Optional[str] = Field(None, description="MQTT client ID")


class LoggingConfig(BaseModel):
    """Configuration for logging system."""
    level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field("json", pattern="^(json|text)$")
    max_log_size: int = Field(10485760, ge=1048576, description="Maximum log file size in bytes")
    backup_count: int = Field(5, ge=1, le=20, description="Number of backup log files")
    log_dir: str = Field("logs", description="Directory for log files")
    console_output: bool = Field(True, description="Enable console logging")
    file_output: bool = Field(True, description="Enable file logging")


class SystemConfig(BaseModel):
    """Configuration for system-wide settings."""
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    heartbeat_interval: float = Field(30.0, ge=5.0, le=300.0, description="System heartbeat interval")


class OrchestratorConfig(BaseModel):
    """Main configuration model for the Orchestrator platform."""
    system: SystemConfig = Field(default_factory=SystemConfig)
    mqtt: MQTTConfig = Field(default_factory=MQTTConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    motors: List[MotorConfig] = Field(default_factory=list, description="Motor configurations")
    sensors: List[SensorConfig] = Field(default_factory=list, description="Sensor configurations")
    
    @field_validator('motors')
    @classmethod
    def validate_unique_motor_names(cls, v):
        names = [motor.name for motor in v]
        if len(names) != len(set(names)):
            raise ValueError("Motor names must be unique")
        return v
    
    @field_validator('sensors')
    @classmethod
    def validate_unique_sensor_names(cls, v):
        names = [sensor.name for sensor in v]
        if len(names) != len(set(names)):
            raise ValueError("Sensor names must be unique")
        return v


class ConfigurationService:
    """
    Service for loading and managing configuration from YAML files.
    
    Provides configuration loading with schema validation, environment variable
    substitution, and configuration merging capabilities.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration service.
        
        Args:
            config_path: Path to the configuration file. If None, uses default locations.
        """
        self.config_path = self._resolve_config_path(config_path)
        self._config: Optional[OrchestratorConfig] = None
    
    def _resolve_config_path(self, config_path: Optional[Union[str, Path]]) -> Path:
        """
        Resolve the configuration file path using default locations if not specified.
        
        Args:
            config_path: User-specified config path or None
            
        Returns:
            Path: Resolved configuration file path
        """
        if config_path:
            return Path(config_path)
        
        # Default search locations
        search_paths = [
            Path("config.yaml"),
            Path("config/orchestrator.yaml"),
            Path("/etc/orchestrator/config.yaml"),
            Path.home() / ".orchestrator" / "config.yaml"
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        # Return the first default if none exist (will be created)
        return search_paths[0]
    
    def load_config(self, reload: bool = False) -> OrchestratorConfig:
        """
        Load configuration from the YAML file with validation.
        
        Args:
            reload: Force reload even if config is already loaded
            
        Returns:
            OrchestratorConfig: Validated configuration object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config validation fails
            yaml.YAMLError: If YAML parsing fails
        """
        if self._config is not None and not reload:
            return self._config
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            # Substitute environment variables
            raw_config = self._substitute_env_vars(raw_config)
            
            # Validate and create config object
            self._config = OrchestratorConfig(**raw_config)
            
            return self._config
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML config: {e}")
        except ValidationError as e:
            raise e
    
    def _substitute_env_vars(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively substitute environment variables in configuration values.
        
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Dict with environment variables substituted
        """
        if isinstance(config_dict, dict):
            return {k: self._substitute_env_vars(v) for k, v in config_dict.items()}
        elif isinstance(config_dict, list):
            return [self._substitute_env_vars(item) for item in config_dict]
        elif isinstance(config_dict, str):
            return self._substitute_env_var_string(config_dict)
        else:
            return config_dict
    
    def _substitute_env_var_string(self, value: str) -> str:
        """
        Substitute environment variables in a string value.
        
        Args:
            value: String that may contain environment variable references
            
        Returns:
            String with environment variables substituted
        """
        import re
        
        def replace_env_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(var_expr, match.group(0))
        
        return re.sub(r'\$\{([^}]+)\}', replace_env_var, value)
    
    def get_motor_config(self, motor_name: str) -> Optional[MotorConfig]:
        """
        Get configuration for a specific motor by name.
        
        Args:
            motor_name: Name of the motor
            
        Returns:
            MotorConfig if found, None otherwise
        """
        if not self._config:
            self.load_config()
        
        for motor in self._config.motors:
            if motor.name == motor_name:
                return motor
        return None
    
    def get_sensor_config(self, sensor_name: str) -> Optional[SensorConfig]:
        """
        Get configuration for a specific sensor by name.
        
        Args:
            sensor_name: Name of the sensor
            
        Returns:
            SensorConfig if found, None otherwise
        """
        if not self._config:
            self.load_config()
        
        for sensor in self._config.sensors:
            if sensor.name == sensor_name:
                return sensor
        return None
    
    def validate_config_file(self, config_path: Optional[Union[str, Path]] = None) -> bool:
        """
        Validate a configuration file without loading it into the service.
        
        Args:
            config_path: Path to config file to validate, or None for current config
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if config_path:
                temp_service = ConfigurationService(config_path)
                temp_service.load_config()
            else:
                self.load_config()
            return True
        except (FileNotFoundError, ValidationError, yaml.YAMLError):
            return False
    
    def create_default_config(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Create a default configuration file with example values.
        
        Args:
            output_path: Where to write the config file, or None for default location
            
        Returns:
            Path: Path where the config file was created
        """
        if output_path:
            config_path = Path(output_path)
        else:
            config_path = self.config_path
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create default configuration
        default_config = {
            "system": {
                "logging": {
                    "level": "INFO",
                    "format": "json",
                    "max_log_size": 10485760,
                    "backup_count": 5,
                    "log_dir": "logs",
                    "console_output": True,
                    "file_output": True
                },
                "heartbeat_interval": 30.0
            },
            "mqtt": {
                "broker_host": "${MQTT_HOST:localhost}",
                "broker_port": 1883,
                "keepalive": 60,
                "qos_commands": 1,
                "qos_telemetry": 0
            },
            "safety": {
                "enabled": True,
                "obstacle_threshold": 0.5,
                "emergency_stop_timeout": 0.1
            },
            "motors": [
                {
                    "name": "left_motor",
                    "type": "dc",
                    "gpio_pins": {
                        "enable": 18,
                        "direction": 19
                    },
                    "encoder_pins": {
                        "a": 20,
                        "b": 21
                    },
                    "max_speed": 1.0,
                    "acceleration": 0.5
                },
                {
                    "name": "right_motor", 
                    "type": "dc",
                    "gpio_pins": {
                        "enable": 22,
                        "direction": 23
                    },
                    "encoder_pins": {
                        "a": 24,
                        "b": 25
                    },
                    "max_speed": 1.0,
                    "acceleration": 0.5
                }
            ],
            "sensors": [
                {
                    "name": "lidar_01",
                    "type": "lidar",
                    "interface": {
                        "port": "/dev/ttyUSB0",
                        "baudrate": 115200,
                        "timeout": 1.0
                    },
                    "publish_rate": 10.0
                },
                {
                    "name": "left_encoder",
                    "type": "encoder", 
                    "interface": {
                        "pin": 20,
                        "mode": "IN",
                        "pull_up_down": "PUD_UP"
                    },
                    "publish_rate": 20.0
                }
            ]
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        return config_path


# Global configuration service instance
_config_service: Optional[ConfigurationService] = None


def get_config_service(config_path: Optional[Union[str, Path]] = None) -> ConfigurationService:
    """
    Get the global configuration service instance.
    
    Args:
        config_path: Path to config file (only used on first call)
        
    Returns:
        ConfigurationService: Global configuration service instance
    """
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService(config_path)
    return _config_service


def load_config(config_path: Optional[Union[str, Path]] = None) -> OrchestratorConfig:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Path to config file
        
    Returns:
        OrchestratorConfig: Loaded and validated configuration
    """
    service = get_config_service(config_path)
    return service.load_config()