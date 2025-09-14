#!/usr/bin/env python3
"""
Example usage of the MQTT Client Wrapper

This script demonstrates how to use the MQTTClientWrapper for the Orchestrator platform.
"""

import logging
import time
from mqtt_client import MQTTClientWrapper, MQTTConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def on_command_received(message_data):
    """Callback for command messages"""
    print(f"Command received: {message_data['payload']}")

def on_connection_changed(connected):
    """Callback for connection status changes"""
    status = "connected" if connected else "disconnected"
    print(f"MQTT broker {status}")

def main():
    # Create MQTT configuration
    config = MQTTConfig(
        broker_host="localhost",
        broker_port=1883,
        client_id="orchestrator_example"
    )
    
    # Create MQTT client
    mqtt_client = MQTTClientWrapper(config)
    
    # Add connection callback
    mqtt_client.add_connection_callback("main", on_connection_changed)
    
    # Connect to broker
    print("Connecting to MQTT broker...")
    if mqtt_client.connect():
        # Wait for connection
        time.sleep(2)
        
        if mqtt_client.is_connected:
            print("Connected successfully!")
            
            # Subscribe to command topics
            mqtt_client.subscribe("orchestrator/cmd/+", on_command_received)
            
            # Publish some test data
            test_data = {
                "device_id": "test_sensor",
                "data": {
                    "temperature": 25.5,
                    "humidity": 60.2
                }
            }
            
            mqtt_client.publish("orchestrator/data/test_sensor", test_data)
            
            # Publish status update
            status_data = {
                "subsystem": "robot",
                "status": "active",
                "position": {"x": 0.0, "y": 0.0, "heading": 0.0}
            }
            
            mqtt_client.publish("orchestrator/status/robot", status_data)
            
            print("Published test messages. Waiting for commands...")
            print("You can test by publishing to: orchestrator/cmd/motors")
            print("Example: mosquitto_pub -t 'orchestrator/cmd/motors' -m '{\"action\":\"move_forward\",\"distance\":100}'")
            
            # Keep running for demonstration
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
        else:
            print("Failed to connect to MQTT broker")
    
    # Cleanup
    mqtt_client.disconnect()
    print("Disconnected from MQTT broker")

if __name__ == "__main__":
    main()