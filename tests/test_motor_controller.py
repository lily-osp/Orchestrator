"""
Unit tests for MotorController class.

Tests the motor controller functionality including command execution,
encoder feedback, and MQTT communication.
"""

import pytest
import json
import time
import threading
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from hal_service.motor_controller import MotorController
from hal_service.config import MotorConfig


@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    client = Mock()
    client.publish = Mock()
    client.subscribe = Mock()
    client.unsubscribe = Mock()
    client.message_callback_add = Mock()
    client.message_callback_remove = Mock()
    return client


@pytest.fixture
def motor_config():
    """Create a test motor configuration."""
    return MotorConfig(
        name="test_motor",
        type="dc",
        gpio_pins={
            "enable": 18,
            "direction": 19
        },
        encoder_pins={
            "a": 20,
            "b": 21
        },
        max_speed=1.0,
        acceleration=0.5
    )


@pytest.fixture
def motor_controller(mock_mqtt_client, motor_config):
    """Create a MotorController instance for testing."""
    with patch('hal_service.motor_controller.GPIO'):
        controller = MotorController("test_motor", mock_mqtt_client, motor_config)
        yield controller
        # Cleanup
        controller._running = False
        if controller._control_thread and controller._control_thread.is_alive():
            controller._control_thread.join(timeout=1.0)


class TestMotorControllerInitialization:
    """Test motor controller initialization."""
    
    def test_init_with_valid_config(self, mock_mqtt_client, motor_config):
        """Test initialization with valid configuration."""
        with patch('hal_service.motor_controller.GPIO'):
            controller = MotorController("test_motor", mock_mqtt_client, motor_config)
            
            assert controller.device_id == "test_motor"
            assert controller.motor_config == motor_config
            assert controller.gpio_pins == motor_config.gpio_pins
            assert controller.encoder_pins == motor_config.encoder_pins
            assert controller.max_speed == 1.0
            assert controller.acceleration == 0.5
            assert controller.current_speed == 0.0
            assert controller.is_moving is False
    
    @patch('hal_service.motor_controller.GPIO')
    def test_initialize_success(self, mock_gpio, motor_controller):
        """Test successful GPIO initialization."""
        mock_pwm = Mock()
        mock_gpio.PWM.return_value = mock_pwm
        
        result = motor_controller.initialize()
        
        assert result is True
        assert motor_controller._initialized is True
        assert motor_controller.status == "ready"
        
        # Verify GPIO setup calls
        mock_gpio.setmode.assert_called_once_with(mock_gpio.BCM)
        mock_gpio.setup.assert_any_call(18, mock_gpio.OUT)  # enable pin
        mock_gpio.setup.assert_any_call(19, mock_gpio.OUT)  # direction pin
        mock_gpio.setup.assert_any_call(20, mock_gpio.IN, pull_up_down=mock_gpio.PUD_UP)  # encoder A
        
        # Verify PWM setup
        mock_gpio.PWM.assert_called_once_with(18, 1000)
        mock_pwm.start.assert_called_once_with(0)
    
    @patch('hal_service.motor_controller.GPIO')
    def test_initialize_missing_pins(self, mock_gpio, mock_mqtt_client):
        """Test initialization with missing GPIO pins."""
        config = MotorConfig(
            name="test_motor",
            type="dc",
            gpio_pins={"enable": 18},  # Missing direction pin
            max_speed=1.0,
            acceleration=0.5
        )
        
        controller = MotorController("test_motor", mock_mqtt_client, config)
        result = controller.initialize()
        
        assert result is False
        assert controller._initialized is False


class TestMotorControllerCommands:
    """Test motor controller command execution."""
    
    def test_execute_move_forward_command(self, motor_controller):
        """Test forward movement command execution."""
        with patch.object(motor_controller, '_execute_movement') as mock_execute:
            mock_execute.return_value = True
            
            command = {
                "action": "move_forward",
                "parameters": {
                    "distance": 1.0,
                    "speed": 0.5
                },
                "command_id": "test_cmd_001"
            }
            
            result = motor_controller.execute_command(command)
            
            assert result is True
            mock_execute.assert_called_once_with(1.0, 0.5, 1)
    
    def test_execute_move_backward_command(self, motor_controller):
        """Test backward movement command execution."""
        with patch.object(motor_controller, '_execute_movement') as mock_execute:
            mock_execute.return_value = True
            
            command = {
                "action": "move_backward",
                "parameters": {
                    "distance": 0.5,
                    "speed": 0.3
                }
            }
            
            result = motor_controller.execute_command(command)
            
            assert result is True
            mock_execute.assert_called_once_with(0.5, 0.3, -1)
    
    def test_execute_rotate_left_command(self, motor_controller):
        """Test left rotation command execution."""
        with patch.object(motor_controller, '_execute_movement') as mock_execute:
            mock_execute.return_value = True
            
            command = {
                "action": "rotate_left",
                "parameters": {
                    "angle": 90.0,
                    "speed": 0.3
                }
            }
            
            result = motor_controller.execute_command(command)
            
            assert result is True
            # Verify rotation distance calculation (90 degrees = 1/4 of circle)
            expected_distance = (90.0 / 360.0) * 3.14159 * 0.3
            mock_execute.assert_called_once_with(expected_distance, 0.3, -1)
    
    def test_execute_stop_command(self, motor_controller):
        """Test stop command execution."""
        with patch.object(motor_controller, '_stop_motor') as mock_stop:
            mock_stop.return_value = True
            
            command = {"action": "stop"}
            result = motor_controller.execute_command(command)
            
            assert result is True
            mock_stop.assert_called_once()
    
    def test_execute_set_speed_command(self, motor_controller):
        """Test set speed command execution."""
        command = {
            "action": "set_speed",
            "parameters": {
                "speed": 0.7,
                "direction": 1
            }
        }
        
        result = motor_controller.execute_command(command)
        
        assert result is True
        assert motor_controller.target_speed == 0.7
        assert motor_controller.direction == 1
        assert motor_controller.target_distance == float('inf')
    
    def test_execute_invalid_command(self, motor_controller):
        """Test execution of invalid command."""
        command = {"action": "invalid_action"}
        result = motor_controller.execute_command(command)
        
        assert result is False
    
    def test_execute_command_with_invalid_parameters(self, motor_controller):
        """Test command execution with invalid parameters."""
        command = {
            "action": "move_forward",
            "parameters": {
                "distance": -1.0,  # Invalid negative distance
                "speed": 0.5
            }
        }
        
        result = motor_controller.execute_command(command)
        
        assert result is False


class TestMotorControllerMovement:
    """Test motor controller movement execution."""
    
    @patch('hal_service.motor_controller.GPIO')
    def test_execute_movement(self, mock_gpio, motor_controller):
        """Test movement execution with valid parameters."""
        motor_controller._initialized = True
        
        result = motor_controller._execute_movement(1.0, 0.5, 1)
        
        assert result is True
        assert motor_controller.target_distance == 1.0
        assert motor_controller.target_speed == 0.5  # 0.5 * max_speed (1.0)
        assert motor_controller.direction == 1
        assert motor_controller.is_moving is True
        assert motor_controller.status == "moving"
        
        # Verify GPIO direction pin set
        mock_gpio.output.assert_called_with(19, mock_gpio.HIGH)
    
    @patch('hal_service.motor_controller.GPIO')
    def test_execute_movement_reverse(self, mock_gpio, motor_controller):
        """Test reverse movement execution."""
        motor_controller._initialized = True
        
        result = motor_controller._execute_movement(0.5, 0.3, -1)
        
        assert result is True
        assert motor_controller.direction == -1
        
        # Verify GPIO direction pin set for reverse
        mock_gpio.output.assert_called_with(19, mock_gpio.LOW)
    
    def test_stop_motor(self, motor_controller):
        """Test motor stop functionality."""
        motor_controller.is_moving = True
        motor_controller.target_speed = 0.5
        motor_controller.current_speed = 0.3
        motor_controller._pwm = Mock()
        
        result = motor_controller._stop_motor()
        
        assert result is True
        assert motor_controller.is_moving is False
        assert motor_controller.target_speed == 0.0
        assert motor_controller.current_speed == 0.0
        assert motor_controller.status == "stopped"
        
        motor_controller._pwm.ChangeDutyCycle.assert_called_once_with(0)


class TestMotorControllerEncoder:
    """Test motor controller encoder functionality."""
    
    def test_encoder_callback(self, motor_controller):
        """Test encoder pulse callback."""
        motor_controller.encoder_count = 0
        motor_controller.distance_traveled = 0.0
        motor_controller.encoder_resolution = 1000
        motor_controller.wheel_diameter = 0.1
        
        # Simulate encoder pulse
        motor_controller._encoder_callback(20)
        
        assert motor_controller.encoder_count == 1
        
        # Calculate expected distance
        wheel_circumference = 3.14159 * 0.1
        expected_distance = wheel_circumference / 1000
        assert abs(motor_controller.distance_traveled - expected_distance) < 0.0001
    
    def test_encoder_velocity_calculation(self, motor_controller):
        """Test encoder velocity calculation."""
        motor_controller.encoder_resolution = 1000
        motor_controller.wheel_diameter = 0.1
        motor_controller.last_encoder_time = time.time() - 0.1  # 100ms ago
        
        motor_controller._encoder_callback(20)
        
        # Velocity should be calculated based on time difference
        assert motor_controller.velocity > 0


class TestMotorControllerStatus:
    """Test motor controller status and telemetry."""
    
    def test_get_status(self, motor_controller):
        """Test status retrieval."""
        motor_controller._initialized = True
        motor_controller.is_moving = True
        motor_controller.current_speed = 0.5
        motor_controller.encoder_count = 100
        
        status = motor_controller.get_status()
        
        assert status["device_id"] == "test_motor"
        assert status["initialized"] is True
        assert status["is_moving"] is True
        assert status["current_speed"] == 0.5
        assert status["encoder_count"] == 100
        assert "gpio_pins" in status
        assert "encoder_pins" in status
    
    def test_publish_motor_status(self, motor_controller):
        """Test motor status publishing."""
        motor_controller.is_moving = True
        motor_controller.current_speed = 0.5
        motor_controller.max_speed = 1.0
        
        motor_controller._publish_motor_status()
        
        # Verify MQTT publish was called
        motor_controller.mqtt_client.publish.assert_called()
        
        # Get the published message
        call_args = motor_controller.mqtt_client.publish.call_args
        topic = call_args[0][0]
        message_json = call_args[0][1]
        
        assert topic == "orchestrator/data/test_motor"
        
        message = json.loads(message_json)
        assert message["device_id"] == "test_motor"
        assert message["data"]["is_moving"] is True
        assert message["data"]["current_speed"] == 0.5


class TestMotorControllerCleanup:
    """Test motor controller cleanup and resource management."""
    
    @patch('hal_service.motor_controller.GPIO')
    def test_stop_cleanup(self, mock_gpio, motor_controller):
        """Test proper cleanup when stopping."""
        motor_controller._initialized = True
        motor_controller._running = True
        motor_controller._pwm = Mock()
        motor_controller.encoder_pins = {"a": 20}
        
        motor_controller.stop()
        
        assert motor_controller._running is False
        assert motor_controller.status == "stopped"
        
        # Verify PWM cleanup
        motor_controller._pwm.stop.assert_called_once()
        
        # Verify encoder cleanup
        mock_gpio.remove_event_detect.assert_called_with(20)
        
        # Verify MQTT cleanup
        motor_controller.mqtt_client.unsubscribe.assert_called()


class TestMotorControllerIntegration:
    """Integration tests for motor controller."""
    
    @patch('hal_service.motor_controller.GPIO')
    def test_full_movement_cycle(self, mock_gpio, motor_controller):
        """Test a complete movement cycle."""
        mock_pwm = Mock()
        mock_gpio.PWM.return_value = mock_pwm
        
        # Initialize
        assert motor_controller.initialize() is True
        
        # Execute movement command
        command = {
            "action": "move_forward",
            "parameters": {
                "distance": 1.0,
                "speed": 0.5
            }
        }
        
        assert motor_controller.execute_command(command) is True
        assert motor_controller.is_moving is True
        
        # Simulate reaching target distance
        motor_controller.distance_traveled = 1.0
        
        # Stop
        motor_controller.stop()
        assert motor_controller.is_moving is False
    
    def test_mqtt_command_handling(self, motor_controller):
        """Test MQTT command message handling."""
        # Mock MQTT message
        message = Mock()
        message.topic = "orchestrator/cmd/test_motor"
        message.payload.decode.return_value = json.dumps({
            "action": "move_forward",
            "parameters": {"distance": 0.5, "speed": 0.3},
            "command_id": "test_001"
        })
        
        with patch.object(motor_controller, 'execute_command') as mock_execute:
            mock_execute.return_value = True
            
            motor_controller._handle_command(None, None, message)
            
            mock_execute.assert_called_once()
            command = mock_execute.call_args[0][0]
            assert command["action"] == "move_forward"
            assert command["parameters"]["distance"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__])