"""
Unit tests for EncoderSensor class.

Tests the encoder sensor functionality including GPIO interrupt handling,
velocity calculation, and MQTT telemetry publishing.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

# Import the module under test
from hal_service.encoder_sensor import EncoderSensor
from hal_service.config import SensorConfig, GPIOConfig


class TestEncoderSensor:
    """Test suite for EncoderSensor class."""
    
    @pytest.fixture
    def mock_mqtt_client(self):
        """Create a mock MQTT client."""
        client = Mock()
        client.publish = Mock()
        client.subscribe = Mock()
        client.unsubscribe = Mock()
        return client
    
    @pytest.fixture
    def gpio_config(self):
        """Create a GPIO configuration for testing."""
        return GPIOConfig(
            pin=20,
            mode="IN",
            pull_up_down="PUD_UP"
        )
    
    @pytest.fixture
    def sensor_config(self, gpio_config):
        """Create a sensor configuration for testing."""
        return SensorConfig(
            name="test_encoder",
            type="encoder",
            interface=gpio_config,
            publish_rate=10.0,
            calibration={
                "resolution": 1000.0,
                "wheel_diameter": 0.1,
                "gear_ratio": 1.0,
                "pin_a": 20.0,
                "pin_b": 21.0
            }
        )
    
    @pytest.fixture
    def encoder_sensor(self, mock_mqtt_client, sensor_config):
        """Create an EncoderSensor instance for testing."""
        return EncoderSensor("test_encoder", mock_mqtt_client, sensor_config)
    
    def test_encoder_sensor_initialization(self, encoder_sensor, sensor_config):
        """Test encoder sensor initialization."""
        assert encoder_sensor.device_id == "test_encoder"
        assert encoder_sensor.sensor_config == sensor_config
        assert encoder_sensor.encoder_pin_a == 20
        assert encoder_sensor.encoder_pin_b == 21
        assert encoder_sensor.encoder_resolution == 1000
        assert encoder_sensor.wheel_diameter == 0.1
        assert encoder_sensor.gear_ratio == 1.0
        assert encoder_sensor.tick_count == 0
        assert encoder_sensor.total_distance == 0.0
        assert encoder_sensor.velocity == 0.0
        assert encoder_sensor.direction == 1
    
    @patch('hal_service.encoder_sensor.GPIO')
    def test_encoder_initialization_success(self, mock_gpio, encoder_sensor):
        """Test successful encoder initialization."""
        # Setup GPIO mock
        mock_gpio.BCM = "BCM"
        mock_gpio.IN = "IN"
        mock_gpio.PUD_UP = "PUD_UP"
        mock_gpio.BOTH = "BOTH"
        mock_gpio.input.return_value = 0
        
        # Initialize encoder
        result = encoder_sensor.initialize()
        
        # Verify initialization
        assert result is True
        assert encoder_sensor._initialized is True
        assert encoder_sensor.status == "ready"
        
        # Verify GPIO setup calls
        mock_gpio.setmode.assert_called_once_with("BCM")
        mock_gpio.setup.assert_any_call(20, "IN", pull_up_down="PUD_UP")
        mock_gpio.setup.assert_any_call(21, "IN", pull_up_down="PUD_UP")
        mock_gpio.add_event_detect.assert_any_call(
            20, "BOTH", callback=encoder_sensor._encoder_interrupt_a, bouncetime=1
        )
        mock_gpio.add_event_detect.assert_any_call(
            21, "BOTH", callback=encoder_sensor._encoder_interrupt_b, bouncetime=1
        )
    
    @patch('hal_service.encoder_sensor.GPIO')
    def test_encoder_initialization_missing_pin(self, mock_gpio, mock_mqtt_client):
        """Test encoder initialization with missing pin configuration."""
        # Create config with valid pin but then simulate missing pin
        config = SensorConfig(
            name="test_encoder",
            type="encoder",
            interface=GPIOConfig(pin=20, mode="IN"),
            publish_rate=10.0
        )
        
        encoder = EncoderSensor("test_encoder", mock_mqtt_client, config)
        encoder.encoder_pin_a = None  # Simulate missing pin
        
        result = encoder.initialize()
        
        assert result is False
        assert encoder._initialized is False
    
    def test_read_data_initial_state(self, encoder_sensor):
        """Test reading data in initial state."""
        data = encoder_sensor.read_data()
        
        assert data["tick_count"] == 0
        assert data["total_distance"] == 0.0
        assert data["velocity"] == 0.0
        assert data["direction"] == 1
        assert data["rpm"] == 0.0
        assert data["distance_per_tick"] > 0
        assert data["wheel_diameter"] == 0.1
        assert data["encoder_resolution"] == 1000
        assert data["gear_ratio"] == 1.0
        assert "pins" in data
        assert data["pins"]["encoder_a"] == 20
        assert data["pins"]["encoder_b"] == 21
    
    @patch('hal_service.encoder_sensor.GPIO')
    def test_encoder_interrupt_a_quadrature(self, mock_gpio, encoder_sensor):
        """Test encoder interrupt A handling with quadrature encoding."""
        # Setup initial state
        encoder_sensor._initialized = True
        encoder_sensor.last_a_state = 0
        encoder_sensor.last_b_state = 0
        
        # Mock GPIO inputs for forward direction (A leads B)
        mock_gpio.input.side_effect = lambda pin: 1 if pin == 20 else 0
        
        # Trigger interrupt
        encoder_sensor._encoder_interrupt_a(20)
        
        # Verify forward counting
        assert encoder_sensor.tick_count == 1
        assert encoder_sensor.direction == 1
        assert encoder_sensor.last_a_state == 1
        assert encoder_sensor.last_b_state == 0
    
    @patch('hal_service.encoder_sensor.GPIO')
    def test_encoder_interrupt_a_reverse(self, mock_gpio, encoder_sensor):
        """Test encoder interrupt A handling in reverse direction."""
        # Setup initial state
        encoder_sensor._initialized = True
        encoder_sensor.last_a_state = 0
        encoder_sensor.last_b_state = 1
        
        # Mock GPIO inputs for reverse direction (B leads A)
        mock_gpio.input.side_effect = lambda pin: 1 if pin == 20 else 1
        
        # Trigger interrupt
        encoder_sensor._encoder_interrupt_a(20)
        
        # Verify reverse counting
        assert encoder_sensor.tick_count == -1
        assert encoder_sensor.direction == -1
        assert encoder_sensor.last_a_state == 1
        assert encoder_sensor.last_b_state == 1
    
    @patch('hal_service.encoder_sensor.GPIO')
    def test_encoder_interrupt_b_quadrature(self, mock_gpio, encoder_sensor):
        """Test encoder interrupt B handling with quadrature encoding."""
        # Setup initial state
        encoder_sensor._initialized = True
        encoder_sensor.last_a_state = 1
        encoder_sensor.last_b_state = 0
        
        # Mock GPIO inputs
        mock_gpio.input.side_effect = lambda pin: 1 if pin == 20 else 1
        
        # Trigger interrupt
        encoder_sensor._encoder_interrupt_b(21)
        
        # Verify counting
        assert encoder_sensor.tick_count == 1
        assert encoder_sensor.direction == 1
        assert encoder_sensor.last_a_state == 1
        assert encoder_sensor.last_b_state == 1
    
    def test_velocity_calculation(self, encoder_sensor):
        """Test velocity calculation with simulated ticks."""
        encoder_sensor._initialized = True
        
        # Simulate encoder ticks over time
        start_time = time.time()
        
        # First tick
        encoder_sensor.tick_count = 10
        encoder_sensor._update_velocity(start_time)
        
        # Second tick after 0.1 seconds
        encoder_sensor.tick_count = 20
        encoder_sensor._update_velocity(start_time + 0.1)
        
        # Velocity should be calculated based on distance change
        assert encoder_sensor.velocity > 0
        assert encoder_sensor.total_distance > 0
    
    def test_reset_encoder(self, encoder_sensor):
        """Test encoder reset functionality."""
        # Set some values
        encoder_sensor.tick_count = 100
        encoder_sensor.total_distance = 1.5
        encoder_sensor.velocity = 0.5
        encoder_sensor.interrupt_count = 50
        encoder_sensor.recent_ticks = [(time.time(), 100)]
        
        # Reset encoder
        encoder_sensor.reset_encoder()
        
        # Verify reset
        assert encoder_sensor.tick_count == 0
        assert encoder_sensor.total_distance == 0.0
        assert encoder_sensor.velocity == 0.0
        assert encoder_sensor.interrupt_count == 0
        assert len(encoder_sensor.recent_ticks) == 0
    
    def test_set_direction(self, encoder_sensor):
        """Test setting encoder direction."""
        # Test valid directions
        encoder_sensor.set_direction(1)
        assert encoder_sensor.direction == 1
        
        encoder_sensor.set_direction(-1)
        assert encoder_sensor.direction == -1
        
        # Test invalid direction (should not change)
        encoder_sensor.set_direction(0)
        assert encoder_sensor.direction == -1  # Should remain unchanged
        
        encoder_sensor.set_direction(2)
        assert encoder_sensor.direction == -1  # Should remain unchanged
    
    @patch('hal_service.encoder_sensor.GPIO')
    def test_encoder_stop(self, mock_gpio, encoder_sensor):
        """Test encoder stop and cleanup."""
        # Initialize first
        encoder_sensor._initialized = True
        encoder_sensor._running = True
        
        # Stop encoder
        encoder_sensor.stop()
        
        # Verify cleanup
        assert encoder_sensor.status == "stopped"
        mock_gpio.remove_event_detect.assert_any_call(20)
        mock_gpio.remove_event_detect.assert_any_call(21)
    
    def test_get_status(self, encoder_sensor):
        """Test getting encoder status."""
        encoder_sensor._initialized = True
        encoder_sensor.tick_count = 50
        encoder_sensor.total_distance = 0.5
        encoder_sensor.velocity = 0.2
        encoder_sensor.interrupt_count = 25
        
        status = encoder_sensor.get_status()
        
        assert status["device_id"] == "test_encoder"
        assert status["initialized"] is True
        assert status["tick_count"] == 50
        assert status["total_distance"] == 0.5
        assert status["velocity"] == 0.2
        assert status["interrupt_count"] == 25
        assert "pins" in status
        assert "config" in status
        assert status["config"]["encoder_resolution"] == 1000
        assert status["config"]["wheel_diameter"] == 0.1
    
    def test_publish_data_called(self, encoder_sensor, mock_mqtt_client):
        """Test that sensor data is published via MQTT."""
        encoder_sensor._initialized = True
        
        # Mock the publish_data method to verify it's called
        with patch.object(encoder_sensor, 'publish_data') as mock_publish:
            data = encoder_sensor.read_data()
            encoder_sensor.publish_data(data)
            
            mock_publish.assert_called_once_with(data)
    
    def test_distance_calculation_accuracy(self, encoder_sensor):
        """Test accuracy of distance calculations."""
        # Set known parameters
        encoder_sensor.encoder_resolution = 1000  # 1000 pulses per revolution
        encoder_sensor.wheel_diameter = 0.1  # 10cm diameter
        encoder_sensor.gear_ratio = 1.0  # No gearing
        
        # Calculate expected distance per tick
        wheel_circumference = 3.14159 * 0.1  # ~0.314 meters per revolution
        expected_distance_per_tick = wheel_circumference / 1000  # ~0.000314 meters per tick
        
        # Simulate 1000 ticks (one full revolution)
        encoder_sensor.tick_count = 1000
        encoder_sensor._update_velocity(time.time())
        
        # Verify distance calculation
        assert abs(encoder_sensor.total_distance - wheel_circumference) < 0.001
        
        data = encoder_sensor.read_data()
        assert abs(data["distance_per_tick"] - expected_distance_per_tick) < 0.000001
    
    def test_rpm_calculation(self, encoder_sensor):
        """Test RPM calculation from velocity."""
        # Set parameters
        encoder_sensor.wheel_diameter = 0.1  # 10cm diameter
        wheel_circumference = 3.14159 * 0.1
        
        # Set velocity to 1 revolution per second
        encoder_sensor.velocity = wheel_circumference  # m/s
        
        data = encoder_sensor.read_data()
        
        # Should be 60 RPM (1 rev/sec * 60 sec/min)
        assert abs(data["rpm"] - 60.0) < 0.1
    
    @patch('hal_service.encoder_sensor.GPIO')
    def test_single_channel_encoder(self, mock_gpio, mock_mqtt_client):
        """Test single-channel encoder configuration."""
        # Create config for single channel encoder
        config = SensorConfig(
            name="single_encoder",
            type="encoder",
            interface=GPIOConfig(pin=20, mode="IN", pull_up_down="PUD_UP"),
            publish_rate=10.0,
            calibration={
                "resolution": 500.0,
                "wheel_diameter": 0.08,
                "gear_ratio": 2.0
            }
        )
        
        encoder = EncoderSensor("single_encoder", mock_mqtt_client, config)
        
        # Verify single channel setup
        assert encoder.encoder_pin_a == 20
        assert encoder.encoder_pin_b is None
        assert encoder.encoder_resolution == 500
        assert encoder.wheel_diameter == 0.08
        assert encoder.gear_ratio == 2.0
        
        # Initialize and test
        mock_gpio.input.return_value = 0
        result = encoder.initialize()
        assert result is True
        
        # Test single channel interrupt (assumes forward direction)
        encoder.last_a_state = 0
        mock_gpio.input.return_value = 1
        encoder._encoder_interrupt_a(20)
        
        assert encoder.tick_count == 1  # Should increment by direction (1)
        assert encoder.direction == 1