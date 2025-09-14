"""
Motor Controller Implementation for Orchestrator Platform

This module implements the MotorController class that provides DC motor control
with encoder feedback for precise distance and rotation control.

Requirements covered: 1.1, 1.2, 1.3, 2.2
"""

import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime
import json

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for development/testing environments
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        PUD_UP = "PUD_UP"
        PUD_DOWN = "PUD_DOWN"
        HIGH = 1
        LOW = 0
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode, pull_up_down=None): pass
        @staticmethod
        def output(pin, value): pass
        @staticmethod
        def input(pin): return 0
        @staticmethod
        def PWM(pin, frequency): return MockPWM()
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None): pass
        @staticmethod
        def remove_event_detect(pin): pass
        @staticmethod
        def cleanup(): pass
    
    class MockPWM:
        def start(self, duty_cycle): pass
        def ChangeDutyCycle(self, duty_cycle): pass
        def stop(self): pass
    
    GPIO = MockGPIO()

from .base import Actuator
from .config import MotorConfig


class MotorController(Actuator):
    """
    DC Motor Controller with encoder feedback for precise movement control.
    
    This class provides control for DC motors with the following features:
    - PWM speed control
    - Direction control via GPIO
    - Encoder feedback for distance measurement
    - MQTT command subscription
    - Safety limits and error handling
    """
    
    def __init__(self, device_id: str, mqtt_client, config: MotorConfig):
        """
        Initialize the motor controller.
        
        Args:
            device_id: Unique identifier for this motor
            mqtt_client: MQTT client for communication
            config: Motor configuration object
        """
        super().__init__(device_id, mqtt_client, config.__dict__)
        
        self.motor_config = config
        self.gpio_pins = config.gpio_pins
        self.encoder_pins = config.encoder_pins or {}
        self.max_speed = config.max_speed
        self.acceleration = config.acceleration
        
        # Motor state
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.direction = 1  # 1 for forward, -1 for reverse
        self.is_moving = False
        
        # Encoder state
        self.encoder_count = 0
        self.target_distance = 0.0
        self.distance_traveled = 0.0
        self.encoder_resolution = 1000  # Pulses per revolution (configurable)
        self.wheel_diameter = 0.1  # meters (configurable)
        
        # Control threads
        self._control_thread = None
        self._encoder_thread = None
        self._running = False
        self._movement_lock = threading.Lock()
        
        # PWM instance
        self._pwm = None
        self._pwm_frequency = 1000  # Hz
        
        # Movement tracking
        self.last_encoder_time = time.time()
        self.velocity = 0.0  # m/s
        
        # Command tracking
        self.current_command = None
        self.command_start_time = None
        
        self.logger.info(f"MotorController {device_id} initialized with config: {config}")
    
    def initialize(self) -> bool:
        """
        Initialize GPIO pins and start control systems.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Set GPIO mode
            GPIO.setmode(GPIO.BCM)
            
            # Setup motor control pins
            enable_pin = self.gpio_pins.get('enable')
            direction_pin = self.gpio_pins.get('direction')
            
            if not enable_pin or not direction_pin:
                self.logger.error("Missing required GPIO pins (enable, direction)")
                return False
            
            GPIO.setup(enable_pin, GPIO.OUT)
            GPIO.setup(direction_pin, GPIO.OUT)
            
            # Initialize PWM for speed control
            self._pwm = GPIO.PWM(enable_pin, self._pwm_frequency)
            self._pwm.start(0)  # Start with 0% duty cycle
            
            # Setup encoder pins if available
            if self.encoder_pins:
                encoder_a = self.encoder_pins.get('a')
                encoder_b = self.encoder_pins.get('b')
                
                if encoder_a:
                    GPIO.setup(encoder_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                    GPIO.add_event_detect(
                        encoder_a, 
                        GPIO.BOTH, 
                        callback=self._encoder_callback,
                        bouncetime=1
                    )
                
                if encoder_b:
                    GPIO.setup(encoder_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Start control threads
            self._running = True
            self._control_thread = threading.Thread(target=self._control_loop, daemon=True)
            self._control_thread.start()
            
            # Subscribe to MQTT commands
            self.subscribe_to_commands()
            
            self._initialized = True
            self.set_status("ready")
            
            self.logger.info(f"Motor {self.device_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to initialize motor {self.device_id}")
            return False
    
    def execute_command(self, command: Dict[str, Any]) -> bool:
        """
        Execute a motor command received via MQTT.
        
        Args:
            command: Command dictionary with action and parameters
            
        Returns:
            bool: True if command executed successfully
        """
        try:
            action = command.get("action")
            parameters = command.get("parameters", {})
            command_id = command.get("command_id", "unknown")
            
            self.logger.info(f"Executing command: {action} with parameters: {parameters}")
            
            with self._movement_lock:
                self.current_command = command
                self.command_start_time = time.time()
                
                if action == "move_forward":
                    return self._move_forward(parameters)
                elif action == "move_backward":
                    return self._move_backward(parameters)
                elif action == "rotate_left":
                    return self._rotate_left(parameters)
                elif action == "rotate_right":
                    return self._rotate_right(parameters)
                elif action == "stop":
                    return self._stop_motor()
                elif action == "set_speed":
                    return self._set_speed(parameters)
                else:
                    self.logger.warning(f"Unknown command action: {action}")
                    return False
                    
        except Exception as e:
            self.logger.exception(f"Error executing command: {command}")
            return False
    
    def _move_forward(self, parameters: Dict[str, Any]) -> bool:
        """Execute forward movement command."""
        distance = parameters.get("distance", 0.0)  # meters
        speed = parameters.get("speed", 0.5)  # 0.0 to 1.0
        
        if distance <= 0:
            self.logger.warning("Invalid distance for forward movement")
            return False
        
        return self._execute_movement(distance, speed, 1)
    
    def _move_backward(self, parameters: Dict[str, Any]) -> bool:
        """Execute backward movement command."""
        distance = parameters.get("distance", 0.0)  # meters
        speed = parameters.get("speed", 0.5)  # 0.0 to 1.0
        
        if distance <= 0:
            self.logger.warning("Invalid distance for backward movement")
            return False
        
        return self._execute_movement(distance, speed, -1)
    
    def _rotate_left(self, parameters: Dict[str, Any]) -> bool:
        """Execute left rotation command."""
        angle = parameters.get("angle", 0.0)  # degrees
        speed = parameters.get("speed", 0.3)  # 0.0 to 1.0
        
        if angle <= 0:
            self.logger.warning("Invalid angle for left rotation")
            return False
        
        # Convert angle to distance (simplified calculation)
        # This would need calibration for actual robot
        rotation_distance = (angle / 360.0) * 3.14159 * 0.3  # Assuming 30cm wheelbase
        return self._execute_movement(rotation_distance, speed, -1)  # Left motor reverse
    
    def _rotate_right(self, parameters: Dict[str, Any]) -> bool:
        """Execute right rotation command."""
        angle = parameters.get("angle", 0.0)  # degrees
        speed = parameters.get("speed", 0.3)  # 0.0 to 1.0
        
        if angle <= 0:
            self.logger.warning("Invalid angle for right rotation")
            return False
        
        # Convert angle to distance (simplified calculation)
        rotation_distance = (angle / 360.0) * 3.14159 * 0.3  # Assuming 30cm wheelbase
        return self._execute_movement(rotation_distance, speed, 1)  # Left motor forward
    
    def _execute_movement(self, distance: float, speed: float, direction: int) -> bool:
        """
        Execute a movement with specified distance, speed, and direction.
        
        Args:
            distance: Distance to travel in meters
            speed: Speed as fraction of max_speed (0.0 to 1.0)
            direction: 1 for forward, -1 for reverse
        """
        try:
            # Validate parameters
            speed = max(0.0, min(1.0, speed))  # Clamp to valid range
            
            # Reset encoder tracking
            self.encoder_count = 0
            self.distance_traveled = 0.0
            self.target_distance = distance
            
            # Set motor parameters
            self.direction = direction
            self.target_speed = speed * self.max_speed
            self.is_moving = True
            
            # Set GPIO direction
            direction_pin = self.gpio_pins.get('direction')
            GPIO.output(direction_pin, GPIO.HIGH if direction > 0 else GPIO.LOW)
            
            self.set_status("moving")
            self.logger.info(f"Started movement: distance={distance}m, speed={speed}, direction={direction}")
            
            return True
            
        except Exception as e:
            self.logger.exception("Error executing movement")
            return False
    
    def _set_speed(self, parameters: Dict[str, Any]) -> bool:
        """Set motor speed without distance target."""
        speed = parameters.get("speed", 0.0)
        direction = parameters.get("direction", 1)
        
        speed = max(0.0, min(1.0, speed))
        
        with self._movement_lock:
            self.target_speed = speed * self.max_speed
            self.direction = direction
            self.target_distance = float('inf')  # Continuous movement
            self.is_moving = speed > 0
            
            # Set GPIO direction
            direction_pin = self.gpio_pins.get('direction')
            GPIO.output(direction_pin, GPIO.HIGH if direction > 0 else GPIO.LOW)
            
            if self.is_moving:
                self.set_status("moving")
            else:
                self.set_status("ready")
        
        return True
    
    def _stop_motor(self) -> bool:
        """Stop the motor immediately."""
        try:
            with self._movement_lock:
                self.is_moving = False
                self.target_speed = 0.0
                self.current_speed = 0.0
                
                if self._pwm:
                    self._pwm.ChangeDutyCycle(0)
                
                self.set_status("stopped")
                self.logger.info("Motor stopped")
            
            return True
            
        except Exception as e:
            self.logger.exception("Error stopping motor")
            return False
    
    def _control_loop(self):
        """Main control loop for motor speed and position control."""
        while self._running:
            try:
                if self.is_moving and self._initialized:
                    # Check if target distance reached
                    if (self.target_distance != float('inf') and 
                        self.distance_traveled >= self.target_distance):
                        self._stop_motor()
                        continue
                    
                    # Gradual acceleration/deceleration
                    speed_diff = self.target_speed - self.current_speed
                    if abs(speed_diff) > 0.01:
                        acceleration_step = self.acceleration * 0.1  # 100ms steps
                        if speed_diff > 0:
                            self.current_speed += min(acceleration_step, speed_diff)
                        else:
                            self.current_speed += max(-acceleration_step, speed_diff)
                    
                    # Apply PWM duty cycle (0-100%)
                    duty_cycle = min(100, abs(self.current_speed) * 100 / self.max_speed)
                    if self._pwm:
                        self._pwm.ChangeDutyCycle(duty_cycle)
                    
                    # Publish status
                    self._publish_motor_status()
                
                time.sleep(0.1)  # 10Hz control loop
                
            except Exception as e:
                self.logger.exception("Error in motor control loop")
                time.sleep(0.1)
    
    def _encoder_callback(self, channel):
        """Callback for encoder pulse detection."""
        try:
            current_time = time.time()
            
            # Increment encoder count
            self.encoder_count += 1
            
            # Calculate distance traveled
            # Distance per pulse = wheel circumference / encoder resolution
            wheel_circumference = 3.14159 * self.wheel_diameter
            distance_per_pulse = wheel_circumference / self.encoder_resolution
            self.distance_traveled = self.encoder_count * distance_per_pulse
            
            # Calculate velocity
            time_diff = current_time - self.last_encoder_time
            if time_diff > 0:
                self.velocity = distance_per_pulse / time_diff
            
            self.last_encoder_time = current_time
            
        except Exception as e:
            self.logger.exception("Error in encoder callback")
    
    def _publish_motor_status(self):
        """Publish current motor status and telemetry."""
        try:
            status_data = {
                "motor_id": self.device_id,
                "is_moving": self.is_moving,
                "current_speed": self.current_speed,
                "target_speed": self.target_speed,
                "direction": self.direction,
                "encoder_count": self.encoder_count,
                "distance_traveled": self.distance_traveled,
                "target_distance": self.target_distance,
                "velocity": self.velocity,
                "duty_cycle": abs(self.current_speed) * 100 / self.max_speed if self.max_speed > 0 else 0
            }
            
            # Publish to telemetry topic
            telemetry_topic = f"orchestrator/data/{self.device_id}"
            telemetry_message = {
                "timestamp": datetime.now().isoformat(),
                "device_id": self.device_id,
                "data": status_data
            }
            
            if self.mqtt_client:
                self.mqtt_client.publish(telemetry_topic, json.dumps(telemetry_message))
            
        except Exception as e:
            self.logger.exception("Error publishing motor status")
    
    def stop(self) -> None:
        """Stop the motor and clean up resources."""
        try:
            self._running = False
            self._stop_motor()
            
            # Wait for control thread to finish
            if self._control_thread and self._control_thread.is_alive():
                self._control_thread.join(timeout=2.0)
            
            # Clean up PWM
            if self._pwm:
                self._pwm.stop()
                self._pwm = None
            
            # Clean up encoder interrupts
            if self.encoder_pins:
                encoder_a = self.encoder_pins.get('a')
                if encoder_a:
                    try:
                        GPIO.remove_event_detect(encoder_a)
                    except:
                        pass
            
            # Unsubscribe from commands
            self.unsubscribe_from_commands()
            
            self.set_status("stopped")
            self.logger.info(f"Motor {self.device_id} stopped and cleaned up")
            
        except Exception as e:
            self.logger.exception("Error stopping motor controller")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current motor status."""
        return {
            "device_id": self.device_id,
            "status": self.status,
            "initialized": self._initialized,
            "is_moving": self.is_moving,
            "current_speed": self.current_speed,
            "target_speed": self.target_speed,
            "direction": self.direction,
            "encoder_count": self.encoder_count,
            "distance_traveled": self.distance_traveled,
            "target_distance": self.target_distance,
            "velocity": self.velocity,
            "last_updated": self.last_updated.isoformat(),
            "gpio_pins": self.gpio_pins,
            "encoder_pins": self.encoder_pins
        }