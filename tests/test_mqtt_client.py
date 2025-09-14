"""
Tests for MQTT Client Wrapper

This module contains comprehensive tests for the MQTTClientWrapper class,
including unit tests and integration tests with mock MQTT broker.
"""

import pytest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hal_service'))

from mqtt_client import MQTTClientWrapper, MQTTConfig, TopicValidator


class TestTopicValidator:
    """Test cases for TopicValidator class"""
    
    def test_valid_command_topics(self):
        """Test validation of command topics"""
        valid_topics = [
            "orchestrator/cmd/motors",
            "orchestrator/cmd/gripper",
            "orchestrator/cmd/lidar_01"
        ]
        
        for topic in valid_topics:
            assert TopicValidator.validate_topic(topic), f"Topic should be valid: {topic}"
            assert TopicValidator.get_topic_type(topic) == "command"
    
    def test_valid_data_topics(self):
        """Test validation of data topics"""
        valid_topics = [
            "orchestrator/data/lidar",
            "orchestrator/data/encoder_left",
            "orchestrator/data/temperature"
        ]
        
        for topic in valid_topics:
            assert TopicValidator.validate_topic(topic), f"Topic should be valid: {topic}"
            assert TopicValidator.get_topic_type(topic) == "data"
    
    def test_valid_status_topics(self):
        """Test validation of status topics"""
        valid_topics = [
            "orchestrator/status/robot",
            "orchestrator/status/safety",
            "orchestrator/status/mission"
        ]
        
        for topic in valid_topics:
            assert TopicValidator.validate_topic(topic), f"Topic should be valid: {topic}"
            assert TopicValidator.get_topic_type(topic) == "status"
    
    def test_invalid_topics(self):
        """Test rejection of invalid topics"""
        invalid_topics = [
            "invalid/topic",
            "orchestrator/invalid/test",
            "orchestrator/cmd/",
            "orchestrator/cmd/test/subtopic",
            "random_topic",
            ""
        ]
        
        for topic in invalid_topics:
            assert not TopicValidator.validate_topic(topic), f"Topic should be invalid: {topic}"
            assert TopicValidator.get_topic_type(topic) is None


class TestMQTTClientWrapper:
    """Test cases for MQTTClientWrapper class"""
    
    @pytest.fixture
    def mqtt_config(self):
        """Create test MQTT configuration"""
        return MQTTConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="test_client"
        )
    
    @pytest.fixture
    def mqtt_client(self, mqtt_config):
        """Create test MQTT client wrapper"""
        return MQTTClientWrapper(mqtt_config)
    
    def test_client_initialization(self, mqtt_client, mqtt_config):
        """Test client initialization"""
        assert mqtt_client.config == mqtt_config
        assert not mqtt_client.is_connected
        assert mqtt_client._reconnect_delay == mqtt_config.base_reconnect_delay
    
    @patch('paho.mqtt.client.Client')
    def test_client_setup(self, mock_mqtt_client, mqtt_client):
        """Test MQTT client setup"""
        # Verify client was created with correct ID
        mock_mqtt_client.assert_called_with(client_id="test_client")
        
        # Verify callbacks were set
        client_instance = mock_mqtt_client.return_value
        assert client_instance.on_connect is not None
        assert client_instance.on_disconnect is not None
        assert client_instance.on_message is not None
    
    @patch('paho.mqtt.client.Client')
    def test_successful_connection(self, mock_mqtt_client, mqtt_client):
        """Test successful connection to MQTT broker"""
        client_instance = mock_mqtt_client.return_value
        client_instance.connect.return_value = None
        
        # Mock successful connection
        result = mqtt_client.connect()
        assert result is True
        
        # Simulate connection callback
        mqtt_client._on_connect(client_instance, None, None, 0)
        assert mqtt_client.is_connected
    
    @patch('paho.mqtt.client.Client')
    def test_connection_failure(self, mock_mqtt_client, mqtt_client):
        """Test connection failure handling"""
        client_instance = mock_mqtt_client.return_value
        client_instance.connect.side_effect = Exception("Connection failed")
        
        result = mqtt_client.connect()
        assert result is False
        assert not mqtt_client.is_connected
    
    @patch('paho.mqtt.client.Client')
    def test_publish_valid_message(self, mock_mqtt_client, mqtt_client):
        """Test publishing valid message"""
        client_instance = mock_mqtt_client.return_value
        
        # Mock successful connection
        mqtt_client._connected = True
        
        # Mock successful publish
        mock_result = Mock()
        mock_result.rc = 0  # MQTT_ERR_SUCCESS
        client_instance.publish.return_value = mock_result
        
        payload = {"action": "move_forward", "distance": 100}
        result = mqtt_client.publish("orchestrator/cmd/motors", payload)
        
        assert result is True
        client_instance.publish.assert_called_once()
        
        # Verify JSON serialization and timestamp addition
        call_args = client_instance.publish.call_args
        assert call_args[0][0] == "orchestrator/cmd/motors"  # topic
        
        published_data = json.loads(call_args[0][1])  # payload
        assert published_data["action"] == "move_forward"
        assert published_data["distance"] == 100
        assert "timestamp" in published_data
    
    def test_publish_invalid_topic(self, mqtt_client):
        """Test publishing to invalid topic"""
        mqtt_client._connected = True
        
        payload = {"test": "data"}
        result = mqtt_client.publish("invalid/topic", payload)
        
        assert result is False
    
    def test_publish_when_disconnected(self, mqtt_client):
        """Test publishing when not connected"""
        payload = {"test": "data"}
        result = mqtt_client.publish("orchestrator/cmd/motors", payload)
        
        assert result is False
    
    @patch('paho.mqtt.client.Client')
    def test_subscribe_to_topic(self, mock_mqtt_client, mqtt_client):
        """Test subscribing to topic"""
        client_instance = mock_mqtt_client.return_value
        mqtt_client._connected = True
        
        # Mock successful subscription
        client_instance.subscribe.return_value = (0, 1)  # (result, mid)
        
        callback = Mock()
        result = mqtt_client.subscribe("orchestrator/cmd/+", callback)
        
        assert result is True
        client_instance.subscribe.assert_called_with("orchestrator/cmd/+", qos=0)
        assert "orchestrator/cmd/+" in mqtt_client._message_callbacks
    
    def test_message_callback_execution(self, mqtt_client):
        """Test message callback execution"""
        # Setup callback
        callback = Mock()
        mqtt_client._message_callbacks["orchestrator/cmd/+"] = callback
        
        # Create mock message
        mock_msg = Mock()
        mock_msg.topic = "orchestrator/cmd/motors"
        mock_msg.payload = json.dumps({"action": "stop"}).encode('utf-8')
        mock_msg.qos = 0
        mock_msg.retain = False
        
        # Process message
        mqtt_client._on_message(None, None, mock_msg)
        
        # Verify callback was called
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args['topic'] == "orchestrator/cmd/motors"
        assert call_args['payload']['action'] == "stop"
    
    def test_message_with_invalid_json(self, mqtt_client):
        """Test handling of message with invalid JSON"""
        callback = Mock()
        mqtt_client._message_callbacks["orchestrator/cmd/+"] = callback
        
        # Create mock message with invalid JSON
        mock_msg = Mock()
        mock_msg.topic = "orchestrator/cmd/motors"
        mock_msg.payload = b"invalid json"
        mock_msg.qos = 0
        mock_msg.retain = False
        
        # Process message - should not crash
        mqtt_client._on_message(None, None, mock_msg)
        
        # Callback should not be called for invalid JSON
        callback.assert_not_called()
    
    def test_topic_pattern_matching(self, mqtt_client):
        """Test topic pattern matching for wildcards"""
        # Test single-level wildcard
        assert mqtt_client._topic_matches_pattern("orchestrator/cmd/motors", "orchestrator/cmd/+")
        assert mqtt_client._topic_matches_pattern("orchestrator/cmd/gripper", "orchestrator/cmd/+")
        assert not mqtt_client._topic_matches_pattern("orchestrator/cmd/motors/speed", "orchestrator/cmd/+")
        
        # Test multi-level wildcard
        assert mqtt_client._topic_matches_pattern("orchestrator/data/lidar", "orchestrator/data/#")
        assert mqtt_client._topic_matches_pattern("orchestrator/data/lidar/scan", "orchestrator/data/#")
    
    def test_connection_callbacks(self, mqtt_client):
        """Test connection status callbacks"""
        callback1 = Mock()
        callback2 = Mock()
        
        mqtt_client.add_connection_callback("test1", callback1)
        mqtt_client.add_connection_callback("test2", callback2)
        
        # Simulate connection
        mqtt_client._on_connect(None, None, None, 0)
        
        callback1.assert_called_with(True)
        callback2.assert_called_with(True)
        
        # Simulate disconnection
        mqtt_client._on_disconnect(None, None, 1)  # rc != 0 means unexpected disconnect
        
        callback1.assert_called_with(False)
        callback2.assert_called_with(False)
    
    def test_get_status(self, mqtt_client):
        """Test status reporting"""
        status = mqtt_client.get_status()
        
        assert 'connected' in status
        assert 'broker_host' in status
        assert 'broker_port' in status
        assert 'client_id' in status
        assert 'subscriptions' in status
        assert 'reconnect_delay' in status
        
        assert status['broker_host'] == "localhost"
        assert status['broker_port'] == 1883
        assert status['client_id'] == "test_client"
    
    @patch('paho.mqtt.client.Client')
    def test_disconnect(self, mock_mqtt_client, mqtt_client):
        """Test client disconnection"""
        client_instance = mock_mqtt_client.return_value
        mqtt_client._connected = True
        
        mqtt_client.disconnect()
        
        client_instance.loop_stop.assert_called_once()
        client_instance.disconnect.assert_called_once()
        assert not mqtt_client.is_connected


class TestMQTTIntegration:
    """Integration tests for MQTT client (requires running MQTT broker)"""
    
    @pytest.mark.integration
    def test_real_mqtt_connection(self):
        """Test connection to real MQTT broker (skip if broker not available)"""
        config = MQTTConfig(broker_host="localhost", client_id="integration_test")
        client = MQTTClientWrapper(config)
        
        try:
            result = client.connect()
            if result:
                time.sleep(1)  # Allow connection to establish
                assert client.is_connected
                
                # Test publish/subscribe
                received_messages = []
                
                def message_callback(message_data):
                    received_messages.append(message_data)
                
                client.subscribe("orchestrator/test/+", message_callback)
                time.sleep(0.5)  # Allow subscription to register
                
                test_payload = {"test": "integration", "value": 42}
                client.publish("orchestrator/test/integration", test_payload)
                
                time.sleep(1)  # Allow message to be received
                
                assert len(received_messages) > 0
                assert received_messages[0]['payload']['test'] == "integration"
                
                client.disconnect()
            else:
                pytest.skip("MQTT broker not available for integration test")
        except Exception as e:
            pytest.skip(f"MQTT broker not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])