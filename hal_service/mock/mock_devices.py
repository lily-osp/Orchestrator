"""
Mock Device Implementations for HAL Testing

Provides mock implementations of all HAL device classes that simulate
hardware behavior without requiring physical components.
"""

import time
import threading
import json
from typing import Dict, Any, Optional
from datetime import datetime

from ..base import Device, Sensor, Actuator
from .data_generators import (
    LidarDataGenerator, 
    EncoderDataGenerator, 
    MotorDataGenerator,
    SimulationCoordinator
)


# Global simulation coordinator for consistent state across all mock devices
_simulation_coordinator = None


def get_simulation_coordinator() -> SimulationCoordinator:
    """Get the global simulation coordinator instance"""
    global _simulation_coordinator
    if _simulation_coordinator is None:
        _simulation_coordinator = SimulationCoordinator()
    return _simulation_coordinator


class MockMotorController(Actuator):
    """
    Mock motor controller that simulates DC motor behavior.
    
    Provides realistic responses to commands and generates telemetry
    data without requiring physical hardware.
    """
    
    def __init__(self, device_id: str, mqtt_client, config: Dict[str, Any]):
        super().__init__(device_id, mqtt_client, config)
        
        # Get simulation coordinator
        self.coordinator = get_simulation_coordinator()
        
        # Motor simulation parameters
        self.max_speed = config.get('max_speed', 1.0)
        self.acceleration = config.get('acceleration', 0.5)
        
        # Mock GPIO pins (for status reporting)
        self.gpio_pins = config.get('gpio_pins', {'enable': 18, 'direction': 19})
        self.encoder_pins = config.get('encoder_pins', {'a': 20, 'b': 21})
        
        # Simulation state
        self.current_command = None
        self.command_start_time = None
        
        # Publishing thread
        self._publish_thread = None
        self._publish_interval = 0.1  # 10Hz
        
        self.logger.info(f"MockMotorController {device_id} initialized")
    
    def initialize(self) -> bool:
        """Initialize the mock motor controller"""
        try:
            # Simulate initialization delay
            time.sleep(0.1)
            
            # Subscribe to commands
            self.subscribe_to_commands()
            
            self._initialized = True
            self.set_status("ready")
            
            # Start telemetry publishing after setting initialized flag
            self._start_telemetry_publishing()
            
            self.logger.info(f"MockMotorController {self.device_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to initialize MockMotorController {self.device_id}")
            return False
    
    def execute_command(self, command: Dict[str, Any]) -> bool:
        """Execute a motor command"""
        try:
            action = command.get("action")
            parameters = command.get("parameters", {})
            command_id = command.get("command_id", "unknown")
            
            self.logger.info(f"Executing mock command: {action} with parameters: {parameters}")
            
            # Store current command
            self.current_command = command
            self.command_start_time = time.time()
            
            # Process command through simulation coordinator
            self.coordinator.process_motor_command(self.device_id, command)
            
            # Update status based on action
            if action in ["move_forward", "move_backward", "rotate_left", "rotate_right"]:
                self.set_status("moving")
            elif action == "stop":
                self.set_status("ready")
            elif action == "set_speed":
                speed = parameters.get("speed", 0.0)
                if speed > 0:
                    self.set_status("moving")
                else:
                    self.set_status("ready")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error executing mock command: {command}")
            return False
    
    def _start_telemetry_publishing(self):
        """Start publishing telemetry data"""
        if self._publish_thread is None or not self._publish_thread.is_alive():
            self._publish_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
            self._publish_thread.start()
    
    def _telemetry_loop(self):
        """Main loop for publishing motor telemetry"""
        while self._initialized and self.status != "stopped":
            try:
                # Get motor data from coordinator
                motor_data = self.coordinator.get_motor_data(self.device_id)
                
                # Publish telemetry
                telemetry_topic = f"orchestrator/data/{self.device_id}"
                telemetry_message = {
                    "timestamp": datetime.now().isoformat(),
                    "device_id": self.device_id,
                    "data": motor_data
                }
                
                if self.mqtt_client:
                    self.mqtt_client.publish(telemetry_topic, telemetry_message)
                
                time.sleep(self._publish_interval)
                
            except Exception as e:
                self.logger.exception("Error in mock motor telemetry loop")
                time.sleep(self._publish_interval)
    
    def stop(self) -> None:
        """Stop the mock motor controller"""
        try:
            # Stop any current movement
            if self.current_command:
                stop_command = {"action": "stop", "parameters": {}}
                self.coordinator.process_motor_command(self.device_id, stop_command)
            
            # Unsubscribe from commands
            self.unsubscribe_from_commands()
            
            self.set_status("stopped")
            self.logger.info(f"MockMotorController {self.device_id} stopped")
            
        except Exception as e:
            self.logger.exception("Error stopping mock motor controller")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current motor status"""
        motor_data = self.coordinator.get_motor_data(self.device_id)
        
        return {
            "device_id": self.device_id,
            "status": self.status,
            "initialized": self._initialized,
            "device_type": "mock_motor",
            "last_updated": self.last_updated.isoformat(),
            "current_command": self.current_command,
            "command_start_time": self.command_start_time,
            "gpio_pins": self.gpio_pins,
            "encoder_pins": self.encoder_pins,
            "motor_data": motor_data
        }


class MockEncoderSensor(Sensor):
    """
    Mock encoder sensor that simulates wheel encoder behavior.
    
    Generates realistic encoder data based on motor commands and
    simulated mechanical characteristics.
    """
    
    def __init__(self, device_id: str, mqtt_client, config: Dict[str, Any]):
        publish_rate = config.get('publish_rate', 20.0)
        super().__init__(device_id, mqtt_client, config, publish_rate)
        
        # Get simulation coordinator
        self.coordinator = get_simulation_coordinator()
        
        # Encoder configuration
        calibration = config.get('calibration', {})
        self.encoder_resolution = int(calibration.get('resolution', 1000))
        self.wheel_diameter = float(calibration.get('wheel_diameter', 0.1))
        self.gear_ratio = float(calibration.get('gear_ratio', 1.0))
        
        # Mock GPIO pins
        if hasattr(config.get('interface', {}), 'pin'):
            self.encoder_pin_a = config['interface']['pin']
            self.encoder_pin_b = calibration.get('pin_b')
        else:
            self.encoder_pin_a = calibration.get('pin_a', 20)
            self.encoder_pin_b = calibration.get('pin_b', 21)
        
        self.logger.info(f"MockEncoderSensor {device_id} initialized")
    
    def initialize(self) -> bool:
        """Initialize the mock encoder sensor"""
        try:
            # Simulate initialization delay
            time.sleep(0.05)
            
            self._initialized = True
            self.set_status("ready")
            
            # Start publishing telemetry
            self.start_publishing()
            
            self.logger.info(f"MockEncoderSensor {self.device_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to initialize MockEncoderSensor {self.device_id}")
            return False
    
    def read_data(self) -> Dict[str, Any]:
        """Read current encoder data"""
        try:
            # Get encoder data from coordinator
            encoder_data = self.coordinator.get_encoder_data(self.device_id)
            
            # Add mock-specific information
            encoder_data.update({
                'device_type': 'mock_encoder',
                'pins': {
                    'encoder_a': self.encoder_pin_a,
                    'encoder_b': self.encoder_pin_b
                },
                'config': {
                    'encoder_resolution': self.encoder_resolution,
                    'wheel_diameter': self.wheel_diameter,
                    'gear_ratio': self.gear_ratio,
                    'publish_rate': self.publish_rate
                }
            })
            
            return encoder_data
            
        except Exception as e:
            self.logger.exception("Error reading mock encoder data")
            return {
                "tick_count": 0,
                "total_distance": 0.0,
                "velocity": 0.0,
                "direction": 0,
                "error": str(e)
            }
    
    def reset_encoder(self):
        """Reset encoder counts"""
        try:
            # Reset the appropriate encoder in the coordinator
            if 'left' in self.device_id.lower():
                self.coordinator.left_encoder_generator.reset()
            elif 'right' in self.device_id.lower():
                self.coordinator.right_encoder_generator.reset()
            
            self.logger.info(f"MockEncoderSensor {self.device_id} reset")
            
        except Exception as e:
            self.logger.exception("Error resetting mock encoder")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current encoder sensor status"""
        encoder_data = self.coordinator.get_encoder_data(self.device_id)
        
        return {
            "device_id": self.device_id,
            "status": self.status,
            "initialized": self._initialized,
            "device_type": "mock_encoder",
            "last_updated": self.last_updated.isoformat(),
            "publish_rate": self.publish_rate,
            "encoder_data": encoder_data
        }


class MockLidarSensor(Sensor):
    """
    Mock LiDAR sensor that simulates 2D laser scanning.
    
    Generates realistic scan data with obstacles, walls, and noise
    based on the current robot position in the simulation.
    """
    
    def __init__(self, device_id: str, mqtt_client, config: Dict[str, Any]):
        publish_rate = config.get('publish_rate', 10.0)
        super().__init__(device_id, mqtt_client, config, publish_rate)
        
        # Get simulation coordinator
        self.coordinator = get_simulation_coordinator()
        
        # LiDAR configuration
        calibration = config.get('calibration', {})
        self.min_range = float(calibration.get('min_range', 0.15))
        self.max_range = float(calibration.get('max_range', 12.0))
        self.angle_resolution = float(calibration.get('angle_resolution', 1.0))
        self.scan_frequency = float(calibration.get('scan_frequency', 10.0))
        
        # Mock serial configuration
        interface = config.get('interface', {})
        self.port = interface.get('port', '/dev/ttyUSB0')
        self.baudrate = interface.get('baudrate', 115200)
        
        # Scanning state
        self.scanning = False
        self.current_scan = None
        self.scan_count = 0
        
        self.logger.info(f"MockLidarSensor {device_id} initialized")
    
    def initialize(self) -> bool:
        """Initialize the mock LiDAR sensor"""
        try:
            # Simulate connection delay
            time.sleep(0.2)
            
            self._initialized = True
            self.set_status("ready")
            
            # Start scanning
            self.start_scanning()
            
            # Start publishing telemetry
            self.start_publishing()
            
            self.logger.info(f"MockLidarSensor {self.device_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to initialize MockLidarSensor {self.device_id}")
            return False
    
    def start_scanning(self) -> bool:
        """Start LiDAR scanning"""
        if not self.scanning:
            self.scanning = True
            self.logger.info(f"Started mock LiDAR scanning for {self.device_id}")
        return True
    
    def stop_scanning(self) -> None:
        """Stop LiDAR scanning"""
        self.scanning = False
        self.logger.info(f"Stopped mock LiDAR scanning for {self.device_id}")
    
    def read_data(self) -> Dict[str, Any]:
        """Read current LiDAR scan data"""
        try:
            if not self.scanning:
                return {
                    "scan_available": False,
                    "error": "Scanner not running"
                }
            
            # Get LiDAR data from coordinator
            scan_data = self.coordinator.get_lidar_data()
            
            # Store current scan
            self.current_scan = scan_data
            self.scan_count += 1
            
            # Add mock-specific information
            scan_data.update({
                'device_type': 'mock_lidar',
                'port': self.port,
                'baudrate': self.baudrate,
                'scan_count': self.scan_count,
                'scanning': self.scanning
            })
            
            return scan_data
            
        except Exception as e:
            self.logger.exception("Error reading mock LiDAR data")
            return {
                "scan_available": False,
                "error": str(e)
            }
    
    def get_current_scan(self):
        """Get the current scan object"""
        return self.current_scan
    
    def is_obstacle_detected(self, min_distance: float = 0.5, 
                           angle_range: tuple = (-45, 45)) -> bool:
        """Check if obstacles are detected within specified parameters"""
        try:
            if not self.current_scan or not self.current_scan.get('scan_available'):
                return False
            
            ranges = self.current_scan.get('ranges', [])
            angles = self.current_scan.get('angles', [])
            
            for distance, angle in zip(ranges, angles):
                if (angle_range[0] <= angle <= angle_range[1] and 
                    0.1 <= distance <= min_distance):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.exception("Error checking obstacle detection")
            return False
    
    def stop(self) -> None:
        """Stop the mock LiDAR sensor"""
        try:
            self.stop_scanning()
            self.stop_publishing()
            
            self.set_status("stopped")
            self.logger.info(f"MockLidarSensor {self.device_id} stopped")
            
        except Exception as e:
            self.logger.exception("Error stopping mock LiDAR sensor")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current LiDAR sensor status"""
        return {
            "device_id": self.device_id,
            "status": self.status,
            "initialized": self._initialized,
            "device_type": "mock_lidar",
            "last_updated": self.last_updated.isoformat(),
            "scanning": self.scanning,
            "scan_count": self.scan_count,
            "publish_rate": self.publish_rate,
            "connection": {
                "port": self.port,
                "baudrate": self.baudrate,
                "connected": True  # Always connected in mock
            },
            "config": {
                "min_range": self.min_range,
                "max_range": self.max_range,
                "scan_frequency": self.scan_frequency,
                "angle_resolution": self.angle_resolution
            }
        }


class MockSafetyMonitor:
    """
    Mock safety monitor that simulates safety system behavior.
    
    Monitors mock LiDAR data and triggers emergency stops based on
    simulated obstacle detection.
    """
    
    def __init__(self, mqtt_client, config: Dict[str, Any]):
        self.mqtt_client = mqtt_client
        self.config = config
        
        # Get simulation coordinator
        self.coordinator = get_simulation_coordinator()
        
        # Safety configuration
        self.obstacle_threshold = config.get('obstacle_threshold', 0.5)
        self.emergency_stop_timeout = config.get('emergency_stop_timeout', 0.1)
        
        # Safety state
        self.running = False
        self.emergency_stop_active = False
        self.monitor_thread = None
        
        # Statistics
        self.obstacle_detections = []
        self.emergency_stops_triggered = 0
        
        self.logger = None  # Will be set when logging is available
    
    def start(self) -> bool:
        """Start the mock safety monitor"""
        try:
            if self.running:
                return True
            
            self.running = True
            
            # Subscribe to LiDAR data
            if self.mqtt_client:
                self.mqtt_client.subscribe(
                    "orchestrator/data/lidar_01",
                    self._handle_lidar_data
                )
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.exception("Failed to start mock safety monitor")
            return False
    
    def stop(self) -> None:
        """Stop the mock safety monitor"""
        try:
            self.running = False
            
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)
            
            if self.mqtt_client:
                self.mqtt_client.unsubscribe("orchestrator/data/lidar_01")
            
        except Exception as e:
            if self.logger:
                self.logger.exception("Error stopping mock safety monitor")
    
    def _handle_lidar_data(self, message_data: Dict[str, Any]):
        """Handle incoming LiDAR data for safety analysis"""
        try:
            payload = message_data['payload']
            lidar_data = payload.get('data', {})
            
            if not lidar_data.get('scan_available'):
                return
            
            # Check for obstacles in critical zones
            ranges = lidar_data.get('ranges', [])
            angles = lidar_data.get('angles', [])
            
            critical_obstacles = []
            
            # Check front zone (-45 to +45 degrees)
            for distance, angle in zip(ranges, angles):
                if -45 <= angle <= 45 and 0.1 <= distance <= self.obstacle_threshold:
                    critical_obstacles.append((distance, angle))
            
            # Trigger emergency stop if critical obstacles detected
            if critical_obstacles and not self.emergency_stop_active:
                self._trigger_emergency_stop(critical_obstacles)
            
        except Exception as e:
            if self.logger:
                self.logger.exception("Error handling LiDAR data in mock safety monitor")
    
    def _trigger_emergency_stop(self, obstacles):
        """Trigger emergency stop due to obstacles"""
        try:
            self.emergency_stop_active = True
            self.emergency_stops_triggered += 1
            
            # Find closest obstacle
            closest_obstacle = min(obstacles, key=lambda x: x[0])
            
            # Create emergency stop command
            estop_command = {
                "timestamp": datetime.now().isoformat(),
                "command_id": f"mock_safety_estop_{int(time.time())}",
                "action": "emergency_stop",
                "reason": "obstacle_detected",
                "source": "mock_safety_monitor",
                "obstacle_info": {
                    "distance": closest_obstacle[0],
                    "angle": closest_obstacle[1],
                    "total_obstacles": len(obstacles)
                }
            }
            
            # Publish emergency stop
            if self.mqtt_client:
                self.mqtt_client.publish(
                    "orchestrator/cmd/estop",
                    estop_command,
                    qos=1
                )
            
            if self.logger:
                self.logger.critical(
                    f"MOCK EMERGENCY STOP: Obstacle at {closest_obstacle[0]:.2f}m"
                )
            
        except Exception as e:
            if self.logger:
                self.logger.exception("Error triggering mock emergency stop")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Publish safety status
                if self.mqtt_client:
                    status_data = {
                        "timestamp": datetime.now().isoformat(),
                        "device_id": "mock_safety_monitor",
                        "status": "emergency_stop" if self.emergency_stop_active else "monitoring",
                        "emergency_stops_triggered": self.emergency_stops_triggered,
                        "obstacle_threshold": self.obstacle_threshold
                    }
                    
                    self.mqtt_client.publish(
                        "orchestrator/status/safety_monitor",
                        status_data
                    )
                
                # Reset emergency stop if conditions clear
                if self.emergency_stop_active:
                    # Simple reset after 2 seconds (in real system would check conditions)
                    time.sleep(2.0)
                    self.emergency_stop_active = False
                
                time.sleep(1.0)  # 1Hz monitoring
                
            except Exception as e:
                if self.logger:
                    self.logger.exception("Error in mock safety monitoring loop")
                time.sleep(1.0)


class MockStateManager:
    """
    Mock state manager that simulates robot state tracking.
    
    Calculates robot position and heading based on encoder data
    and publishes robot state information.
    """
    
    def __init__(self, mqtt_client, wheel_base: float = 0.3, publish_rate: float = 10.0):
        self.mqtt_client = mqtt_client
        self.wheel_base = wheel_base
        self.publish_rate = publish_rate
        
        # Get simulation coordinator
        self.coordinator = get_simulation_coordinator()
        
        # State management
        self.running = False
        self.publish_thread = None
        
        self.logger = None  # Will be set when logging is available
    
    def start(self) -> bool:
        """Start the mock state manager"""
        try:
            if self.running:
                return True
            
            self.running = True
            
            # Subscribe to encoder data
            if self.mqtt_client:
                self.mqtt_client.subscribe(
                    "orchestrator/data/left_encoder",
                    self._handle_encoder_data
                )
                self.mqtt_client.subscribe(
                    "orchestrator/data/right_encoder",
                    self._handle_encoder_data
                )
            
            # Start publishing thread
            self.publish_thread = threading.Thread(target=self._publish_loop, daemon=True)
            self.publish_thread.start()
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.exception("Failed to start mock state manager")
            return False
    
    def stop(self):
        """Stop the mock state manager"""
        try:
            self.running = False
            
            if self.publish_thread:
                self.publish_thread.join(timeout=2.0)
            
            if self.mqtt_client:
                self.mqtt_client.unsubscribe("orchestrator/data/left_encoder")
                self.mqtt_client.unsubscribe("orchestrator/data/right_encoder")
            
        except Exception as e:
            if self.logger:
                self.logger.exception("Error stopping mock state manager")
    
    def _handle_encoder_data(self, message_data: Dict[str, Any]):
        """Handle encoder data (not needed for mock, coordinator handles this)"""
        pass
    
    def _publish_loop(self):
        """Main loop for publishing robot state"""
        interval = 1.0 / self.publish_rate
        
        while self.running:
            try:
                # Get robot state from coordinator
                robot_state = self.coordinator.get_robot_state()
                
                # Create state message
                state_message = {
                    "timestamp": datetime.now().isoformat(),
                    "position": robot_state['position'],
                    "heading": robot_state['heading'],
                    "velocity": robot_state['velocity'],
                    "status": "active",
                    "mission_status": "idle",
                    "odometry_valid": True,
                    "device_type": "mock_state_manager"
                }
                
                # Publish state
                if self.mqtt_client:
                    self.mqtt_client.publish(
                        "orchestrator/status/robot",
                        state_message,
                        qos=1
                    )
                
                time.sleep(interval)
                
            except Exception as e:
                if self.logger:
                    self.logger.exception("Error in mock state manager publish loop")
                time.sleep(interval)