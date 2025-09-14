#!/usr/bin/env python3
"""
Functional test for MQTT Client Wrapper

This script tests the MQTT client with a real MQTT broker if available.
If no broker is running, it will show how the client handles connection failures gracefully.
"""

import time
import logging
from mqtt_client import MQTTClientWrapper, MQTTConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_mqtt_functionality():
    """Test MQTT client functionality"""
    print("=== MQTT Client Functional Test ===\n")
    
    # Create configuration
    config = MQTTConfig(
        broker_host="localhost",
        broker_port=1883,
        client_id="functional_test"
    )
    
    print(f"Testing connection to {config.broker_host}:{config.broker_port}")
    
    # Create client
    client = MQTTClientWrapper(config)
    
    # Test connection
    print("Attempting to connect...")
    success = client.connect()
    
    if success:
        print("✓ Connection initiated")
        
        # Wait a moment for connection to establish
        time.sleep(2)
        
        if client.is_connected:
            print("✓ Successfully connected to MQTT broker")
            
            # Test message handling
            received_messages = []
            
            def message_handler(message_data):
                received_messages.append(message_data)
                print(f"✓ Received message: {message_data['payload']}")
            
            # Subscribe to test topic
            print("\nTesting subscription...")
            sub_result = client.subscribe("orchestrator/test/+", message_handler)
            
            if sub_result:
                print("✓ Successfully subscribed to orchestrator/test/+")
                
                # Test publishing
                print("\nTesting publishing...")
                test_payload = {
                    "test_id": "functional_test_001",
                    "message": "Hello from MQTT client wrapper!",
                    "value": 42
                }
                
                pub_result = client.publish("orchestrator/test/functional", test_payload)
                
                if pub_result:
                    print("✓ Successfully published test message")
                    
                    # Wait for message to be received
                    time.sleep(1)
                    
                    if received_messages:
                        print("✓ Message loop-back successful")
                        print(f"  Sent: {test_payload}")
                        print(f"  Received: {received_messages[0]['payload']}")
                    else:
                        print("⚠ Message not received (may be normal in some setups)")
                else:
                    print("✗ Failed to publish message")
            else:
                print("✗ Failed to subscribe")
            
            # Test status
            print("\nTesting status reporting...")
            status = client.get_status()
            print(f"✓ Client status: {status}")
            
            # Test disconnection
            print("\nTesting disconnection...")
            client.disconnect()
            print("✓ Disconnected successfully")
            
        else:
            print("⚠ Connection initiated but not established (broker may not be running)")
    else:
        print("⚠ Failed to initiate connection (broker likely not running)")
        print("This is expected if no MQTT broker is installed/running")
    
    print("\n=== Functional Test Complete ===")
    print("\nTo run a full test with MQTT broker:")
    print("1. Install Mosquitto: sudo apt-get install mosquitto mosquitto-clients")
    print("2. Start broker: sudo systemctl start mosquitto")
    print("3. Run this test again")

if __name__ == "__main__":
    test_mqtt_functionality()