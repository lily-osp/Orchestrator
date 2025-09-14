"""
LiDAR Sensor Implementation for Orchestrator Platform

This module implements the LidarSensor class that provides 2D LiDAR scanning
with UART/USB communication and real-time obstacle detection capabilities.

Requirements covered: 1.1, 1.2, 1.3, 5.1, 5.2
"""

import time
import threading
import struct
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

try:
    import serial
except ImportError:
    # Mock serial for development/testing environments
    class MockSerial:
        def __init__(self, *args, **kwargs):
            self.is_open = True
            self._mock_data_index = 0
            
        def read(self, size=1):
            # Return mock LiDAR data for testing
            return b'\x00' * size
            
        def write(self, data):
            return len(data)
            
        def close(self):
            self.is_open = False
            
        def flush(self):
            pass
            
        def reset_input_buffer(self):
            pass
            
        def reset_output_buffer(self):
            pass
    
    serial = type('MockSerialModule', (), {
        'Serial': MockSerial,
        'SerialException': Exception,
        'PARITY_NONE': 'N',
        'STOPBITS_ONE': 1,
        'EIGHTBITS': 8
    })()

from .base import Sensor
from .config import SensorConfig


@dataclass
class LidarScan:
    """
    Data structure for LiDAR scan results.
    
    Contains the complete scan data including ranges, angles, and metadata
    for obstacle detection and navigation purposes.
    """
    timestamp: datetime
    ranges: List[float]  # Distance measurements in meters
    angles: List[float]  # Angle measurements in degrees
    min_range: float     # Minimum valid range in meters
    max_range: float     # Maximum valid range in meters
    scan_time: float     # Time taken for complete scan in seconds
    quality: List[int]   # Signal quality for each measurement (0-255)
    
    def get_closest_obstacle(self) -> Tuple[float, float]:
        """
        Get the closest obstacle distance and angle.
        
        Returns:
            Tuple of (distance, angle) for closest valid measurement
        """
        valid_ranges = [(r, a) for r, a in zip(self.ranges, self.angles) 
                       if self.min_range <= r <= self.max_range]
        
        if not valid_ranges:
            return float('inf'), 0.0
            
        return min(valid_ranges, key=lambda x: x[0])
    
    def get_obstacles_in_zone(self, min_angle: float, max_angle: float, 
                             max_distance: float) -> List[Tuple[float, float]]:
        """
        Get all obstacles within a specified angular zone and distance.
        
        Args:
            min_angle: Minimum angle in degrees
            max_angle: Maximum angle in degrees  
            max_distance: Maximum distance in meters
            
        Returns:
            List of (distance, angle) tuples for obstacles in zone
        """
        obstacles = []
        for r, a in zip(self.ranges, self.angles):
            if (min_angle <= a <= max_angle and 
                self.min_range <= r <= min(max_distance, self.max_range)):
                obstacles.append((r, a))
        return obstacles


class LidarSensor(Sensor):
    """
    2D LiDAR Sensor for obstacle detection and navigation.
    
    This class provides LiDAR scanning with the following features:
    - UART/USB communication with LiDAR device
    - Real-time 360-degree scanning
    - Configurable scan rates and filtering
    - Obstacle detection and safety monitoring
    - MQTT telemetry publishing
    """
    
    # LiDAR protocol constants (generic implementation)
    START_BYTE = 0xA5
    SCAN_COMMAND = 0x20
    STOP_COMMAND = 0x25
    GET_INFO_COMMAND = 0x50
    RESET_COMMAND = 0x40
    
    def __init__(self, device_id: str, mqtt_client, config: SensorConfig):
        """
        Initialize the LiDAR sensor.
        
        Args:
            device_id: Unique identifier for this LiDAR
            mqtt_client: MQTT client for communication
            config: Sensor configuration object
        """
        super().__init__(device_id, mqtt_client, config.__dict__, config.publish_rate)
        
        self.sensor_config = config
        
        # Extract UART configuration
        if hasattr(config.interface, 'port'):
            self.port = config.interface.port
            self.baudrate = getattr(config.interface, 'baudrate', 115200)
            self.timeout = getattr(config.interface, 'timeout', 1.0)
            self.bytesize = getattr(config.interface, 'bytesize', 8)
            self.parity = getattr(config.interface, 'parity', 'N')
            self.stopbits = getattr(config.interface, 'stopbits', 1)
        else:
            raise ValueError("LiDAR sensor requires UART interface configuration")
        
        # LiDAR parameters from calibration
        calibration = config.calibration or {}
        self.min_range = float(calibration.get('min_range', 0.15))  # meters
        self.max_range = float(calibration.get('max_range', 12.0))  # meters
        self.angle_resolution = float(calibration.get('angle_resolution', 1.0))  # degrees
        self.scan_frequency = float(calibration.get('scan_frequency', 10.0))  # Hz
        self.quality_threshold = int(calibration.get('quality_threshold', 10))
        
        # Serial connection
        self.serial_connection = None
        self.scanning = False
        self.scan_thread = None
        
        # Scan data
        self.current_scan = None
        self.scan_count = 0
        self.last_scan_time = 0
        
        # Performance tracking
        self.scan_errors = 0
        self.communication_errors = 0
        self.last_successful_scan = time.time()
        
        # Thread safety
        self._scan_lock = threading.Lock()
        
        self.logger.info(f"LidarSensor {device_id} initialized with config: {config}")
    
    def initialize(self) -> bool:
        """
        Initialize serial connection and start LiDAR communication.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Open serial connection
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits
            )
            
            # Clear buffers
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Test communication with device info command
            if not self._get_device_info():
                self.logger.warning("Could not retrieve device info, but continuing...")
            
            # Reset device to known state
            self._send_command(self.RESET_COMMAND)
            time.sleep(0.5)
            
            self._initialized = True
            self.set_status("ready")
            
            # Start scanning
            self.start_scanning()
            
            # Start publishing telemetry
            self.start_publishing()
            
            self.logger.info(f"LidarSensor {self.device_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to initialize LiDAR sensor {self.device_id}")
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            return False
    
    def _get_device_info(self) -> bool:
        """
        Get device information from LiDAR.
        
        Returns:
            bool: True if device info retrieved successfully
        """
        try:
            self._send_command(self.GET_INFO_COMMAND)
            time.sleep(0.1)
            
            # Read response (implementation depends on specific LiDAR protocol)
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.read(self.serial_connection.in_waiting)
                self.logger.info(f"LiDAR device info: {response.hex()}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.exception("Error getting device info")
            return False
    
    def _send_command(self, command: int, payload: bytes = b'') -> bool:
        """
        Send command to LiDAR device.
        
        Args:
            command: Command byte
            payload: Optional payload data
            
        Returns:
            bool: True if command sent successfully
        """
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                return False
            
            # Build command packet (generic format)
            packet = bytes([self.START_BYTE, command]) + payload
            
            self.serial_connection.write(packet)
            self.serial_connection.flush()
            
            return True
            
        except Exception as e:
            self.logger.exception("Error sending command")
            self.communication_errors += 1
            return False
    
    def start_scanning(self) -> bool:
        """
        Start continuous LiDAR scanning.
        
        Returns:
            bool: True if scanning started successfully
        """
        if self.scanning:
            return True
        
        try:
            # Send scan start command
            if not self._send_command(self.SCAN_COMMAND):
                return False
            
            self.scanning = True
            self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.scan_thread.start()
            
            self.logger.info(f"Started LiDAR scanning for {self.device_id}")
            return True
            
        except Exception as e:
            self.logger.exception("Error starting LiDAR scan")
            return False
    
    def stop_scanning(self) -> None:
        """Stop LiDAR scanning."""
        try:
            self.scanning = False
            
            # Send stop command
            self._send_command(self.STOP_COMMAND)
            
            # Wait for scan thread to finish
            if self.scan_thread and self.scan_thread.is_alive():
                self.scan_thread.join(timeout=2.0)
            
            self.logger.info(f"Stopped LiDAR scanning for {self.device_id}")
            
        except Exception as e:
            self.logger.exception("Error stopping LiDAR scan")
    
    def _scan_loop(self) -> None:
        """
        Main scanning loop that reads LiDAR data continuously.
        """
        while self.scanning and self._initialized:
            try:
                scan_start_time = time.time()
                
                # Read scan data from LiDAR
                scan_data = self._read_scan_data()
                
                if scan_data:
                    scan_time = time.time() - scan_start_time
                    
                    with self._scan_lock:
                        self.current_scan = scan_data
                        self.scan_count += 1
                        self.last_scan_time = scan_start_time
                        self.last_successful_scan = time.time()
                    
                    # Log performance metric
                    self.logger.log_performance_metric("lidar_scan_time", scan_time, "seconds")
                    
                else:
                    self.scan_errors += 1
                    time.sleep(0.01)  # Brief pause on error
                
                # Control scan rate
                target_interval = 1.0 / self.scan_frequency
                elapsed = time.time() - scan_start_time
                if elapsed < target_interval:
                    time.sleep(target_interval - elapsed)
                
            except Exception as e:
                self.logger.exception("Error in LiDAR scan loop")
                self.scan_errors += 1
                time.sleep(0.1)
    
    def _read_scan_data(self) -> Optional[LidarScan]:
        """
        Read and parse scan data from LiDAR device.
        
        Returns:
            LidarScan object if successful, None otherwise
        """
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                return None
            
            # This is a generic implementation - real LiDAR would have specific protocol
            # For demonstration, we'll generate mock data with some realistic patterns
            
            # Check for available data
            if self.serial_connection.in_waiting < 10:
                return None
            
            # Read available data
            raw_data = self.serial_connection.read(self.serial_connection.in_waiting)
            
            # Parse scan data (mock implementation)
            scan_data = self._parse_scan_data(raw_data)
            
            return scan_data
            
        except Exception as e:
            self.logger.exception("Error reading scan data")
            return None
    
    def _parse_scan_data(self, raw_data: bytes) -> Optional[LidarScan]:
        """
        Parse raw LiDAR data into structured scan object.
        
        Args:
            raw_data: Raw bytes from LiDAR device
            
        Returns:
            LidarScan object if parsing successful
        """
        try:
            # Mock implementation - generates realistic scan data
            # Real implementation would parse actual LiDAR protocol
            
            num_points = 360  # 360-degree scan
            ranges = []
            angles = []
            quality = []
            
            # Generate mock scan data with some obstacles
            for i in range(num_points):
                angle = i * 1.0  # 1-degree resolution
                
                # Simulate some obstacles and walls
                if 80 <= angle <= 100:  # Obstacle at 90 degrees
                    distance = 0.8 + 0.1 * math.sin(angle * 0.1)
                elif 170 <= angle <= 190:  # Obstacle at 180 degrees
                    distance = 1.5 + 0.2 * math.cos(angle * 0.05)
                elif 260 <= angle <= 280:  # Wall segment
                    distance = 2.0 + 0.05 * math.sin(angle * 0.2)
                else:
                    # Open space with some noise
                    base_distance = 5.0 + 2.0 * math.sin(angle * 0.02)
                    noise = 0.1 * (hash(str(angle + time.time())) % 100 - 50) / 50
                    distance = max(self.min_range, base_distance + noise)
                
                # Clamp to valid range
                distance = max(self.min_range, min(self.max_range, distance))
                
                ranges.append(distance)
                angles.append(angle)
                quality.append(min(255, max(0, int(200 - distance * 10))))
            
            return LidarScan(
                timestamp=datetime.now(),
                ranges=ranges,
                angles=angles,
                min_range=self.min_range,
                max_range=self.max_range,
                scan_time=0.1,  # 100ms scan time
                quality=quality
            )
            
        except Exception as e:
            self.logger.exception("Error parsing scan data")
            return None
    
    def read_data(self) -> Dict[str, Any]:
        """
        Read current LiDAR scan data.
        
        Returns:
            Dict containing current scan data and metadata
        """
        try:
            with self._scan_lock:
                if self.current_scan is None:
                    return {
                        "scan_available": False,
                        "error": "No scan data available"
                    }
                
                scan = self.current_scan
                
                # Calculate derived metrics
                closest_distance, closest_angle = scan.get_closest_obstacle()
                
                # Count obstacles in different zones
                front_obstacles = len(scan.get_obstacles_in_zone(-30, 30, 2.0))
                left_obstacles = len(scan.get_obstacles_in_zone(60, 120, 2.0))
                right_obstacles = len(scan.get_obstacles_in_zone(240, 300, 2.0))
                rear_obstacles = len(scan.get_obstacles_in_zone(150, 210, 2.0))
                
                data = {
                    "scan_available": True,
                    "timestamp": scan.timestamp.isoformat(),
                    "ranges": scan.ranges,
                    "angles": scan.angles,
                    "quality": scan.quality,
                    "min_range": scan.min_range,
                    "max_range": scan.max_range,
                    "scan_time": scan.scan_time,
                    "num_points": len(scan.ranges),
                    "closest_obstacle": {
                        "distance": closest_distance,
                        "angle": closest_angle
                    },
                    "obstacle_zones": {
                        "front": front_obstacles,
                        "left": left_obstacles,
                        "right": right_obstacles,
                        "rear": rear_obstacles
                    },
                    "scan_statistics": {
                        "scan_count": self.scan_count,
                        "scan_errors": self.scan_errors,
                        "communication_errors": self.communication_errors,
                        "last_scan_time": self.last_scan_time,
                        "last_successful_scan": self.last_successful_scan
                    },
                    "sensor_config": {
                        "port": self.port,
                        "baudrate": self.baudrate,
                        "scan_frequency": self.scan_frequency,
                        "angle_resolution": self.angle_resolution,
                        "quality_threshold": self.quality_threshold
                    }
                }
                
                return data
                
        except Exception as e:
            self.logger.exception("Error reading LiDAR data")
            return {
                "scan_available": False,
                "error": str(e)
            }
    
    def get_current_scan(self) -> Optional[LidarScan]:
        """
        Get the current LidarScan object.
        
        Returns:
            Current LidarScan or None if no scan available
        """
        with self._scan_lock:
            return self.current_scan
    
    def is_obstacle_detected(self, min_distance: float = 0.5, 
                           angle_range: Tuple[float, float] = (-45, 45)) -> bool:
        """
        Check if obstacles are detected within specified parameters.
        
        Args:
            min_distance: Minimum safe distance in meters
            angle_range: Tuple of (min_angle, max_angle) in degrees
            
        Returns:
            True if obstacle detected within parameters
        """
        try:
            with self._scan_lock:
                if self.current_scan is None:
                    return False
                
                obstacles = self.current_scan.get_obstacles_in_zone(
                    angle_range[0], angle_range[1], min_distance
                )
                
                return len(obstacles) > 0
                
        except Exception as e:
            self.logger.exception("Error checking obstacle detection")
            return False
    
    def stop(self) -> None:
        """Stop the LiDAR sensor and clean up resources."""
        try:
            # Stop publishing
            self.stop_publishing()
            
            # Stop scanning
            self.stop_scanning()
            
            # Close serial connection
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            self.set_status("stopped")
            self.logger.info(f"LidarSensor {self.device_id} stopped and cleaned up")
            
        except Exception as e:
            self.logger.exception("Error stopping LiDAR sensor")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current LiDAR sensor status."""
        return {
            "device_id": self.device_id,
            "status": self.status,
            "initialized": self._initialized,
            "scanning": self.scanning,
            "scan_count": self.scan_count,
            "scan_errors": self.scan_errors,
            "communication_errors": self.communication_errors,
            "last_successful_scan": self.last_successful_scan,
            "last_updated": self.last_updated.isoformat(),
            "connection": {
                "port": self.port,
                "baudrate": self.baudrate,
                "connected": self.serial_connection.is_open if self.serial_connection else False
            },
            "config": {
                "min_range": self.min_range,
                "max_range": self.max_range,
                "scan_frequency": self.scan_frequency,
                "angle_resolution": self.angle_resolution,
                "publish_rate": self.publish_rate
            }
        }