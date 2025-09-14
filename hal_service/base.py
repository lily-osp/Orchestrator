"""
Base classes for the Hardware Abstraction Layer (HAL).

This module defines the abstract base classes that all hardware components must inherit from,
providing standardized interfaces for sensors, actuators, and general devices.
"""

import json
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

from .logging_service import get_logging_service


class Device(ABC):
    """
    Abstract base class for all hardware devices in the HAL.
    
    Provides common functionality for device identification, status management,
    and MQTT communication that all hardware components share.
    """
    
    def __init__(self, device_id: str, mqtt_client, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a hardware device.
        
        Args:
            device_id: Unique identifier for this device instance
            mqtt_client: MQTT client instance for communication
            config: Optional configuration dictionary for device parameters
        """
        self.device_id = device_id
        self.mqtt_client = mqtt_client
        self.config = config or {}
        self.status = "initialized"
        self.last_updated = datetime.now()
        self._initialized = False
        
        # Initialize device logger
        logging_service = get_logging_service()
        self.logger = logging_service.get_device_logger(device_id)
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the hardware device and establish communication.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """
        Safely stop the device and release any resources.
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the device.
        
        Returns:
            Dict containing device status information
        """
        pass
    
    def publish_status(self, data: Dict[str, Any]) -> None:
        """
        Publish device status to MQTT.
        
        Args:
            data: Status data dictionary to publish
        """
        if self.mqtt_client:
            topic = f"orchestrator/status/{self.device_id}"
            message = {
                "timestamp": datetime.now().isoformat(),
                "device_id": self.device_id,
                "status": self.status,
                **data
            }
            try:
                self.mqtt_client.publish(topic, json.dumps(message))
                self.logger.log_mqtt_event(topic, "publish", "success", message_size=len(json.dumps(message)))
            except Exception as e:
                self.logger.log_mqtt_event(topic, "publish", "failure", error=str(e))
                self.logger.exception(f"Failed to publish status for device {self.device_id}")
    
    def is_initialized(self) -> bool:
        """
        Check if the device has been successfully initialized.
        
        Returns:
            bool: True if device is initialized and ready
        """
        return self._initialized
    
    def set_status(self, status: str) -> None:
        """
        Update the device status and timestamp.
        
        Args:
            status: New status string
        """
        old_status = self.status
        self.status = status
        self.last_updated = datetime.now()
        
        # Log status change
        self.logger.log_device_event(
            self.device_id, 
            "status_change", 
            "success",
            old_status=old_status,
            new_status=status
        )


class Sensor(Device):
    """
    Abstract base class for all sensor devices.
    
    Extends Device with sensor-specific functionality including data reading,
    automatic publishing, and configurable update rates.
    """
    
    def __init__(self, device_id: str, mqtt_client, config: Optional[Dict[str, Any]] = None, 
                 publish_rate: float = 1.0):
        """
        Initialize a sensor device.
        
        Args:
            device_id: Unique identifier for this sensor
            mqtt_client: MQTT client for publishing sensor data
            config: Optional configuration dictionary
            publish_rate: Rate in Hz for automatic data publishing
        """
        super().__init__(device_id, mqtt_client, config)
        self.publish_rate = publish_rate
        self._running = False
        self._publish_thread = None
    
    @abstractmethod
    def read_data(self) -> Dict[str, Any]:
        """
        Read current sensor data.
        
        Returns:
            Dict containing the current sensor readings
        """
        pass
    
    def start_publishing(self) -> None:
        """
        Start automatic publishing of sensor data at the configured rate.
        """
        if not self._running and self._initialized:
            self._running = True
            self._publish_thread = threading.Thread(target=self._publish_loop, daemon=True)
            self._publish_thread.start()
    
    def stop_publishing(self) -> None:
        """
        Stop automatic publishing of sensor data.
        """
        self._running = False
        if self._publish_thread:
            self._publish_thread.join(timeout=1.0)
    
    def stop(self) -> None:
        """
        Stop the sensor and clean up resources.
        """
        self.stop_publishing()
        self.set_status("stopped")
    
    def publish_data(self, data: Dict[str, Any]) -> None:
        """
        Publish sensor data to MQTT.
        
        Args:
            data: Sensor data dictionary to publish
        """
        if self.mqtt_client:
            topic = f"orchestrator/data/{self.device_id}"
            message = {
                "timestamp": datetime.now().isoformat(),
                "device_id": self.device_id,
                "data": data
            }
            try:
                self.mqtt_client.publish(topic, json.dumps(message))
                self.logger.log_mqtt_event(topic, "publish", "success", data_points=len(data))
            except Exception as e:
                self.logger.log_mqtt_event(topic, "publish", "failure", error=str(e))
                self.logger.exception(f"Failed to publish data for sensor {self.device_id}")
    
    def _publish_loop(self) -> None:
        """
        Internal loop for automatic data publishing.
        """
        interval = 1.0 / self.publish_rate if self.publish_rate > 0 else 1.0
        
        while self._running:
            try:
                if self._initialized:
                    start_time = time.time()
                    data = self.read_data()
                    self.publish_data(data)
                    
                    # Log performance metric
                    read_time = time.time() - start_time
                    self.logger.log_performance_metric("sensor_read_time", read_time, "seconds")
                    
                time.sleep(interval)
            except Exception as e:
                self.logger.exception(f"Error in sensor {self.device_id} publish loop")
                time.sleep(interval)


class Actuator(Device):
    """
    Abstract base class for all actuator devices.
    
    Extends Device with actuator-specific functionality including command execution,
    MQTT command subscription, and movement control.
    """
    
    def __init__(self, device_id: str, mqtt_client, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an actuator device.
        
        Args:
            device_id: Unique identifier for this actuator
            mqtt_client: MQTT client for receiving commands
            config: Optional configuration dictionary
        """
        super().__init__(device_id, mqtt_client, config)
        self._command_topic = f"orchestrator/cmd/{device_id}"
        self._subscribed = False
    
    @abstractmethod
    def execute_command(self, command: Dict[str, Any]) -> bool:
        """
        Execute a command received via MQTT.
        
        Args:
            command: Command dictionary containing action and parameters
            
        Returns:
            bool: True if command executed successfully, False otherwise
        """
        pass
    
    def subscribe_to_commands(self) -> None:
        """
        Subscribe to MQTT commands for this actuator.
        """
        if self.mqtt_client and not self._subscribed:
            self.mqtt_client.subscribe(self._command_topic)
            self.mqtt_client.message_callback_add(self._command_topic, self._handle_command)
            self._subscribed = True
    
    def unsubscribe_from_commands(self) -> None:
        """
        Unsubscribe from MQTT commands.
        """
        if self.mqtt_client and self._subscribed:
            self.mqtt_client.unsubscribe(self._command_topic)
            self.mqtt_client.message_callback_remove(self._command_topic)
            self._subscribed = False
    
    def stop(self) -> None:
        """
        Stop the actuator and clean up resources.
        """
        self.unsubscribe_from_commands()
        self.set_status("stopped")
    
    def _handle_command(self, client, userdata, message) -> None:
        """
        Internal handler for incoming MQTT commands.
        
        Args:
            client: MQTT client instance
            userdata: User data (unused)
            message: MQTT message containing the command
        """
        try:
            command = json.loads(message.payload.decode())
            command_id = command.get("command_id", "unknown")
            action = command.get("action", "unknown")
            
            self.logger.log_mqtt_event(
                message.topic, 
                "receive", 
                "success",
                command_id=command_id,
                action=action
            )
            
            start_time = time.time()
            success = self.execute_command(command)
            execution_time = time.time() - start_time
            
            # Log command execution
            self.logger.log_device_event(
                self.device_id,
                "command_executed",
                "success" if success else "failure",
                command_id=command_id,
                action=action,
                execution_time=execution_time
            )
            
            # Publish command acknowledgment
            ack_topic = f"orchestrator/ack/{self.device_id}"
            ack_message = {
                "timestamp": datetime.now().isoformat(),
                "device_id": self.device_id,
                "command_id": command_id,
                "success": success
            }
            self.mqtt_client.publish(ack_topic, json.dumps(ack_message))
            
        except Exception as e:
            self.logger.exception(f"Error handling command for {self.device_id}")
            self.logger.log_device_event(
                self.device_id,
                "command_error",
                "failure",
                error=str(e)
            )