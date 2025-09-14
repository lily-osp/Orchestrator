#!/usr/bin/env python3
"""
Example usage of the Configuration Service.

This script demonstrates how to use the configuration service to load
and validate device configurations for the Orchestrator platform.
"""

import sys
from pathlib import Path
from hal_service.config import ConfigurationService, load_config


def main():
    """Main example function."""
    print("Orchestrator Configuration Service Example")
    print("=" * 50)
    
    # Method 1: Using the convenience function
    print("\n1. Loading configuration using convenience function:")
    try:
        config = load_config("config.yaml")
        print(f"✓ Successfully loaded configuration")
        print(f"  - System log level: {config.system.log_level}")
        print(f"  - MQTT broker: {config.mqtt.broker_host}:{config.mqtt.broker_port}")
        print(f"  - Motors configured: {len(config.motors)}")
        print(f"  - Sensors configured: {len(config.sensors)}")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return 1
    
    # Method 2: Using the ConfigurationService directly
    print("\n2. Using ConfigurationService directly:")
    service = ConfigurationService("config.yaml")
    
    # Get specific motor configuration
    motor_config = service.get_motor_config("left_motor")
    if motor_config:
        print(f"✓ Found left_motor configuration:")
        print(f"  - Type: {motor_config.type}")
        print(f"  - GPIO pins: {motor_config.gpio_pins}")
        print(f"  - Max speed: {motor_config.max_speed}")
    else:
        print("✗ Left motor configuration not found")
    
    # Get specific sensor configuration
    sensor_config = service.get_sensor_config("lidar_01")
    if sensor_config:
        print(f"✓ Found lidar_01 configuration:")
        print(f"  - Type: {sensor_config.type}")
        print(f"  - Publish rate: {sensor_config.publish_rate} Hz")
        if hasattr(sensor_config.interface, 'port'):
            print(f"  - Port: {sensor_config.interface.port}")
            print(f"  - Baudrate: {sensor_config.interface.baudrate}")
    else:
        print("✗ LiDAR sensor configuration not found")
    
    # Method 3: Validate configuration file
    print("\n3. Validating configuration file:")
    is_valid = service.validate_config_file("config.yaml")
    if is_valid:
        print("✓ Configuration file is valid")
    else:
        print("✗ Configuration file validation failed")
    
    # Method 4: Create a new default configuration
    print("\n4. Creating a new default configuration:")
    try:
        new_config_path = service.create_default_config("example_config.yaml")
        print(f"✓ Created default configuration at: {new_config_path}")
        
        # Validate the newly created config
        if service.validate_config_file(new_config_path):
            print("✓ New configuration file is valid")
        else:
            print("✗ New configuration file validation failed")
            
    except Exception as e:
        print(f"✗ Failed to create default config: {e}")
    
    print("\n" + "=" * 50)
    print("Configuration service example completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())