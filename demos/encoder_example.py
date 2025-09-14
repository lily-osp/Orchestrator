#!/usr/bin/env python3
"""
Example usage of the EncoderSensor class.

This example demonstrates how to configure and use the EncoderSensor
for wheel encoder monitoring in the Orchestrator platform.
"""

import time
import signal
import sys
from typing import Optional

from mqtt_client import MQTTClientService
from encoder_sensor import EncoderSensor
from config import SensorConfig, GPIOConfig
from logging_service import get_logging_service


class EncoderExample:
    """Example application demonstrating EncoderSensor usage."""
    
    def __init__(self):
        """Initialize the encoder example."""
        self.mqtt_client: Optional[MQTTClientService] = None
        self.left_encoder: Optional[EncoderSensor] = None
        self.right_encoder: Optional[EncoderSensor] = None
        self.running = False
        
        # Setup logging
        logging_service = get_logging_service()
        self.logger = logging_service.get_device_logger("encoder_example")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def setup_mqtt(self) -> bool:
        """Setup MQTT client connection."""
        try:
            self.mqtt_client = MQTTClientService(
                broker_host="localhost",
                broker_port=1883,
                client_id="encoder_example"
            )
            
            if self.mqtt_client.connect():
                self.logger.info("MQTT client connected successfully")
                return True
            else:
                self.logger.error("Failed to connect MQTT client")
                return False
                
        except Exception as e:
            self.logger.exception("Error setting up MQTT client")
            return False
    
    def setup_encoders(self) -> bool:
        """Setup encoder sensors."""
        try:
            # Left wheel encoder configuration
            left_config = SensorConfig(
                name="left_encoder",
                type="encoder",
                interface=GPIOConfig(
                    pin=20,
                    mode="IN",
                    pull_up_down="PUD_UP"
                ),
                publish_rate=20.0,  # 20 Hz publishing rate
                calibration={
                    "pin_a": 20,
                    "pin_b": 21,
                    "resolution": 1000,  # 1000 pulses per revolution
                    "wheel_diameter": 0.1,  # 10cm diameter wheels
                    "gear_ratio": 1.0,  # Direct drive
                    "pull_up_down": "PUD_UP"
                }
            )
            
            # Right wheel encoder configuration
            right_config = SensorConfig(
                name="right_encoder",
                type="encoder",
                interface=GPIOConfig(
                    pin=22,
                    mode="IN",
                    pull_up_down="PUD_UP"
                ),
                publish_rate=20.0,
                calibration={
                    "pin_a": 22,
                    "pin_b": 23,
                    "resolution": 1000,
                    "wheel_diameter": 0.1,
                    "gear_ratio": 1.0,
                    "pull_up_down": "PUD_UP"
                }
            )
            
            # Create encoder instances
            self.left_encoder = EncoderSensor("left_encoder", self.mqtt_client, left_config)
            self.right_encoder = EncoderSensor("right_encoder", self.mqtt_client, right_config)
            
            # Initialize encoders
            if not self.left_encoder.initialize():
                self.logger.error("Failed to initialize left encoder")
                return False
            
            if not self.right_encoder.initialize():
                self.logger.error("Failed to initialize right encoder")
                return False
            
            self.logger.info("Encoders initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception("Error setting up encoders")
            return False
    
    def print_encoder_status(self):
        """Print current encoder status to console."""
        try:
            left_data = self.left_encoder.read_data()
            right_data = self.right_encoder.read_data()
            
            print("\n" + "="*60)
            print("ENCODER STATUS")
            print("="*60)
            
            print(f"Left Encoder:")
            print(f"  Ticks: {left_data['tick_count']:>8}")
            print(f"  Distance: {left_data['total_distance']:>8.3f} m")
            print(f"  Velocity: {left_data['velocity']:>8.3f} m/s")
            print(f"  RPM: {left_data['rpm']:>8.1f}")
            print(f"  Direction: {left_data['direction']:>8}")
            
            print(f"\nRight Encoder:")
            print(f"  Ticks: {right_data['tick_count']:>8}")
            print(f"  Distance: {right_data['total_distance']:>8.3f} m")
            print(f"  Velocity: {right_data['velocity']:>8.3f} m/s")
            print(f"  RPM: {right_data['rpm']:>8.1f}")
            print(f"  Direction: {right_data['direction']:>8}")
            
            # Calculate differential data
            distance_diff = left_data['total_distance'] - right_data['total_distance']
            velocity_diff = left_data['velocity'] - right_data['velocity']
            
            print(f"\nDifferential:")
            print(f"  Distance Diff: {distance_diff:>8.3f} m")
            print(f"  Velocity Diff: {velocity_diff:>8.3f} m/s")
            
            print("="*60)
            
        except Exception as e:
            self.logger.exception("Error printing encoder status")
    
    def run_monitoring_loop(self):
        """Run the main monitoring loop."""
        self.logger.info("Starting encoder monitoring loop")
        self.running = True
        
        last_status_time = time.time()
        status_interval = 2.0  # Print status every 2 seconds
        
        try:
            while self.running:
                current_time = time.time()
                
                # Print status periodically
                if current_time - last_status_time >= status_interval:
                    self.print_encoder_status()
                    last_status_time = current_time
                
                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring interrupted by user")
        except Exception as e:
            self.logger.exception("Error in monitoring loop")
        finally:
            self.cleanup()
    
    def test_encoder_reset(self):
        """Test encoder reset functionality."""
        print("\nTesting encoder reset...")
        
        # Print current values
        left_data = self.left_encoder.read_data()
        right_data = self.right_encoder.read_data()
        
        print(f"Before reset - Left: {left_data['tick_count']} ticks, Right: {right_data['tick_count']} ticks")
        
        # Reset encoders
        self.left_encoder.reset_encoder()
        self.right_encoder.reset_encoder()
        
        # Print values after reset
        left_data = self.left_encoder.read_data()
        right_data = self.right_encoder.read_data()
        
        print(f"After reset - Left: {left_data['tick_count']} ticks, Right: {right_data['tick_count']} ticks")
    
    def test_direction_setting(self):
        """Test setting encoder direction."""
        print("\nTesting direction setting...")
        
        # Test setting different directions
        print("Setting left encoder to reverse direction (-1)")
        self.left_encoder.set_direction(-1)
        
        print("Setting right encoder to forward direction (1)")
        self.right_encoder.set_direction(1)
        
        # Wait a moment for any encoder activity
        time.sleep(1)
        
        # Print current directions
        left_data = self.left_encoder.read_data()
        right_data = self.right_encoder.read_data()
        
        print(f"Left encoder direction: {left_data['direction']}")
        print(f"Right encoder direction: {right_data['direction']}")
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up encoder example")
        
        try:
            if self.left_encoder:
                self.left_encoder.stop()
            
            if self.right_encoder:
                self.right_encoder.stop()
            
            if self.mqtt_client:
                self.mqtt_client.disconnect()
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.exception("Error during cleanup")
    
    def run(self):
        """Run the complete encoder example."""
        print("Orchestrator Encoder Sensor Example")
        print("===================================")
        
        # Setup MQTT
        if not self.setup_mqtt():
            print("Failed to setup MQTT client")
            return False
        
        # Setup encoders
        if not self.setup_encoders():
            print("Failed to setup encoders")
            return False
        
        print("\nEncoders initialized successfully!")
        print("Move the robot wheels to see encoder data...")
        print("Press Ctrl+C to stop monitoring")
        
        # Run tests
        self.test_encoder_reset()
        self.test_direction_setting()
        
        # Start monitoring
        self.run_monitoring_loop()
        
        return True


def main():
    """Main entry point."""
    example = EncoderExample()
    
    try:
        success = example.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()