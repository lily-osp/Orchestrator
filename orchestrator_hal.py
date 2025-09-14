#!/usr/bin/env python3
"""
HAL Orchestration Service for Orchestrator Platform

This is the main service that initializes and manages all hardware device instances
based on the configuration file. It provides graceful shutdown procedures and
coordinates all HAL components.

Requirements covered: 1.4, 6.3
"""

import sys
import signal
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent / "hal_service"))

from hal_service.config import ConfigurationService, OrchestratorConfig
from hal_service.mqtt_client import MQTTClientWrapper, MQTTConfig
from hal_service.logging_service import get_logging_service
from hal_service.motor_controller import MotorController
from hal_service.encoder_sensor import EncoderSensor
from hal_service.lidar_sensor import LidarSensor
from hal_service.base import Device


class HALOrchestrator:
    """
    Main orchestration service for the Hardware Abstraction Layer.
    
    This service manages the lifecycle of all hardware devices, coordinates
    MQTT communication, and provides graceful shutdown capabilities.
    """
    
    def __init__(self, config_path: Optional[str] = None, test_mode: bool = False):
        """
        Initialize the HAL orchestrator.
        
        Args:
            config_path: Path to configuration file, or None for default
            test_mode: If True, skip hardware initialization for testing
        """
        self.config_path = config_path
        self.test_mode = test_mode
        self.config: Optional[OrchestratorConfig] = None
        self.mqtt_client: Optional[MQTTClientWrapper] = None
        self.devices: Dict[str, Device] = {}
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def initialize(self) -> bool:
        """
        Initialize the HAL orchestrator and all components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Starting HAL Orchestrator initialization...")
            
            # Load configuration
            if not self._load_configuration():
                return False
            
            # Initialize logging service
            if not self._initialize_logging():
                return False
            
            # Initialize MQTT client
            if not self._initialize_mqtt():
                return False
            
            # Initialize hardware devices
            if not self._initialize_devices():
                return False
            
            self.running = True
            self.logger.info("HAL Orchestrator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception("Failed to initialize HAL Orchestrator")
            return False
    
    def _load_configuration(self) -> bool:
        """Load and validate configuration from file."""
        try:
            config_service = ConfigurationService(self.config_path)
            self.config = config_service.load_config()
            
            self.logger.info(f"Loaded configuration from {config_service.config_path}")
            self.logger.info(f"Found {len(self.config.motors)} motors and {len(self.config.sensors)} sensors")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False
    
    def _initialize_logging(self) -> bool:
        """Initialize the logging service with configuration."""
        try:
            logging_service = get_logging_service()
            
            # Configure logging based on config
            log_config = self.config.system.logging
            
            # Create configuration dict for the logging service
            logging_config = {
                'level': log_config.level,
                'format': log_config.format,
                'log_dir': log_config.log_dir,
                'max_log_size': log_config.max_log_size,
                'backup_count': log_config.backup_count,
                'console_output': log_config.console_output,
                'file_output': log_config.file_output
            }
            
            logging_service.configure(logging_config)
            
            self.logger.info("Logging service initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize logging: {e}")
            return False
    
    def _initialize_mqtt(self) -> bool:
        """Initialize MQTT client with configuration."""
        if self.test_mode:
            self.logger.info("Test mode: Skipping MQTT initialization")
            return True
            
        try:
            mqtt_config = MQTTConfig(
                broker_host=self.config.mqtt.broker_host,
                broker_port=self.config.mqtt.broker_port,
                keepalive=self.config.mqtt.keepalive,
                client_id=self.config.mqtt.client_id or "orchestrator_hal",
                username=self.config.mqtt.username,
                password=self.config.mqtt.password
            )
            
            self.mqtt_client = MQTTClientWrapper(mqtt_config)
            
            # Add connection status callback
            self.mqtt_client.add_connection_callback("orchestrator", self._mqtt_connection_callback)
            
            # Connect to broker
            if not self.mqtt_client.connect():
                self.logger.error("Failed to connect to MQTT broker")
                return False
            
            # Wait for connection
            max_wait = 10  # seconds
            wait_time = 0
            while not self.mqtt_client.is_connected and wait_time < max_wait:
                time.sleep(0.1)
                wait_time += 0.1
            
            if not self.mqtt_client.is_connected:
                self.logger.error("MQTT connection timeout")
                return False
            
            self.logger.info("MQTT client initialized and connected")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MQTT client: {e}")
            return False
    
    def _mqtt_connection_callback(self, connected: bool):
        """Handle MQTT connection status changes."""
        if connected:
            self.logger.info("MQTT client connected")
            self._publish_system_status("connected")
        else:
            self.logger.warning("MQTT client disconnected")
            self._publish_system_status("disconnected")
    
    def _initialize_devices(self) -> bool:
        """Initialize all hardware devices from configuration."""
        if self.test_mode:
            self.logger.info("Test mode: Skipping hardware device initialization")
            return True
            
        try:
            # Initialize motors
            for motor_config in self.config.motors:
                if not self._initialize_motor(motor_config):
                    self.logger.error(f"Failed to initialize motor: {motor_config.name}")
                    return False
            
            # Initialize sensors
            for sensor_config in self.config.sensors:
                if not self._initialize_sensor(sensor_config):
                    self.logger.error(f"Failed to initialize sensor: {sensor_config.name}")
                    return False
            
            self.logger.info(f"Initialized {len(self.devices)} devices successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize devices: {e}")
            return False
    
    def _initialize_motor(self, motor_config) -> bool:
        """Initialize a single motor device."""
        try:
            self.logger.info(f"Initializing motor: {motor_config.name}")
            
            motor = MotorController(
                device_id=motor_config.name,
                mqtt_client=self.mqtt_client,
                config=motor_config
            )
            
            if not motor.initialize():
                self.logger.error(f"Motor {motor_config.name} initialization failed")
                return False
            
            self.devices[motor_config.name] = motor
            self.logger.info(f"Motor {motor_config.name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing motor {motor_config.name}: {e}")
            return False
    
    def _initialize_sensor(self, sensor_config) -> bool:
        """Initialize a single sensor device."""
        try:
            self.logger.info(f"Initializing sensor: {sensor_config.name} (type: {sensor_config.type})")
            
            # Create appropriate sensor based on type
            if sensor_config.type == "encoder":
                sensor = EncoderSensor(
                    device_id=sensor_config.name,
                    mqtt_client=self.mqtt_client,
                    config=sensor_config
                )
            elif sensor_config.type == "lidar":
                sensor = LidarSensor(
                    device_id=sensor_config.name,
                    mqtt_client=self.mqtt_client,
                    config=sensor_config
                )
            else:
                self.logger.error(f"Unsupported sensor type: {sensor_config.type}")
                return False
            
            if not sensor.initialize():
                self.logger.error(f"Sensor {sensor_config.name} initialization failed")
                return False
            
            self.devices[sensor_config.name] = sensor
            self.logger.info(f"Sensor {sensor_config.name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing sensor {sensor_config.name}: {e}")
            return False
    
    def run(self):
        """
        Main run loop for the HAL orchestrator.
        
        Monitors system health and publishes status updates.
        """
        try:
            self.logger.info("HAL Orchestrator started, entering main loop...")
            self._publish_system_status("running")
            
            heartbeat_interval = self.config.system.heartbeat_interval
            last_heartbeat = time.time()
            
            while self.running and not self.shutdown_event.is_set():
                current_time = time.time()
                
                # Send heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    self._send_heartbeat()
                    last_heartbeat = current_time
                
                # Check device health
                self._check_device_health()
                
                # Sleep for a short interval
                time.sleep(1.0)
            
            self.logger.info("HAL Orchestrator main loop exited")
            
        except Exception as e:
            self.logger.exception("Error in HAL Orchestrator main loop")
        finally:
            self._publish_system_status("stopping")
    
    def _send_heartbeat(self):
        """Send system heartbeat with status information."""
        try:
            heartbeat_data = {
                "timestamp": time.time(),
                "status": "running" if self.running else "stopping",
                "devices": {
                    name: device.get_status() 
                    for name, device in self.devices.items()
                },
                "mqtt_status": self.mqtt_client.get_status() if self.mqtt_client else None
            }
            
            if self.mqtt_client and self.mqtt_client.is_connected:
                self.mqtt_client.publish(
                    "orchestrator/status/system",
                    heartbeat_data,
                    qos=0
                )
            
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
    
    def _check_device_health(self):
        """Check health status of all devices."""
        try:
            for name, device in self.devices.items():
                if not device.is_initialized():
                    self.logger.warning(f"Device {name} is not initialized")
                    # Could implement recovery logic here
                    
        except Exception as e:
            self.logger.error(f"Error checking device health: {e}")
    
    def _publish_system_status(self, status: str):
        """Publish system status update."""
        try:
            status_data = {
                "timestamp": time.time(),
                "status": status,
                "device_count": len(self.devices),
                "initialized_devices": sum(1 for d in self.devices.values() if d.is_initialized())
            }
            
            if self.mqtt_client and self.mqtt_client.is_connected:
                self.mqtt_client.publish(
                    "orchestrator/status/hal",
                    status_data,
                    qos=1  # Ensure delivery for status updates
                )
            
        except Exception as e:
            self.logger.error(f"Error publishing system status: {e}")
    
    def shutdown(self):
        """
        Gracefully shutdown the HAL orchestrator and all devices.
        """
        try:
            self.logger.info("Starting graceful shutdown...")
            self.running = False
            self.shutdown_event.set()
            
            # Stop all devices
            for name, device in self.devices.items():
                try:
                    self.logger.info(f"Stopping device: {name}")
                    device.stop()
                except Exception as e:
                    self.logger.error(f"Error stopping device {name}: {e}")
            
            # Disconnect MQTT client
            if self.mqtt_client:
                try:
                    self._publish_system_status("stopped")
                    time.sleep(0.5)  # Allow message to be sent
                    self.mqtt_client.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting MQTT client: {e}")
            
            self.logger.info("HAL Orchestrator shutdown complete")
            
        except Exception as e:
            self.logger.exception("Error during shutdown")
    
    def get_device(self, device_name: str) -> Optional[Device]:
        """Get a device by name."""
        return self.devices.get(device_name)
    
    def get_device_status(self, device_name: str) -> Optional[Dict]:
        """Get status of a specific device."""
        device = self.devices.get(device_name)
        return device.get_status() if device else None
    
    def get_system_status(self) -> Dict:
        """Get overall system status."""
        return {
            "running": self.running,
            "device_count": len(self.devices),
            "devices": {name: device.get_status() for name, device in self.devices.items()},
            "mqtt_connected": self.mqtt_client.is_connected if self.mqtt_client else False,
            "config_loaded": self.config is not None
        }


def main():
    """Main entry point for the HAL service."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrator HAL Service")
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (skip hardware initialization)"
    )
    
    args = parser.parse_args()
    
    # Setup basic logging for startup
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create and initialize orchestrator
        orchestrator = HALOrchestrator(config_path=args.config, test_mode=args.test_mode)
        
        if not orchestrator.initialize():
            logger.error("Failed to initialize HAL Orchestrator")
            sys.exit(1)
        
        # Run the service
        orchestrator.run()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.exception("Unexpected error in main")
        sys.exit(1)
    finally:
        if 'orchestrator' in locals():
            orchestrator.shutdown()


if __name__ == "__main__":
    main()