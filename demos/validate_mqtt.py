#!/usr/bin/env python3
"""
Validation script for MQTT Client Wrapper

This script validates the core functionality of the MQTT client wrapper
without requiring an actual MQTT broker connection.
"""

import sys
import json
from datetime import datetime

# Import our MQTT client components
try:
    from mqtt_client import MQTTClientWrapper, MQTTConfig, TopicValidator
    print("✓ Successfully imported MQTT client components")
except ImportError as e:
    print(f"✗ Failed to import MQTT client: {e}")
    sys.exit(1)

def test_topic_validator():
    """Test the TopicValidator functionality"""
    print("\n=== Testing TopicValidator ===")
    
    # Test valid topics
    valid_topics = [
        ("orchestrator/cmd/motors", "command"),
        ("orchestrator/data/lidar", "data"),
        ("orchestrator/status/robot", "status"),
        ("orchestrator/cmd/gripper_01", "command"),
        ("orchestrator/data/encoder_left", "data")
    ]
    
    for topic, expected_type in valid_topics:
        is_valid = TopicValidator.validate_topic(topic)
        topic_type = TopicValidator.get_topic_type(topic)
        
        if is_valid and topic_type == expected_type:
            print(f"✓ {topic} -> {topic_type}")
        else:
            print(f"✗ {topic} -> Expected {expected_type}, got {topic_type}")
    
    # Test invalid topics
    invalid_topics = [
        "invalid/topic",
        "orchestrator/invalid/test",
        "orchestrator/cmd/",
        "random_topic"
    ]
    
    for topic in invalid_topics:
        is_valid = TopicValidator.validate_topic(topic)
        if not is_valid:
            print(f"✓ {topic} -> correctly rejected")
        else:
            print(f"✗ {topic} -> should have been rejected")

def test_mqtt_config():
    """Test MQTT configuration"""
    print("\n=== Testing MQTTConfig ===")
    
    # Test default configuration
    config = MQTTConfig()
    print(f"✓ Default config: {config.broker_host}:{config.broker_port}")
    
    # Test custom configuration
    custom_config = MQTTConfig(
        broker_host="192.168.1.100",
        broker_port=8883,
        client_id="test_client"
    )
    print(f"✓ Custom config: {custom_config.broker_host}:{custom_config.broker_port}")

def test_message_formatting():
    """Test message formatting and JSON handling"""
    print("\n=== Testing Message Formatting ===")
    
    # Test payload with timestamp addition
    test_payload = {
        "action": "move_forward",
        "distance": 100,
        "speed": 0.5
    }
    
    # Add timestamp (simulating what the client does)
    test_payload["timestamp"] = datetime.now().isoformat()
    
    # Test JSON serialization
    try:
        json_str = json.dumps(test_payload, default=str)
        parsed_back = json.loads(json_str)
        
        print(f"✓ JSON serialization successful")
        print(f"  Original keys: {list(test_payload.keys())}")
        print(f"  Parsed keys: {list(parsed_back.keys())}")
        
        if parsed_back["action"] == "move_forward":
            print("✓ Data integrity maintained")
        else:
            print("✗ Data integrity lost")
            
    except Exception as e:
        print(f"✗ JSON handling failed: {e}")

def test_client_initialization():
    """Test MQTT client initialization"""
    print("\n=== Testing Client Initialization ===")
    
    try:
        config = MQTTConfig(client_id="validation_test")
        client = MQTTClientWrapper(config)
        
        print("✓ Client initialized successfully")
        print(f"  Client ID: {client.config.client_id}")
        print(f"  Connected: {client.is_connected}")
        
        # Test status method
        status = client.get_status()
        required_keys = ['connected', 'broker_host', 'broker_port', 'client_id']
        
        for key in required_keys:
            if key in status:
                print(f"✓ Status contains {key}: {status[key]}")
            else:
                print(f"✗ Status missing {key}")
        
        # Test topic pattern matching
        test_cases = [
            ("orchestrator/cmd/motors", "orchestrator/cmd/+", True),
            ("orchestrator/cmd/gripper", "orchestrator/cmd/+", True),
            ("orchestrator/data/lidar/scan", "orchestrator/data/#", True),
            ("orchestrator/cmd/motors/speed", "orchestrator/cmd/+", False)
        ]
        
        print("\n--- Testing Topic Pattern Matching ---")
        for topic, pattern, expected in test_cases:
            result = client._topic_matches_pattern(topic, pattern)
            if result == expected:
                print(f"✓ {topic} vs {pattern} -> {result}")
            else:
                print(f"✗ {topic} vs {pattern} -> Expected {expected}, got {result}")
        
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")

def main():
    """Run all validation tests"""
    print("MQTT Client Wrapper Validation")
    print("=" * 40)
    
    test_topic_validator()
    test_mqtt_config()
    test_message_formatting()
    test_client_initialization()
    
    print("\n" + "=" * 40)
    print("Validation complete!")
    print("\nNote: This validation tests core functionality without requiring")
    print("an actual MQTT broker. For full integration testing, ensure")
    print("Mosquitto MQTT broker is running and use the example script.")

if __name__ == "__main__":
    main()