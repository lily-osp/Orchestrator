"""
MQTT Client Wrapper for Orchestrator Platform

This module provides a robust MQTT client wrapper with automatic reconnection,
JSON serialization/deserialization, and topic validation capabilities.

Requirements covered: 2.1, 2.3, 7.1, 7.2
"""

import json
import logging
import time
import threading
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import paho.mqtt.client as mqtt
import re


@dataclass
class MQTTConfig:
    """Configuration for MQTT client"""
    broker_host: str = "localhost"
    broker_port: int = 1883
    keepalive: int = 60
    client_id: str = "orchestrator_hal"
    username: Optional[str] = None
    password: Optional[str] = None
    max_reconnect_delay: int = 300  # 5 minutes
    base_reconnect_delay: int = 1   # 1 second


class TopicValidator:
    """Validates MQTT topic names according to orchestrator conventions"""
    
    # Topic patterns for orchestrator platform
    VALID_PATTERNS = {
        'command': r'^orchestrator/cmd/[a-zA-Z0-9_]+$',
        'data': r'^orchestrator/data/[a-zA-Z0-9_]+$',
        'status': r'^orchestrator/status/[a-zA-Z0-9_]+$'
    }
    
    @classmethod
    def validate_topic(cls, topic: str) -> bool:
        """Validate if topic follows orchestrator naming conventions"""
        for pattern in cls.VALID_PATTERNS.values():
            if re.match(pattern, topic):
                return True
        return False
    
    @classmethod
    def get_topic_type(cls, topic: str) -> Optional[str]:
        """Get the type of topic (command, data, status)"""
        for topic_type, pattern in cls.VALID_PATTERNS.items():
            if re.match(pattern, topic):
                return topic_type
        return None


class MQTTClientWrapper:
    """
    Robust MQTT client wrapper with automatic reconnection and JSON handling
    
    Features:
    - Automatic reconnection with exponential backoff
    - JSON serialization/deserialization
    - Topic validation
    - Message callbacks with error handling
    - Connection status monitoring
    """
    
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self._connected = False
        self._reconnect_delay = config.base_reconnect_delay
        self._reconnect_thread = None
        self._stop_reconnect = threading.Event()
        
        # Message callbacks
        self._message_callbacks: Dict[str, Callable] = {}
        self._connection_callbacks: Dict[str, Callable] = {}
        
        # Initialize MQTT client (using callback API version 2)
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=config.client_id)
        self._setup_client()
    
    def _setup_client(self):
        """Setup MQTT client with callbacks"""
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        
        # Set credentials if provided
        if self.config.username and self.config.password:
            self._client.username_pw_set(
                self.config.username, 
                self.config.password
            )
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful connection"""
        if rc == 0:
            self._connected = True
            self._reconnect_delay = self.config.base_reconnect_delay
            self.logger.info(f"Connected to MQTT broker at {self.config.broker_host}:{self.config.broker_port}")
            
            # Notify connection callbacks
            for callback in self._connection_callbacks.values():
                try:
                    callback(True)
                except Exception as e:
                    self.logger.error(f"Error in connection callback: {e}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for disconnection"""
        self._connected = False
        self.logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")
        
        # Notify connection callbacks
        for callback in self._connection_callbacks.values():
            try:
                callback(False)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {e}")
        
        # Start reconnection if not intentional disconnect
        if rc != 0:
            self._start_reconnect()
    
    def _on_message(self, client, userdata, msg):
        """Callback for received messages"""
        try:
            topic = msg.topic
            
            # Validate topic
            if not TopicValidator.validate_topic(topic):
                self.logger.warning(f"Received message on invalid topic: {topic}")
                return
            
            # Deserialize JSON payload
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode JSON message on topic {topic}: {e}")
                return
            
            # Add metadata
            message_data = {
                'topic': topic,
                'payload': payload,
                'qos': msg.qos,
                'retain': msg.retain,
                'received_at': datetime.now().isoformat()
            }
            
            # Call registered callbacks
            for pattern, callback in self._message_callbacks.items():
                if self._topic_matches_pattern(topic, pattern):
                    try:
                        callback(message_data)
                    except Exception as e:
                        self.logger.error(f"Error in message callback for {topic}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if topic matches subscription pattern"""
        # Convert MQTT wildcards to regex
        regex_pattern = pattern.replace('+', '[^/]+').replace('#', '.*')
        return re.match(f"^{regex_pattern}$", topic) is not None
    
    def _start_reconnect(self):
        """Start reconnection thread with exponential backoff"""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        
        self._stop_reconnect.clear()
        self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()
    
    def _reconnect_loop(self):
        """Reconnection loop with exponential backoff"""
        while not self._stop_reconnect.is_set() and not self._connected:
            self.logger.info(f"Attempting to reconnect in {self._reconnect_delay} seconds...")
            
            if self._stop_reconnect.wait(self._reconnect_delay):
                break
            
            try:
                self._client.connect(
                    self.config.broker_host,
                    self.config.broker_port,
                    self.config.keepalive
                )
                self._client.loop_start()
                break
            except Exception as e:
                self.logger.error(f"Reconnection failed: {e}")
                
                # Exponential backoff with jitter
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self.config.max_reconnect_delay
                )
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self._client.connect(
                self.config.broker_host,
                self.config.broker_port,
                self.config.keepalive
            )
            self._client.loop_start()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self._stop_reconnect.set()
        if self._reconnect_thread:
            self._reconnect_thread.join(timeout=5)
        
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 0, retain: bool = False) -> bool:
        """
        Publish a message to MQTT broker
        
        Args:
            topic: MQTT topic to publish to
            payload: Dictionary payload to serialize as JSON
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether to retain the message
            
        Returns:
            True if message was queued for sending, False otherwise
        """
        if not self._connected:
            self.logger.error("Cannot publish: not connected to MQTT broker")
            return False
        
        # Validate topic
        if not TopicValidator.validate_topic(topic):
            self.logger.error(f"Invalid topic format: {topic}")
            return False
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in payload:
                payload['timestamp'] = datetime.now().isoformat()
            
            # Serialize to JSON
            json_payload = json.dumps(payload, default=str)
            
            # Publish message
            result = self._client.publish(topic, json_payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published message to {topic}")
                return True
            else:
                self.logger.error(f"Failed to publish message to {topic}: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing message to {topic}: {e}")
            return False
    
    def subscribe(self, topic_pattern: str, callback: Callable, qos: int = 0) -> bool:
        """
        Subscribe to MQTT topic with callback
        
        Args:
            topic_pattern: MQTT topic pattern (supports + and # wildcards)
            callback: Function to call when message received
            qos: Quality of Service level
            
        Returns:
            True if subscription successful, False otherwise
        """
        if not self._connected:
            self.logger.error("Cannot subscribe: not connected to MQTT broker")
            return False
        
        try:
            result = self._client.subscribe(topic_pattern, qos=qos)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self._message_callbacks[topic_pattern] = callback
                self.logger.info(f"Subscribed to {topic_pattern}")
                return True
            else:
                self.logger.error(f"Failed to subscribe to {topic_pattern}: {result[0]}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error subscribing to {topic_pattern}: {e}")
            return False
    
    def unsubscribe(self, topic_pattern: str) -> bool:
        """Unsubscribe from MQTT topic"""
        if not self._connected:
            self.logger.error("Cannot unsubscribe: not connected to MQTT broker")
            return False
        
        try:
            result = self._client.unsubscribe(topic_pattern)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self._message_callbacks.pop(topic_pattern, None)
                self.logger.info(f"Unsubscribed from {topic_pattern}")
                return True
            else:
                self.logger.error(f"Failed to unsubscribe from {topic_pattern}: {result[0]}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error unsubscribing from {topic_pattern}: {e}")
            return False
    
    def add_connection_callback(self, name: str, callback: Callable):
        """Add callback for connection status changes"""
        self._connection_callbacks[name] = callback
    
    def remove_connection_callback(self, name: str):
        """Remove connection status callback"""
        self._connection_callbacks.pop(name, None)
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to broker"""
        return self._connected
    
    def get_status(self) -> Dict[str, Any]:
        """Get current client status"""
        return {
            'connected': self._connected,
            'broker_host': self.config.broker_host,
            'broker_port': self.config.broker_port,
            'client_id': self.config.client_id,
            'subscriptions': list(self._message_callbacks.keys()),
            'reconnect_delay': self._reconnect_delay
        }