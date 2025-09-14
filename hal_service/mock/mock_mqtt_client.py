"""
Mock MQTT Client for HAL Testing

Provides a mock MQTT client that simulates broker communication without
requiring an actual MQTT broker. Useful for testing and development.
"""

import json
import time
import threading
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

# Import MQTTConfig from parent config module
from ..config import MQTTConfig


@dataclass
class MockMessage:
    """Mock MQTT message structure"""
    topic: str
    payload: bytes
    qos: int = 0
    retain: bool = False
    timestamp: float = field(default_factory=time.time)


class MockMQTTClient:
    """
    Mock MQTT client that simulates broker behavior for testing.
    
    Features:
    - In-memory message routing between publishers and subscribers
    - Topic pattern matching with wildcards
    - Message history for testing verification
    - Configurable delays and failures for testing edge cases
    """
    
    def __init__(self, client_id: str = "mock_client"):
        self.client_id = client_id
        self.connected = False
        
        # Message storage and routing
        self.message_history: List[MockMessage] = []
        self.subscribers: Dict[str, Callable] = {}
        self.retained_messages: Dict[str, MockMessage] = {}
        
        # Simulation parameters
        self.connection_delay = 0.0  # Seconds
        self.publish_delay = 0.0     # Seconds
        self.failure_rate = 0.0      # 0.0 to 1.0
        self.max_history_size = 1000
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'messages_published': 0,
            'messages_received': 0,
            'connections': 0,
            'disconnections': 0,
            'subscription_count': 0
        }
    
    def connect(self, host: str = "localhost", port: int = 1883, keepalive: int = 60) -> bool:
        """Simulate connection to MQTT broker"""
        if self.connection_delay > 0:
            time.sleep(self.connection_delay)
        
        # Simulate connection failure
        if self._should_fail():
            return False
        
        self.connected = True
        self.stats['connections'] += 1
        
        # Deliver retained messages to existing subscribers
        self._deliver_retained_messages()
        
        return True
    
    def disconnect(self):
        """Simulate disconnection from MQTT broker"""
        self.connected = False
        self.stats['disconnections'] += 1
    
    def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """Simulate publishing a message"""
        if not self.connected:
            return False
        
        if self.publish_delay > 0:
            time.sleep(self.publish_delay)
        
        # Simulate publish failure
        if self._should_fail():
            return False
        
        # Convert payload to bytes if needed
        if isinstance(payload, dict):
            payload_bytes = json.dumps(payload).encode('utf-8')
        elif isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        else:
            payload_bytes = payload
        
        message = MockMessage(
            topic=topic,
            payload=payload_bytes,
            qos=qos,
            retain=retain
        )
        
        with self._lock:
            # Store message in history
            self.message_history.append(message)
            if len(self.message_history) > self.max_history_size:
                self.message_history = self.message_history[-self.max_history_size//2:]
            
            # Store retained message
            if retain:
                self.retained_messages[topic] = message
            
            # Deliver to subscribers
            self._deliver_message(message)
            
            self.stats['messages_published'] += 1
        
        return True
    
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """Simulate subscribing to a topic"""
        if not self.connected:
            return False
        
        # Simulate subscription failure
        if self._should_fail():
            return False
        
        with self._lock:
            # Store subscription (simplified - no callback registration here)
            self.stats['subscription_count'] += 1
        
        return True
    
    def message_callback_add(self, topic: str, callback: Callable):
        """Add callback for specific topic"""
        with self._lock:
            self.subscribers[topic] = callback
        
        # Deliver any retained messages for this topic
        self._deliver_retained_for_topic(topic, callback)
    
    def message_callback_remove(self, topic: str):
        """Remove callback for specific topic"""
        with self._lock:
            self.subscribers.pop(topic, None)
    
    def unsubscribe(self, topic: str) -> bool:
        """Simulate unsubscribing from a topic"""
        if not self.connected:
            return False
        
        with self._lock:
            self.subscribers.pop(topic, None)
            self.stats['subscription_count'] = max(0, self.stats['subscription_count'] - 1)
        
        return True
    
    def _deliver_message(self, message: MockMessage):
        """Deliver message to matching subscribers"""
        for topic_pattern, callback in self.subscribers.items():
            if self._topic_matches(message.topic, topic_pattern):
                try:
                    # Create mock message object similar to paho-mqtt
                    mock_msg = type('MockMsg', (), {
                        'topic': message.topic,
                        'payload': message.payload,
                        'qos': message.qos,
                        'retain': message.retain
                    })()
                    
                    callback(self, None, mock_msg)
                    self.stats['messages_received'] += 1
                    
                except Exception as e:
                    print(f"Error in message callback for {topic_pattern}: {e}")
    
    def _deliver_retained_messages(self):
        """Deliver retained messages to all subscribers"""
        for topic_pattern, callback in self.subscribers.items():
            self._deliver_retained_for_topic(topic_pattern, callback)
    
    def _deliver_retained_for_topic(self, topic_pattern: str, callback: Callable):
        """Deliver retained messages matching a topic pattern"""
        for topic, message in self.retained_messages.items():
            if self._topic_matches(topic, topic_pattern):
                try:
                    mock_msg = type('MockMsg', (), {
                        'topic': message.topic,
                        'payload': message.payload,
                        'qos': message.qos,
                        'retain': message.retain
                    })()
                    
                    callback(self, None, mock_msg)
                    
                except Exception as e:
                    print(f"Error delivering retained message: {e}")
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches subscription pattern with wildcards"""
        # Handle exact match
        if topic == pattern:
            return True
        
        # Handle single-level wildcard (+)
        if '+' in pattern:
            topic_parts = topic.split('/')
            pattern_parts = pattern.split('/')
            
            if len(topic_parts) != len(pattern_parts):
                return False
            
            for t_part, p_part in zip(topic_parts, pattern_parts):
                if p_part != '+' and p_part != t_part:
                    return False
            
            return True
        
        # Handle multi-level wildcard (#)
        if pattern.endswith('#'):
            prefix = pattern[:-1]  # Remove the '#'
            return topic.startswith(prefix)
        
        return False
    
    def _should_fail(self) -> bool:
        """Determine if operation should fail based on failure rate"""
        import random
        return random.random() < self.failure_rate
    
    # Additional methods for testing
    def get_message_history(self, topic_filter: Optional[str] = None) -> List[MockMessage]:
        """Get message history, optionally filtered by topic"""
        with self._lock:
            if topic_filter:
                return [msg for msg in self.message_history 
                       if self._topic_matches(msg.topic, topic_filter)]
            return self.message_history.copy()
    
    def get_last_message(self, topic_filter: Optional[str] = None) -> Optional[MockMessage]:
        """Get the last message, optionally filtered by topic"""
        messages = self.get_message_history(topic_filter)
        return messages[-1] if messages else None
    
    def clear_history(self):
        """Clear message history"""
        with self._lock:
            self.message_history.clear()
    
    def set_simulation_params(self, connection_delay: float = 0.0, 
                            publish_delay: float = 0.0, failure_rate: float = 0.0):
        """Set simulation parameters for testing edge cases"""
        self.connection_delay = connection_delay
        self.publish_delay = publish_delay
        self.failure_rate = failure_rate
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        with self._lock:
            return {
                **self.stats,
                'connected': self.connected,
                'client_id': self.client_id,
                'message_history_size': len(self.message_history),
                'retained_messages': len(self.retained_messages),
                'active_subscriptions': len(self.subscribers)
            }
    
    def reset(self):
        """Reset client to initial state"""
        with self._lock:
            self.connected = False
            self.message_history.clear()
            self.subscribers.clear()
            self.retained_messages.clear()
            self.stats = {
                'messages_published': 0,
                'messages_received': 0,
                'connections': 0,
                'disconnections': 0,
                'subscription_count': 0
            }


class MockMQTTClientWrapper:
    """
    Mock wrapper that mimics the MQTTClientWrapper interface
    """
    
    def __init__(self, config):
        self.config = config
        self._client = MockMQTTClient(config.client_id)
        self._connected = False
        self._message_callbacks = {}
        self._connection_callbacks = {}
    
    def connect(self) -> bool:
        """Connect to mock broker"""
        success = self._client.connect()
        self._connected = success
        
        # Notify connection callbacks
        for callback in self._connection_callbacks.values():
            try:
                callback(success)
            except Exception:
                pass
        
        return success
    
    def disconnect(self):
        """Disconnect from mock broker"""
        self._client.disconnect()
        self._connected = False
        
        # Notify connection callbacks
        for callback in self._connection_callbacks.values():
            try:
                callback(False)
            except Exception:
                pass
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 0, retain: bool = False) -> bool:
        """Publish message to mock broker"""
        return self._client.publish(topic, payload, qos, retain)
    
    def subscribe(self, topic_pattern: str, qos: int = 0) -> bool:
        """Subscribe to topic (callback added separately)"""
        success = self._client.subscribe(topic_pattern, qos)
        return success
    
    def subscribe_with_callback(self, topic_pattern: str, callback: Callable, qos: int = 0) -> bool:
        """Subscribe to topic with callback (for tests)"""
        success = self._client.subscribe(topic_pattern, qos)
        if success:
            self._message_callbacks[topic_pattern] = callback
            self._client.message_callback_add(topic_pattern, self._wrap_callback(callback))
        return success
    
    def message_callback_add(self, topic_pattern: str, callback: Callable):
        """Add callback for specific topic (matches paho-mqtt interface)"""
        self._message_callbacks[topic_pattern] = callback
        self._client.message_callback_add(topic_pattern, self._wrap_callback(callback))
    
    def message_callback_remove(self, topic_pattern: str):
        """Remove callback for specific topic (matches paho-mqtt interface)"""
        self._message_callbacks.pop(topic_pattern, None)
        self._client.message_callback_remove(topic_pattern)
    
    def unsubscribe(self, topic_pattern: str) -> bool:
        """Unsubscribe from topic"""
        success = self._client.unsubscribe(topic_pattern)
        if success:
            self._message_callbacks.pop(topic_pattern, None)
            self._client.message_callback_remove(topic_pattern)
        return success
    
    def _wrap_callback(self, callback: Callable) -> Callable:
        """Wrap callback to match expected interface"""
        def wrapper(client, userdata, message):
            try:
                # Parse JSON payload
                payload = json.loads(message.payload.decode('utf-8'))
                
                # Create message data structure
                message_data = {
                    'topic': message.topic,
                    'payload': payload,
                    'qos': message.qos,
                    'retain': message.retain,
                    'received_at': datetime.now().isoformat()
                }
                
                callback(message_data)
                
            except Exception as e:
                print(f"Error in callback wrapper: {e}")
        
        return wrapper
    
    def add_connection_callback(self, name: str, callback: Callable):
        """Add connection status callback"""
        self._connection_callbacks[name] = callback
    
    def remove_connection_callback(self, name: str):
        """Remove connection status callback"""
        self._connection_callbacks.pop(name, None)
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
        return {
            'connected': self._connected,
            'broker_host': self.config.broker_host,
            'broker_port': self.config.broker_port,
            'client_id': self.config.client_id,
            'subscriptions': list(self._message_callbacks.keys()),
            'mock_stats': self._client.get_stats()
        }
    
    # Testing utilities
    def get_mock_client(self) -> MockMQTTClient:
        """Get underlying mock client for testing"""
        return self._client