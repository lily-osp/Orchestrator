"""
Mock HAL Orchestrator for Testing and Development

Provides a complete mock implementation of the HAL orchestrator that simulates
all hardware components without requiring physical devices. Useful for UI/control
development and testing.
"""

import sys
import signal
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ..config import ConfigurationService, OrchestratorConfig
from .mock_mqtt_client import MockMQTTClientWrapper, MQTTConfig
from ..logging_service import get_logging_service
from .mock_devices import (
    MockMotorController,
    MockEncoderSensor, 
    MockLidarSensor,
    MockSafetyMonitor,
    MockStateManager,
    get_simulation_coordinator
)
from ..base import Device


class MockHALOrchestrator:
    """
    Mock HAL Orchestrator that simulates the complete hardware system.
    
    This class provides the same interface as the real HAL orchestrator but
    uses mock devices that simulate hardware behavior. Perfect for:
    - UI and control system development
    - Testing without physical hardware
    - Continuous integration testing
    - Demonstration and training
    """
    
    def __init__(self, config_path: Optional[str] = None, 
                 enable_realistic_delays: bool = True,
                 enable_failures: bool = False):
        """
        Initialize the mock HAL orchestrator.
        
        Args:
            config_path: Path to configuration file, or None for default
            enable_realistic_delays: Add realistic delays to simulate hardware timing
            enable_failures: Enable random failures for testing error handling
        """
        self.config_path = config_path
        self.enable_realistic_delays = enable_realistic_delays
        self.enable_failures = enable_failures
        
        self.config: Optional[OrchestratorConfig] = None
        self.mqtt_client: Optional[MockMQTTClientWrapper] = None
        self.devices: Dict[str, Device] = {}
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Mock-specific components
        self.safety_monitor: Optional[MockSafetyMonitor] = None
        self.state_manager: Optional[MockStateManager] = None
        self.simulation_coordinator = get_simulation_coordinator()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("MockHALOrchestrator initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def initialize(self) -> bool:
        """
        Initialize the mock HAL orchestrator and all components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Starting Mock HAL Orchestrator initialization...")
            
            # Load configuration
            if not self._load_configuration():
                return False
            
            # Initialize logging service
            if not self._initialize_logging():
                return False
            
            # Initialize mock MQTT client
            if not self._initialize_mqtt():
                return False
            
            # Initialize mock hardware devices
            if not self._initialize_devices():
                return False
            
            # Initialize additional mock services
            if not self._initialize_mock_services():
                return False
            
            self.running = True
            self.logger.info("Mock HAL Orchestrator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception("Failed to initialize Mock HAL Orchestrator")
            return False
    
    def _load_configuration(self) -> bool:
        """Load and validate configuration from file."""
        try:
            config_service = ConfigurationService(self.config_path)
            
            # Try to load existing config, or create default if not found
            try:
                self.config = config_service.load_config()
            except FileNotFoundError:
                self.logger.info("Configuration file not found, creating default config")
                config_path = config_service.create_default_config()
                self.config = config_service.load_config()
                self.logger.info(f"Created default configuration at {config_path}")
            
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
            
            self.logger.info("Mock logging service initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize logging: {e}")
            return False
    
    def _initialize_mqtt(self) -> bool:
        """Initialize mock MQTT client."""
        try:
            mqtt_config = MQTTConfig(
                broker_host=self.config.mqtt.broker_host,
                broker_port=self.config.mqtt.broker_port,
                keepalive=self.config.mqtt.keepalive,
                client_id=self.config.mqtt.client_id or "mock_orchestrator_hal",
                username=self.config.mqtt.username,
                password=self.config.mqtt.password
            )
            
            self.mqtt_client = MockMQTTClientWrapper(mqtt_config)
            
            # Configure simulation parameters
            mock_client = self.mqtt_client.get_mock_client()
            if self.enable_realistic_delays:
                mock_client.set_simulation_params(
                    connection_delay=0.1,
                    publish_delay=0.001
                )
            
            if self.enable_failures:
                mock_client.set_simulation_params(failure_rate=0.01)  # 1% failure rate
            
            # Add connection status callback
            self.mqtt_client.add_connection_callback("orchestrator", self._mqtt_connection_callback)
            
            # Connect to mock broker
            if not self.mqtt_client.connect():
                self.logger.error("Failed to connect to mock MQTT broker")
                return False
            
            self.logger.info("Mock MQTT client initialized and connected")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize mock MQTT client: {e}")
            return False
    
    def _mqtt_connection_callback(self, connected: bool):
        """Handle MQTT connection status changes."""
        if connected:
            self.logger.info("Mock MQTT client connected")
            self._publish_system_status("connected")
        else:
            self.logger.warning("Mock MQTT client disconnected")
            self._publish_system_status("disconnected")
    
    def _initialize_devices(self) -> bool:
        """Initialize all mock hardware devices from configuration."""
        try:
            # Initialize motors
            for motor_config in self.config.motors:
                if not self._initialize_motor(motor_config):
                    self.logger.error(f"Failed to initialize mock motor: {motor_config.name}")
                    return False
            
            # Initialize sensors
            for sensor_config in self.config.sensors:
                if not self._initialize_sensor(sensor_config):
                    self.logger.error(f"Failed to initialize mock sensor: {sensor_config.name}")
                    return False
            
            self.logger.info(f"Initialized {len(self.devices)} mock devices successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize mock devices: {e}")
            return False
    
    def _initialize_motor(self, motor_config) -> bool:
        """Initialize a single mock motor device."""
        try:
            self.logger.info(f"Initializing mock motor: {motor_config.name}")
            
            motor = MockMotorController(
                device_id=motor_config.name,
                mqtt_client=self.mqtt_client,
                config=motor_config.__dict__
            )
            
            if not motor.initialize():
                self.logger.error(f"Mock motor {motor_config.name} initialization failed")
                return False
            
            self.devices[motor_config.name] = motor
            self.logger.info(f"Mock motor {motor_config.name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing mock motor {motor_config.name}: {e}")
            return False
    
    def _initialize_sensor(self, sensor_config) -> bool:
        """Initialize a single mock sensor device."""
        try:
            self.logger.info(f"Initializing mock sensor: {sensor_config.name} (type: {sensor_config.type})")
            
            # Create appropriate mock sensor based on type
            if sensor_config.type == "encoder":
                sensor = MockEncoderSensor(
                    device_id=sensor_config.name,
                    mqtt_client=self.mqtt_client,
                    config=sensor_config.__dict__
                )
            elif sensor_config.type == "lidar":
                sensor = MockLidarSensor(
                    device_id=sensor_config.name,
                    mqtt_client=self.mqtt_client,
                    config=sensor_config.__dict__
                )
            else:
                self.logger.warning(f"Unsupported sensor type for mock: {sensor_config.type}")
                # Create a generic mock sensor
                sensor = MockEncoderSensor(  # Use encoder as fallback
                    device_id=sensor_config.name,
                    mqtt_client=self.mqtt_client,
                    config=sensor_config.__dict__
                )
            
            if not sensor.initialize():
                self.logger.error(f"Mock sensor {sensor_config.name} initialization failed")
                return False
            
            self.devices[sensor_config.name] = sensor
            self.logger.info(f"Mock sensor {sensor_config.name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing mock sensor {sensor_config.name}: {e}")
            return False
    
    def _initialize_mock_services(self) -> bool:
        """Initialize additional mock services (safety monitor, state manager)."""
        try:
            # Initialize mock safety monitor
            if self.config.safety.enabled:
                self.safety_monitor = MockSafetyMonitor(
                    mqtt_client=self.mqtt_client,
                    config=self.config.safety.__dict__
                )
                
                if not self.safety_monitor.start():
                    self.logger.error("Failed to start mock safety monitor")
                    return False
                
                self.logger.info("Mock safety monitor started")
            
            # Initialize mock state manager
            self.state_manager = MockStateManager(
                mqtt_client=self.mqtt_client,
                wheel_base=0.3,  # Default wheel base
                publish_rate=10.0
            )
            
            if not self.state_manager.start():
                self.logger.error("Failed to start mock state manager")
                return False
            
            self.logger.info("Mock state manager started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize mock services: {e}")
            return False
    
    def run(self):
        """
        Main run loop for the mock HAL orchestrator.
        
        Monitors system health and publishes status updates.
        """
        try:
            self.logger.info("Mock HAL Orchestrator started, entering main loop...")
            self._publish_system_status("running")
            
            heartbeat_interval = self.config.system.heartbeat_interval
            last_heartbeat = time.time()
            
            while self.running and not self.shutdown_event.is_set():
                current_time = time.time()
                
                # Update simulation coordinator
                self.simulation_coordinator.update()
                
                # Send heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    self._send_heartbeat()
                    last_heartbeat = current_time
                
                # Check device health
                self._check_device_health()
                
                # Sleep for a short interval
                time.sleep(0.1)  # 10Hz update rate for simulation
            
            self.logger.info("Mock HAL Orchestrator main loop exited")
            
        except Exception as e:
            self.logger.exception("Error in Mock HAL Orchestrator main loop")
        finally:
            self._publish_system_status("stopping")
    
    def _send_heartbeat(self):
        """Send system heartbeat with status information."""
        try:
            heartbeat_data = {
                "timestamp": time.time(),
                "status": "running" if self.running else "stopping",
                "device_type": "mock_hal_orchestrator",
                "devices": {
                    name: device.get_status() 
                    for name, device in self.devices.items()
                },
                "mqtt_status": self.mqtt_client.get_status() if self.mqtt_client else None,
                "simulation_state": self.simulation_coordinator.get_robot_state()
            }
            
            if self.mqtt_client and self.mqtt_client.is_connected:
                self.mqtt_client.publish(
                    "orchestrator/status/system",
                    heartbeat_data,
                    qos=0
                )
            
        except Exception as e:
            self.logger.error(f"Error sending mock heartbeat: {e}")
    
    def _check_device_health(self):
        """Check health status of all mock devices."""
        try:
            for name, device in self.devices.items():
                if not device.is_initialized():
                    self.logger.warning(f"Mock device {name} is not initialized")
                    
        except Exception as e:
            self.logger.error(f"Error checking mock device health: {e}")
    
    def _publish_system_status(self, status: str):
        """Publish system status update."""
        try:
            status_data = {
                "timestamp": time.time(),
                "status": status,
                "device_type": "mock_hal_orchestrator",
                "device_count": len(self.devices),
                "initialized_devices": sum(1 for d in self.devices.values() if d.is_initialized()),
                "simulation_enabled": True,
                "realistic_delays": self.enable_realistic_delays,
                "failures_enabled": self.enable_failures
            }
            
            if self.mqtt_client and self.mqtt_client.is_connected:
                self.mqtt_client.publish(
                    "orchestrator/status/hal",
                    status_data,
                    qos=1  # Ensure delivery for status updates
                )
            
        except Exception as e:
            self.logger.error(f"Error publishing mock system status: {e}")
    
    def shutdown(self):
        """
        Gracefully shutdown the mock HAL orchestrator and all devices.
        """
        try:
            self.logger.info("Starting mock HAL graceful shutdown...")
            self.running = False
            self.shutdown_event.set()
            
            # Stop mock services
            if self.safety_monitor:
                self.safety_monitor.stop()
            
            if self.state_manager:
                self.state_manager.stop()
            
            # Stop all devices
            for name, device in self.devices.items():
                try:
                    self.logger.info(f"Stopping mock device: {name}")
                    device.stop()
                except Exception as e:
                    self.logger.error(f"Error stopping mock device {name}: {e}")
            
            # Disconnect MQTT client
            if self.mqtt_client:
                try:
                    self._publish_system_status("stopped")
                    time.sleep(0.1)  # Allow message to be sent
                    self.mqtt_client.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting mock MQTT client: {e}")
            
            self.logger.info("Mock HAL Orchestrator shutdown complete")
            
        except Exception as e:
            self.logger.exception("Error during mock HAL shutdown")
    
    def get_device(self, device_name: str) -> Optional[Device]:
        """Get a mock device by name."""
        return self.devices.get(device_name)
    
    def get_device_status(self, device_name: str) -> Optional[Dict]:
        """Get status of a specific mock device."""
        device = self.devices.get(device_name)
        return device.get_status() if device else None
    
    def get_system_status(self) -> Dict:
        """Get overall mock system status."""
        return {
            "running": self.running,
            "device_count": len(self.devices),
            "device_type": "mock_hal_orchestrator",
            "devices": {name: device.get_status() for name, device in self.devices.items()},
            "mqtt_connected": self.mqtt_client.is_connected if self.mqtt_client else False,
            "config_loaded": self.config is not None,
            "simulation_state": self.simulation_coordinator.get_robot_state(),
            "simulation_enabled": True,
            "realistic_delays": self.enable_realistic_delays,
            "failures_enabled": self.enable_failures
        }
    
    # Testing utilities
    def get_mqtt_client(self) -> MockMQTTClientWrapper:
        """Get the mock MQTT client for testing"""
        return self.mqtt_client
    
    def get_simulation_coordinator(self):
        """Get the simulation coordinator for testing"""
        return self.simulation_coordinator
    
    def inject_command(self, device_name: str, command: Dict[str, Any]):
        """Inject a command directly to a device (for testing)"""
        device = self.devices.get(device_name)
        if device and hasattr(device, 'execute_command'):
            return device.execute_command(command)
        return False
    
    def get_message_history(self, topic_filter: Optional[str] = None):
        """Get MQTT message history for testing"""
        if self.mqtt_client:
            return self.mqtt_client.get_mock_client().get_message_history(topic_filter)
        return []
    
    def reset_simulation(self):
        """Reset simulation state for testing"""
        self.simulation_coordinator.reset_simulation()
        if self.mqtt_client:
            self.mqtt_client.get_mock_client().clear_history()


def main():
    """Main entry point for the mock HAL service."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mock Orchestrator HAL Service")
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
        "--no-delays",
        action="store_true",
        help="Disable realistic timing delays"
    )
    parser.add_argument(
        "--enable-failures",
        action="store_true",
        help="Enable random failures for testing"
    )
    
    args = parser.parse_args()
    
    # Setup basic logging for startup
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create and initialize mock orchestrator
        orchestrator = MockHALOrchestrator(
            config_path=args.config,
            enable_realistic_delays=not args.no_delays,
            enable_failures=args.enable_failures
        )
        
        if not orchestrator.initialize():
            logger.error("Failed to initialize Mock HAL Orchestrator")
            sys.exit(1)
        
        logger.info("Mock HAL Orchestrator started successfully")
        logger.info("This is a SIMULATION - no real hardware is being controlled")
        
        # Run the service
        orchestrator.run()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.exception("Unexpected error in mock HAL main")
        sys.exit(1)
    finally:
        if 'orchestrator' in locals():
            orchestrator.shutdown()


if __name__ == "__main__":
    main()