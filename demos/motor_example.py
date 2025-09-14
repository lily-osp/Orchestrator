#!/usr/bin/env python3
"""
Example usage of the MotorController class.

This script demonstrates how to use the MotorController with MQTT
communication for the Orchestrator platform.
"""

import time
import json
import signal
import sys
from hal_service.motor_controller import MotorController
from hal_service.mqtt_client import MQTTClientWrapper, MQTTConfig
from hal_service.config import MotorConfig, load_config


class MotorControllerDemo:
    """Demo application for MotorController functionality."""
    
    def __init__(self):
        self.running = True
        self.motors = {}
        self.mqtt_client = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
    
    def setup_mqtt(self):
        """Setup MQTT client connection."""
        try:
            # Load configuration
            config = load_config()
            mqtt_config = MQTTConfig(
                broker_host=config.mqtt.broker_host,
                broker_port=config.mqtt.broker_port,
                client_id="motor_demo"
            )
            
            self.mqtt_client = MQTTClientWrapper(mqtt_config)
            
            # Connect to broker
            if self.mqtt_client.connect():
                print("✓ Connected to MQTT broker")
                return True
            else:
                print("✗ Failed to connect to MQTT broker")
                return False
                
        except Exception as e:
            print(f"✗ Error setting up MQTT: {e}")
            return False
    
    def setup_motors(self):
        """Setup motor controllers from configuration."""
        try:
            config = load_config()
            
            for motor_config in config.motors:
                print(f"Setting up motor: {motor_config.name}")
                
                motor = MotorController(
                    motor_config.name,
                    self.mqtt_client,
                    motor_config
                )
                
                if motor.initialize():
                    self.motors[motor_config.name] = motor
                    print(f"✓ Motor {motor_config.name} initialized successfully")
                else:
                    print(f"✗ Failed to initialize motor {motor_config.name}")
            
            return len(self.motors) > 0
            
        except Exception as e:
            print(f"✗ Error setting up motors: {e}")
            return False
    
    def send_test_commands(self):
        """Send test commands to motors."""
        if not self.motors:
            print("No motors available for testing")
            return
        
        print("\nSending test commands...")
        
        # Test commands for each motor
        test_commands = [
            {
                "action": "move_forward",
                "parameters": {"distance": 0.5, "speed": 0.3},
                "command_id": "test_001"
            },
            {
                "action": "stop",
                "command_id": "test_002"
            },
            {
                "action": "move_backward", 
                "parameters": {"distance": 0.3, "speed": 0.2},
                "command_id": "test_003"
            },
            {
                "action": "rotate_left",
                "parameters": {"angle": 45.0, "speed": 0.2},
                "command_id": "test_004"
            }
        ]
        
        for motor_name, motor in self.motors.items():
            print(f"\nTesting motor: {motor_name}")
            
            for i, command in enumerate(test_commands):
                print(f"  Command {i+1}: {command['action']}")
                
                # Execute command directly
                success = motor.execute_command(command)
                print(f"    Result: {'✓ Success' if success else '✗ Failed'}")
                
                # Wait between commands
                time.sleep(2)
                
                # Show motor status
                status = motor.get_status()
                print(f"    Status: {status['status']}, Moving: {status['is_moving']}")
    
    def monitor_telemetry(self, duration=10):
        """Monitor motor telemetry for specified duration."""
        print(f"\nMonitoring telemetry for {duration} seconds...")
        
        def telemetry_callback(message_data):
            """Callback for telemetry messages."""
            payload = message_data['payload']
            device_id = payload.get('device_id', 'unknown')
            data = payload.get('data', {})
            
            print(f"[{device_id}] Speed: {data.get('current_speed', 0):.2f}, "
                  f"Distance: {data.get('distance_traveled', 0):.3f}m, "
                  f"Moving: {data.get('is_moving', False)}")
        
        # Subscribe to telemetry
        self.mqtt_client.subscribe("orchestrator/data/+", telemetry_callback)
        
        # Monitor for specified duration
        start_time = time.time()
        while time.time() - start_time < duration and self.running:
            time.sleep(0.5)
        
        # Unsubscribe
        self.mqtt_client.unsubscribe("orchestrator/data/+")
    
    def run_demo(self):
        """Run the complete motor controller demo."""
        print("Motor Controller Demo")
        print("=" * 50)
        
        # Setup MQTT
        if not self.setup_mqtt():
            return 1
        
        # Setup motors
        if not self.setup_motors():
            print("No motors could be initialized")
            return 1
        
        print(f"\nInitialized {len(self.motors)} motor(s)")
        
        try:
            # Send test commands
            self.send_test_commands()
            
            # Monitor telemetry
            self.monitor_telemetry(10)
            
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
        
        finally:
            self.cleanup()
        
        print("\nDemo completed successfully!")
        return 0
    
    def cleanup(self):
        """Clean up resources."""
        print("\nCleaning up...")
        
        # Stop all motors
        for motor_name, motor in self.motors.items():
            print(f"Stopping motor: {motor_name}")
            motor.stop()
        
        # Disconnect MQTT
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            print("Disconnected from MQTT broker")


def main():
    """Main function."""
    demo = MotorControllerDemo()
    return demo.run_demo()


if __name__ == "__main__":
    sys.exit(main())