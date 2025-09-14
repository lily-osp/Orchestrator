"""
Encoder Sensor Implementation for Orchestrator Platform

This module implements the EncoderSensor class that provides wheel encoder reading
with GPIO interrupts for precise distance and velocity measurement.

Requirements covered: 1.1, 1.2, 1.3, 2.2
"""

import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime

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
        RISING = "RISING"
        FALLING = "FALLING"
        BOTH = "BOTH"
        HIGH = 1
        LOW = 0
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode, pull_up_down=None): pass
        @staticmethod
        def input(pin): return 0
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None): pass
        @staticmethod
        def remove_event_detect(pin): pass
        @staticmethod
        def cleanup(): pass
    
    GPIO = MockGPIO()

from .base import Sensor
from .config import SensorConfig


class EncoderSensor(Sensor):
    """
    Wheel Encoder Sensor for precise distance and velocity measurement.
    
    This class provides encoder reading with the following features:
    - GPIO interrupt-based pulse counting
    - Quadrature encoder support (A/B channels)
    - Real-time velocity calculation
    - Cumulative distance tracking
    - MQTT telemetry publishing
    """
    
    def __init__(self, device_id: str, mqtt_client, config: SensorConfig):
        """
        Initialize the encoder sensor.
        
        Args:
            device_id: Unique identifier for this encoder
            mqtt_client: MQTT client for communication
            config: Sensor configuration object
        """
        super().__init__(device_id, mqtt_client, config.__dict__, config.publish_rate)
        
        self.sensor_config = config
        
        # Extract GPIO configuration
        calibration = config.calibration or {}
        if hasattr(config.interface, 'pin'):
            # Single pin encoder (simple pulse counting)
            self.encoder_pin_a = config.interface.pin
            self.encoder_pin_b = calibration.get('pin_b')
            if self.encoder_pin_b is not None:
                self.encoder_pin_b = int(self.encoder_pin_b)
            self.pull_up_down = getattr(config.interface, 'pull_up_down', 'PUD_UP')
        else:
            # Assume dual pin configuration in calibration
            self.encoder_pin_a = calibration.get('pin_a')
            if self.encoder_pin_a is not None:
                self.encoder_pin_a = int(self.encoder_pin_a)
            self.encoder_pin_b = calibration.get('pin_b')
            if self.encoder_pin_b is not None:
                self.encoder_pin_b = int(self.encoder_pin_b)
            self.pull_up_down = 'PUD_UP'
        
        # Encoder parameters from calibration
        self.encoder_resolution = int(calibration.get('resolution', 1000))  # Pulses per revolution
        self.wheel_diameter = float(calibration.get('wheel_diameter', 0.1))  # meters
        self.gear_ratio = float(calibration.get('gear_ratio', 1.0))  # Motor to wheel gear ratio
        
        # Encoder state
        self.tick_count = 0
        self.total_distance = 0.0
        self.velocity = 0.0
        self.direction = 1  # 1 for forward, -1 for reverse
        
        # Timing for velocity calculation
        self.last_tick_time = time.time()
        self.last_velocity_update = time.time()
        self.velocity_window = 0.1  # seconds for velocity averaging
        self.recent_ticks = []  # List of (timestamp, tick_count) tuples
        
        # Thread safety
        self._encoder_lock = threading.Lock()
        
        # Quadrature state (for dual channel encoders)
        self.last_a_state = 0
        self.last_b_state = 0
        
        # Performance tracking
        self.interrupt_count = 0
        self.last_interrupt_time = 0
        
        self.logger.info(f"EncoderSensor {device_id} initialized with config: {config}")
    
    def initialize(self) -> bool:
        """
        Initialize GPIO pins and interrupt handlers.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Set GPIO mode
            GPIO.setmode(GPIO.BCM)
            
            # Validate pin configuration
            if not self.encoder_pin_a:
                self.logger.error("Missing encoder pin A configuration")
                return False
            
            # Setup encoder pin A
            pull_mode = getattr(GPIO, self.pull_up_down, GPIO.PUD_UP)
            GPIO.setup(self.encoder_pin_a, GPIO.IN, pull_up_down=pull_mode)
            
            # Setup encoder pin B if available (quadrature)
            if self.encoder_pin_b:
                GPIO.setup(self.encoder_pin_b, GPIO.IN, pull_up_down=pull_mode)
                self.logger.info(f"Configured quadrature encoder on pins {self.encoder_pin_a}, {self.encoder_pin_b}")
            else:
                self.logger.info(f"Configured single-channel encoder on pin {self.encoder_pin_a}")
            
            # Add interrupt detection for encoder pin A
            GPIO.add_event_detect(
                self.encoder_pin_a,
                GPIO.BOTH,  # Detect both rising and falling edges
                callback=self._encoder_interrupt_a,
                bouncetime=1  # 1ms debounce
            )
            
            # Add interrupt for pin B if quadrature
            if self.encoder_pin_b:
                GPIO.add_event_detect(
                    self.encoder_pin_b,
                    GPIO.BOTH,
                    callback=self._encoder_interrupt_b,
                    bouncetime=1
                )
            
            # Initialize state readings
            self.last_a_state = GPIO.input(self.encoder_pin_a)
            if self.encoder_pin_b:
                self.last_b_state = GPIO.input(self.encoder_pin_b)
            
            self._initialized = True
            self.set_status("ready")
            
            # Start publishing telemetry
            self.start_publishing()
            
            self.logger.info(f"EncoderSensor {self.device_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to initialize encoder sensor {self.device_id}")
            return False
    
    def _encoder_interrupt_a(self, channel):
        """
        Interrupt handler for encoder channel A.
        
        Args:
            channel: GPIO channel that triggered the interrupt
        """
        try:
            current_time = time.time()
            
            with self._encoder_lock:
                # Read current states
                a_state = GPIO.input(self.encoder_pin_a)
                b_state = GPIO.input(self.encoder_pin_b) if self.encoder_pin_b else 0
                
                # Determine direction and count
                if self.encoder_pin_b:
                    # Quadrature encoding - determine direction
                    if a_state != self.last_a_state:
                        if a_state != b_state:
                            self.direction = 1  # Forward
                            self.tick_count += 1
                        else:
                            self.direction = -1  # Reverse
                            self.tick_count -= 1
                else:
                    # Single channel - assume forward direction
                    if a_state != self.last_a_state:
                        self.tick_count += self.direction
                
                # Update states
                self.last_a_state = a_state
                self.last_b_state = b_state
                
                # Update timing and velocity
                self._update_velocity(current_time)
                
                # Performance tracking
                self.interrupt_count += 1
                self.last_interrupt_time = current_time
                
        except Exception as e:
            self.logger.exception("Error in encoder interrupt A")
    
    def _encoder_interrupt_b(self, channel):
        """
        Interrupt handler for encoder channel B (quadrature only).
        
        Args:
            channel: GPIO channel that triggered the interrupt
        """
        try:
            current_time = time.time()
            
            with self._encoder_lock:
                # Read current states
                a_state = GPIO.input(self.encoder_pin_a)
                b_state = GPIO.input(self.encoder_pin_b)
                
                # Quadrature encoding - determine direction
                if b_state != self.last_b_state:
                    if a_state == b_state:
                        self.direction = 1  # Forward
                        self.tick_count += 1
                    else:
                        self.direction = -1  # Reverse
                        self.tick_count -= 1
                
                # Update states
                self.last_a_state = a_state
                self.last_b_state = b_state
                
                # Update timing and velocity
                self._update_velocity(current_time)
                
                # Performance tracking
                self.interrupt_count += 1
                self.last_interrupt_time = current_time
                
        except Exception as e:
            self.logger.exception("Error in encoder interrupt B")
    
    def _update_velocity(self, current_time: float):
        """
        Update velocity calculation based on recent tick data.
        
        Args:
            current_time: Current timestamp
        """
        # Add current tick to recent history
        self.recent_ticks.append((current_time, self.tick_count))
        
        # Remove old ticks outside velocity window
        cutoff_time = current_time - self.velocity_window
        self.recent_ticks = [(t, count) for t, count in self.recent_ticks if t >= cutoff_time]
        
        # Calculate velocity if we have enough data
        if len(self.recent_ticks) >= 2:
            oldest_time, oldest_count = self.recent_ticks[0]
            time_diff = current_time - oldest_time
            tick_diff = self.tick_count - oldest_count
            
            if time_diff > 0:
                # Calculate distance per tick
                wheel_circumference = 3.14159 * self.wheel_diameter
                distance_per_tick = (wheel_circumference / self.encoder_resolution) / self.gear_ratio
                
                # Calculate velocity (m/s)
                distance_traveled = tick_diff * distance_per_tick
                self.velocity = distance_traveled / time_diff
        
        # Update total distance
        wheel_circumference = 3.14159 * self.wheel_diameter
        distance_per_tick = (wheel_circumference / self.encoder_resolution) / self.gear_ratio
        self.total_distance = self.tick_count * distance_per_tick
    
    def read_data(self) -> Dict[str, Any]:
        """
        Read current encoder data.
        
        Returns:
            Dict containing current encoder readings
        """
        try:
            current_time = time.time()
            
            with self._encoder_lock:
                # Calculate derived values
                wheel_circumference = 3.14159 * self.wheel_diameter
                distance_per_tick = (wheel_circumference / self.encoder_resolution) / self.gear_ratio
                
                # Calculate RPM if we have recent velocity data
                rpm = 0.0
                if abs(self.velocity) > 0.001:  # Avoid division by very small numbers
                    wheel_rps = abs(self.velocity) / wheel_circumference  # Revolutions per second
                    rpm = wheel_rps * 60.0  # Convert to RPM
                
                data = {
                    "tick_count": self.tick_count,
                    "total_distance": self.total_distance,
                    "velocity": self.velocity,
                    "direction": self.direction,
                    "rpm": rpm,
                    "distance_per_tick": distance_per_tick,
                    "wheel_diameter": self.wheel_diameter,
                    "encoder_resolution": self.encoder_resolution,
                    "gear_ratio": self.gear_ratio,
                    "interrupt_count": self.interrupt_count,
                    "last_interrupt_time": self.last_interrupt_time,
                    "pins": {
                        "encoder_a": self.encoder_pin_a,
                        "encoder_b": self.encoder_pin_b
                    }
                }
                
                return data
                
        except Exception as e:
            self.logger.exception("Error reading encoder data")
            return {
                "tick_count": 0,
                "total_distance": 0.0,
                "velocity": 0.0,
                "direction": 0,
                "error": str(e)
            }
    
    def reset_encoder(self):
        """Reset encoder counts and distance tracking."""
        try:
            with self._encoder_lock:
                self.tick_count = 0
                self.total_distance = 0.0
                self.velocity = 0.0
                self.recent_ticks.clear()
                self.interrupt_count = 0
                
            self.logger.info(f"Encoder {self.device_id} reset")
            
        except Exception as e:
            self.logger.exception("Error resetting encoder")
    
    def set_direction(self, direction: int):
        """
        Set the direction multiplier for single-channel encoders.
        
        Args:
            direction: 1 for forward, -1 for reverse
        """
        if direction in [1, -1]:
            with self._encoder_lock:
                self.direction = direction
            self.logger.info(f"Encoder {self.device_id} direction set to {direction}")
        else:
            self.logger.warning(f"Invalid direction value: {direction}")
    
    def stop(self) -> None:
        """Stop the encoder sensor and clean up resources."""
        try:
            # Stop publishing
            self.stop_publishing()
            
            # Remove GPIO interrupts
            if self.encoder_pin_a:
                try:
                    GPIO.remove_event_detect(self.encoder_pin_a)
                except:
                    pass
            
            if self.encoder_pin_b:
                try:
                    GPIO.remove_event_detect(self.encoder_pin_b)
                except:
                    pass
            
            self.set_status("stopped")
            self.logger.info(f"EncoderSensor {self.device_id} stopped and cleaned up")
            
        except Exception as e:
            self.logger.exception("Error stopping encoder sensor")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current encoder sensor status."""
        return {
            "device_id": self.device_id,
            "status": self.status,
            "initialized": self._initialized,
            "tick_count": self.tick_count,
            "total_distance": self.total_distance,
            "velocity": self.velocity,
            "direction": self.direction,
            "interrupt_count": self.interrupt_count,
            "last_updated": self.last_updated.isoformat(),
            "pins": {
                "encoder_a": self.encoder_pin_a,
                "encoder_b": self.encoder_pin_b
            },
            "config": {
                "encoder_resolution": self.encoder_resolution,
                "wheel_diameter": self.wheel_diameter,
                "gear_ratio": self.gear_ratio,
                "publish_rate": self.publish_rate
            }
        }