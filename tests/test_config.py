"""
Tests for the Configuration Service.

This module tests the configuration loading, validation, and management
functionality of the HAL configuration service.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from pydantic import ValidationError

from hal_service.config import (
    ConfigurationService,
    OrchestratorConfig,
    MotorConfig,
    SensorConfig,
    GPIOConfig,
    I2CConfig,
    UARTConfig,
    get_config_service,
    load_config
)


class TestConfigurationModels:
    """Test the Pydantic configuration models."""
    
    def test_gpio_config_valid(self):
        """Test valid GPIO configuration."""
        config = GPIOConfig(pin=18, mode="OUT")
        assert config.pin == 18
        assert config.mode == "OUT"
    
    def test_gpio_config_invalid_pin(self):
        """Test invalid GPIO pin number."""
        with pytest.raises(ValidationError):
            GPIOConfig(pin=50, mode="OUT")  # Pin > 40
    
    def test_gpio_config_invalid_mode(self):
        """Test invalid GPIO mode."""
        with pytest.raises(ValidationError):
            GPIOConfig(pin=18, mode="INVALID")
    
    def test_i2c_config_valid(self):
        """Test valid I2C configuration."""
        config = I2CConfig(address="0x48", bus=1)
        assert config.address == "0x48"
        assert config.bus == 1
    
    def test_i2c_config_invalid_address(self):
        """Test invalid I2C address format."""
        with pytest.raises(ValidationError):
            I2CConfig(address="48", bus=1)  # Missing 0x prefix
    
    def test_uart_config_valid(self):
        """Test valid UART configuration."""
        config = UARTConfig(port="/dev/ttyUSB0", baudrate=115200)
        assert config.port == "/dev/ttyUSB0"
        assert config.baudrate == 115200
    
    def test_motor_config_valid(self):
        """Test valid motor configuration."""
        config = MotorConfig(
            name="test_motor",
            type="dc",
            gpio_pins={"enable": 18, "direction": 19},
            max_speed=1.0,
            acceleration=0.5
        )
        assert config.name == "test_motor"
        assert config.type == "dc"
        assert config.gpio_pins["enable"] == 18
    
    def test_motor_config_missing_gpio_pins(self):
        """Test motor config with missing required GPIO pins."""
        with pytest.raises(ValidationError):
            MotorConfig(
                name="test_motor",
                type="dc",
                gpio_pins={"enable": 18},  # Missing direction pin
                max_speed=1.0,
                acceleration=0.5
            )
    
    def test_sensor_config_valid(self):
        """Test valid sensor configuration."""
        interface = GPIOConfig(pin=20, mode="IN")
        config = SensorConfig(
            name="test_sensor",
            type="encoder",
            interface=interface,
            publish_rate=10.0
        )
        assert config.name == "test_sensor"
        assert config.type == "encoder"
        assert config.publish_rate == 10.0


class TestConfigurationService:
    """Test the ConfigurationService class."""
    
    def create_test_config(self) -> dict:
        """Create a test configuration dictionary."""
        return {
            "system": {
                "log_level": "DEBUG",
                "log_format": "json"
            },
            "mqtt": {
                "broker_host": "localhost",
                "broker_port": 1883
            },
            "safety": {
                "enabled": True,
                "obstacle_threshold": 0.5
            },
            "motors": [
                {
                    "name": "test_motor",
                    "type": "dc",
                    "gpio_pins": {
                        "enable": 18,
                        "direction": 19
                    },
                    "max_speed": 1.0,
                    "acceleration": 0.5
                }
            ],
            "sensors": [
                {
                    "name": "test_sensor",
                    "type": "encoder",
                    "interface": {
                        "pin": 20,
                        "mode": "IN"
                    },
                    "publish_rate": 10.0
                }
            ]
        }
    
    def test_load_config_from_file(self):
        """Test loading configuration from a YAML file."""
        config_data = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            service = ConfigurationService(config_path)
            config = service.load_config()
            
            assert isinstance(config, OrchestratorConfig)
            assert config.system.log_level == "DEBUG"
            assert config.mqtt.broker_host == "localhost"
            assert len(config.motors) == 1
            assert config.motors[0].name == "test_motor"
            assert len(config.sensors) == 1
            assert config.sensors[0].name == "test_sensor"
        finally:
            Path(config_path).unlink()
    
    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        service = ConfigurationService("/nonexistent/config.yaml")
        
        with pytest.raises(FileNotFoundError):
            service.load_config()
    
    def test_load_config_invalid_yaml(self):
        """Test loading config with invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            service = ConfigurationService(config_path)
            with pytest.raises(yaml.YAMLError):
                service.load_config()
        finally:
            Path(config_path).unlink()
    
    def test_load_config_validation_error(self):
        """Test loading config that fails validation."""
        invalid_config = {
            "motors": [
                {
                    "name": "invalid_motor",
                    "type": "invalid_type",  # Invalid motor type
                    "gpio_pins": {"enable": 18},  # Missing direction pin
                    "max_speed": 1.0,
                    "acceleration": 0.5
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            config_path = f.name
        
        try:
            service = ConfigurationService(config_path)
            with pytest.raises(ValidationError):
                service.load_config()
        finally:
            Path(config_path).unlink()
    
    def test_get_motor_config(self):
        """Test retrieving specific motor configuration."""
        config_data = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            service = ConfigurationService(config_path)
            service.load_config()
            
            motor_config = service.get_motor_config("test_motor")
            assert motor_config is not None
            assert motor_config.name == "test_motor"
            assert motor_config.type == "dc"
            
            # Test non-existent motor
            missing_motor = service.get_motor_config("nonexistent")
            assert missing_motor is None
        finally:
            Path(config_path).unlink()
    
    def test_get_sensor_config(self):
        """Test retrieving specific sensor configuration."""
        config_data = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            service = ConfigurationService(config_path)
            service.load_config()
            
            sensor_config = service.get_sensor_config("test_sensor")
            assert sensor_config is not None
            assert sensor_config.name == "test_sensor"
            assert sensor_config.type == "encoder"
            
            # Test non-existent sensor
            missing_sensor = service.get_sensor_config("nonexistent")
            assert missing_sensor is None
        finally:
            Path(config_path).unlink()
    
    def test_validate_config_file(self):
        """Test configuration file validation."""
        config_data = self.create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            service = ConfigurationService()
            is_valid = service.validate_config_file(config_path)
            assert is_valid is True
        finally:
            Path(config_path).unlink()
    
    def test_create_default_config(self):
        """Test creating a default configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            
            service = ConfigurationService()
            created_path = service.create_default_config(config_path)
            
            assert created_path == config_path
            assert config_path.exists()
            
            # Verify the created config is valid
            service = ConfigurationService(config_path)
            config = service.load_config()
            assert isinstance(config, OrchestratorConfig)
    
    def test_environment_variable_substitution(self):
        """Test environment variable substitution in config."""
        import os
        
        # Set test environment variable
        os.environ["TEST_MQTT_HOST"] = "test.example.com"
        
        config_data = {
            "mqtt": {
                "broker_host": "${TEST_MQTT_HOST}",
                "broker_port": 1883
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            service = ConfigurationService(config_path)
            config = service.load_config()
            
            assert config.mqtt.broker_host == "test.example.com"
        finally:
            Path(config_path).unlink()
            # Clean up environment variable
            del os.environ["TEST_MQTT_HOST"]
    
    def test_environment_variable_with_default(self):
        """Test environment variable substitution with default value."""
        config_data = {
            "mqtt": {
                "broker_host": "${NONEXISTENT_VAR:default.example.com}",
                "broker_port": 1883
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            service = ConfigurationService(config_path)
            config = service.load_config()
            
            assert config.mqtt.broker_host == "default.example.com"
        finally:
            Path(config_path).unlink()


class TestGlobalConfigService:
    """Test the global configuration service functions."""
    
    def test_get_config_service_singleton(self):
        """Test that get_config_service returns the same instance."""
        # Reset global state
        import hal_service.config
        hal_service.config._config_service = None
        
        service1 = get_config_service()
        service2 = get_config_service()
        
        assert service1 is service2
    
    def test_load_config_convenience_function(self):
        """Test the load_config convenience function."""
        config_data = {
            "system": {"log_level": "INFO"},
            "mqtt": {"broker_host": "localhost"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Reset global state
            import hal_service.config
            hal_service.config._config_service = None
            
            config = load_config(config_path)
            assert isinstance(config, OrchestratorConfig)
            assert config.system.log_level == "INFO"
        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])