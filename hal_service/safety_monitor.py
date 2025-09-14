"""
Standalone Safety Subsystem for Orchestrator Platform

This module implements a dedicated, high-priority safety monitoring process that
continuously monitors sensor data for hazardous conditions and triggers emergency
stops when necessary.

Requirements covered: 5.1, 5.2, 5.3, 5.4
"""

import json
import time
import signal
import sys
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

from .mqtt_client import MQTTClientWrapper, MQTTConfig
from .config import load_config, SafetyConfig
from .logging_service import get_logging_service


@dataclass
class SafetyZone:
    """Definition of a safety zone for obstacle detection."""
    name: str
    min_angle: float  # degrees
    max_angle: float  # degrees
    min_distance: float  # meters
    priority: int  # 1=highest, 5=lowest
    action: str  # "stop", "slow", "warn"


@dataclass
class ObstacleDetection:
    """Information about a detected obstacle."""
    timestamp: datetime
    distance: float
    angle: float
    zone: str
    severity: str  # "critical", "warning", "info"


class SafetyMonitor:
    """
    Standalone safety monitoring system for the Orchestrator platform.
    
    This class implements a high-priority safety subsystem that:
    - Continuously monitors LiDAR sensor data
    - Detects obstacles within configurable safety zones
    - Triggers immediate emergency stops when critical obstacles are detected
    - Maintains safety event logs and statistics
    - Operates independently of other system components
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the safety monitor.
        
        Args:
            config_path: Path to configuration file, or None for default
        """
        # Load configuration
        self.config = load_config(config_path)
        self.safety_config = self.config.safety
        
        # Initialize logging
        logging_service = get_logging_service()
        self.logger = logging_service.get_device_logger("safety_monitor")
        
        # MQTT configuration
        mqtt_config = MQTTConfig(
            broker_host=self.config.mqtt.broker_host,
            broker_port=self.config.mqtt.broker_port,
            client_id="safety_monitor",
            username=getattr(self.config.mqtt, 'username', None),
            password=getattr(self.config.mqtt, 'password', None),
            keepalive=self.config.mqtt.keepalive
        )
        
        self.mqtt_client = MQTTClientWrapper(mqtt_config)
        
        # Safety state
        self.running = False
        self.emergency_stop_active = False
        self.last_lidar_data = None
        self.last_lidar_timestamp = None
        
        # Safety zones configuration
        self.safety_zones = self._initialize_safety_zones()
        
        # Statistics and monitoring
        self.obstacle_detections = []
        self.emergency_stops_triggered = 0
        self.false_positives = 0
        self.system_start_time = datetime.now()
        
        # Thread safety
        self._data_lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # Performance monitoring
        self.processing_times = []
        self.max_processing_time = 0.0
        self.avg_processing_time = 0.0
        
        self.logger.info("Safety monitor initialized")
    
    def _initialize_safety_zones(self) -> List[SafetyZone]:
        """
        Initialize safety zones from configuration.
        
        Returns:
            List of configured safety zones
        """
        zones = []
        
        # Default critical front zone
        zones.append(SafetyZone(
            name="critical_front",
            min_angle=-45.0,
            max_angle=45.0,
            min_distance=self.safety_config.obstacle_threshold,
            priority=1,
            action="stop"
        ))
        
        # Default warning side zones
        zones.append(SafetyZone(
            name="warning_left",
            min_angle=45.0,
            max_angle=135.0,
            min_distance=self.safety_config.obstacle_threshold * 0.7,
            priority=2,
            action="slow"
        ))
        
        zones.append(SafetyZone(
            name="warning_right",
            min_angle=225.0,
            max_angle=315.0,
            min_distance=self.safety_config.obstacle_threshold * 0.7,
            priority=2,
            action="slow"
        ))
        
        # Add configured zones from config if available
        if hasattr(self.safety_config, 'safety_zones'):
            for zone_config in self.safety_config.safety_zones:
                zones.append(SafetyZone(
                    name=zone_config.get('name', 'custom'),
                    min_angle=zone_config.get('min_angle', 0.0),
                    max_angle=zone_config.get('max_angle', 360.0),
                    min_distance=zone_config.get('min_distance', 0.5),
                    priority=zone_config.get('priority', 3),
                    action=zone_config.get('action', 'warn')
                ))
        
        self.logger.info(f"Initialized {len(zones)} safety zones")
        return zones
    
    def start(self) -> bool:
        """
        Start the safety monitoring system.
        
        Returns:
            bool: True if started successfully
        """
        try:
            if self.running:
                self.logger.warning("Safety monitor already running")
                return True
            
            # Connect to MQTT broker
            if not self.mqtt_client.connect():
                self.logger.error("Failed to connect to MQTT broker")
                return False
            
            # Subscribe to LiDAR data
            lidar_topic = "orchestrator/data/lidar_01"  # From config
            if not self.mqtt_client.subscribe(lidar_topic, self._handle_lidar_data):
                self.logger.error(f"Failed to subscribe to {lidar_topic}")
                return False
            
            # Subscribe to system status for coordination
            status_topic = "orchestrator/status/+"
            self.mqtt_client.subscribe(status_topic, self._handle_status_update)
            
            self.running = True
            self._stop_event.clear()
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            # Start watchdog thread
            self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            self.watchdog_thread.start()
            
            self.logger.info("Safety monitor started successfully")
            
            # Publish initial status
            self._publish_safety_status("active", "Safety monitor started")
            
            return True
            
        except Exception as e:
            self.logger.exception("Failed to start safety monitor")
            return False
    
    def stop(self) -> None:
        """Stop the safety monitoring system."""
        try:
            if not self.running:
                return
            
            self.logger.info("Stopping safety monitor...")
            
            self.running = False
            self._stop_event.set()
            
            # Wait for threads to finish
            if hasattr(self, 'monitor_thread'):
                self.monitor_thread.join(timeout=2.0)
            if hasattr(self, 'watchdog_thread'):
                self.watchdog_thread.join(timeout=2.0)
            
            # Disconnect MQTT
            self.mqtt_client.disconnect()
            
            # Publish final status
            self._publish_safety_status("stopped", "Safety monitor stopped")
            
            self.logger.info("Safety monitor stopped")
            
        except Exception as e:
            self.logger.exception("Error stopping safety monitor")
    
    def _handle_lidar_data(self, message_data: Dict[str, Any]) -> None:
        """
        Handle incoming LiDAR sensor data.
        
        Args:
            message_data: MQTT message containing LiDAR scan data
        """
        try:
            payload = message_data['payload']
            
            # Extract LiDAR scan data
            if 'data' not in payload:
                self.logger.warning("No data field in LiDAR message")
                return
            
            lidar_data = payload['data']
            
            # Validate required fields
            required_fields = ['ranges', 'angles', 'timestamp']
            for field in required_fields:
                if field not in lidar_data:
                    self.logger.warning(f"Missing required field in LiDAR data: {field}")
                    return
            
            # Update current data with thread safety
            with self._data_lock:
                self.last_lidar_data = lidar_data
                self.last_lidar_timestamp = datetime.fromisoformat(
                    lidar_data['timestamp'].replace('Z', '+00:00')
                )
            
            # Process data immediately for critical safety
            self._process_lidar_data(lidar_data)
            
        except Exception as e:
            self.logger.exception("Error handling LiDAR data")
    
    def _handle_status_update(self, message_data: Dict[str, Any]) -> None:
        """
        Handle system status updates for coordination.
        
        Args:
            message_data: MQTT message containing status update
        """
        try:
            topic = message_data['topic']
            payload = message_data['payload']
            
            # Monitor for emergency stop acknowledgments
            if 'estop' in topic.lower() and payload.get('status') == 'acknowledged':
                self.logger.info("Emergency stop acknowledged by system")
                
        except Exception as e:
            self.logger.exception("Error handling status update")
    
    def _process_lidar_data(self, lidar_data: Dict[str, Any]) -> None:
        """
        Process LiDAR data for obstacle detection and safety analysis.
        
        Args:
            lidar_data: Dictionary containing LiDAR scan data
        """
        start_time = time.time()
        
        try:
            ranges = lidar_data['ranges']
            angles = lidar_data['angles']
            
            if len(ranges) != len(angles):
                self.logger.warning("Mismatched ranges and angles in LiDAR data")
                return
            
            # Check each safety zone for obstacles
            critical_obstacles = []
            warning_obstacles = []
            
            for zone in self.safety_zones:
                obstacles = self._check_zone_for_obstacles(zone, ranges, angles)
                
                if obstacles:
                    for obstacle in obstacles:
                        detection = ObstacleDetection(
                            timestamp=datetime.now(),
                            distance=obstacle[0],
                            angle=obstacle[1],
                            zone=zone.name,
                            severity="critical" if zone.action == "stop" else "warning"
                        )
                        
                        if zone.action == "stop":
                            critical_obstacles.append(detection)
                        else:
                            warning_obstacles.append(detection)
            
            # Handle critical obstacles immediately
            if critical_obstacles:
                self._trigger_emergency_stop(critical_obstacles)
            
            # Log warning obstacles
            for obstacle in warning_obstacles:
                self.logger.warning(
                    f"Warning obstacle detected in {obstacle.zone}: "
                    f"{obstacle.distance:.2f}m at {obstacle.angle:.1f}°"
                )
            
            # Update statistics
            self.obstacle_detections.extend(critical_obstacles + warning_obstacles)
            
            # Limit detection history
            if len(self.obstacle_detections) > 1000:
                self.obstacle_detections = self.obstacle_detections[-500:]
            
        except Exception as e:
            self.logger.exception("Error processing LiDAR data")
        
        finally:
            # Track processing performance
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            if len(self.processing_times) > 100:
                self.processing_times = self.processing_times[-50:]
            
            self.max_processing_time = max(self.max_processing_time, processing_time)
            self.avg_processing_time = sum(self.processing_times) / len(self.processing_times)
            
            # Log performance warning if processing is too slow
            if processing_time > self.safety_config.emergency_stop_timeout * 0.5:
                self.logger.warning(
                    f"Slow safety processing: {processing_time:.3f}s "
                    f"(threshold: {self.safety_config.emergency_stop_timeout:.3f}s)"
                )
    
    def _check_zone_for_obstacles(self, zone: SafetyZone, ranges: List[float], 
                                 angles: List[float]) -> List[Tuple[float, float]]:
        """
        Check a specific safety zone for obstacles.
        
        Args:
            zone: Safety zone to check
            ranges: List of distance measurements
            angles: List of angle measurements
            
        Returns:
            List of (distance, angle) tuples for obstacles in the zone
        """
        obstacles = []
        
        for distance, angle in zip(ranges, angles):
            # Normalize angle to 0-360 range
            normalized_angle = angle % 360
            
            # Check if point is within zone angular range
            in_zone = False
            if zone.min_angle <= zone.max_angle:
                # Normal case: zone doesn't cross 0°
                in_zone = zone.min_angle <= normalized_angle <= zone.max_angle
            else:
                # Zone crosses 0° (e.g., 350° to 10°)
                in_zone = (normalized_angle >= zone.min_angle or 
                          normalized_angle <= zone.max_angle)
            
            # Check if obstacle is within minimum safe distance
            if in_zone and 0.1 <= distance <= zone.min_distance:
                obstacles.append((distance, angle))
        
        return obstacles
    
    def _trigger_emergency_stop(self, obstacles: List[ObstacleDetection]) -> None:
        """
        Trigger an emergency stop due to critical obstacles.
        
        Args:
            obstacles: List of critical obstacle detections
        """
        try:
            if self.emergency_stop_active:
                # Already in emergency stop, just log
                self.logger.debug("Emergency stop already active")
                return
            
            self.emergency_stop_active = True
            self.emergency_stops_triggered += 1
            
            # Find closest obstacle for reporting
            closest_obstacle = min(obstacles, key=lambda x: x.distance)
            
            # Create emergency stop command
            estop_command = {
                "timestamp": datetime.now().isoformat(),
                "command_id": f"safety_estop_{int(time.time())}",
                "action": "emergency_stop",
                "reason": "obstacle_detected",
                "source": "safety_monitor",
                "obstacle_info": {
                    "distance": closest_obstacle.distance,
                    "angle": closest_obstacle.angle,
                    "zone": closest_obstacle.zone,
                    "total_obstacles": len(obstacles)
                },
                "parameters": {
                    "immediate": True,
                    "timeout": self.safety_config.emergency_stop_timeout
                }
            }
            
            # Publish emergency stop command with high priority
            estop_topic = "orchestrator/cmd/estop"
            success = self.mqtt_client.publish(estop_topic, estop_command, qos=1)
            
            if success:
                self.logger.critical(
                    f"EMERGENCY STOP TRIGGERED: Obstacle at {closest_obstacle.distance:.2f}m "
                    f"in {closest_obstacle.zone} zone (angle: {closest_obstacle.angle:.1f}°)"
                )
                
                # Publish safety status
                self._publish_safety_status(
                    "emergency_stop",
                    f"Emergency stop triggered: obstacle at {closest_obstacle.distance:.2f}m"
                )
                
                # Log all obstacles for analysis
                for obstacle in obstacles:
                    self.logger.error(
                        f"Critical obstacle: {obstacle.distance:.2f}m at {obstacle.angle:.1f}° "
                        f"in {obstacle.zone}"
                    )
            else:
                self.logger.error("FAILED TO PUBLISH EMERGENCY STOP COMMAND!")
                
        except Exception as e:
            self.logger.exception("Error triggering emergency stop")
    
    def _publish_safety_status(self, status: str, message: str) -> None:
        """
        Publish safety system status.
        
        Args:
            status: Current safety status
            message: Status message
        """
        try:
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "device_id": "safety_monitor",
                "status": status,
                "message": message,
                "statistics": {
                    "uptime_seconds": (datetime.now() - self.system_start_time).total_seconds(),
                    "emergency_stops_triggered": self.emergency_stops_triggered,
                    "total_detections": len(self.obstacle_detections),
                    "avg_processing_time_ms": self.avg_processing_time * 1000,
                    "max_processing_time_ms": self.max_processing_time * 1000
                },
                "configuration": {
                    "obstacle_threshold": self.safety_config.obstacle_threshold,
                    "emergency_stop_timeout": self.safety_config.emergency_stop_timeout,
                    "zones_configured": len(self.safety_zones)
                }
            }
            
            topic = "orchestrator/status/safety_monitor"
            self.mqtt_client.publish(topic, status_data)
            
        except Exception as e:
            self.logger.exception("Error publishing safety status")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop for periodic safety checks."""
        while self.running and not self._stop_event.is_set():
            try:
                # Check for data timeout
                self._check_data_timeout()
                
                # Publish periodic status
                self._publish_safety_status("monitoring", "Safety monitor active")
                
                # Reset emergency stop if conditions are clear
                self._check_emergency_stop_reset()
                
                # Sleep for monitoring interval
                self._stop_event.wait(5.0)  # 5-second monitoring cycle
                
            except Exception as e:
                self.logger.exception("Error in monitoring loop")
                time.sleep(1.0)
    
    def _watchdog_loop(self) -> None:
        """Watchdog loop to ensure system responsiveness."""
        while self.running and not self._stop_event.is_set():
            try:
                # Check if processing times are within acceptable limits
                if self.avg_processing_time > self.safety_config.emergency_stop_timeout:
                    self.logger.error(
                        f"Safety processing too slow: {self.avg_processing_time:.3f}s "
                        f"exceeds timeout {self.safety_config.emergency_stop_timeout:.3f}s"
                    )
                
                # Check system health
                self._check_system_health()
                
                # Watchdog interval
                self._stop_event.wait(10.0)  # 10-second watchdog cycle
                
            except Exception as e:
                self.logger.exception("Error in watchdog loop")
                time.sleep(1.0)
    
    def _check_data_timeout(self) -> None:
        """Check for LiDAR data timeout."""
        with self._data_lock:
            if self.last_lidar_timestamp is None:
                return
            
            time_since_last_data = datetime.now() - self.last_lidar_timestamp
            timeout_threshold = timedelta(seconds=2.0)  # 2-second timeout
            
            if time_since_last_data > timeout_threshold:
                self.logger.warning(
                    f"LiDAR data timeout: {time_since_last_data.total_seconds():.1f}s "
                    f"since last update"
                )
                
                # Consider triggering safety action if timeout is too long
                if time_since_last_data > timedelta(seconds=5.0):
                    self.logger.error("Critical LiDAR data timeout - safety compromised")
    
    def _check_emergency_stop_reset(self) -> None:
        """Check if emergency stop can be reset."""
        if not self.emergency_stop_active:
            return
        
        # Check if obstacles are clear for sufficient time
        with self._data_lock:
            if self.last_lidar_data is None:
                return
            
            # Simple check: no recent critical detections
            recent_critical = [
                d for d in self.obstacle_detections[-10:]  # Last 10 detections
                if d.severity == "critical" and 
                (datetime.now() - d.timestamp).total_seconds() < 3.0
            ]
            
            if not recent_critical:
                self.emergency_stop_active = False
                self.logger.info("Emergency stop condition cleared")
                self._publish_safety_status("monitoring", "Emergency stop cleared")
    
    def _check_system_health(self) -> None:
        """Perform system health checks."""
        try:
            # Check MQTT connection
            if not self.mqtt_client.is_connected:
                self.logger.error("MQTT connection lost - safety monitoring compromised")
            
            # Check memory usage (basic check)
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                self.logger.warning(f"High memory usage: {memory_percent:.1f}%")
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                self.logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                
        except ImportError:
            # psutil not available, skip system checks
            pass
        except Exception as e:
            self.logger.exception("Error checking system health")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down safety monitor...")
    if 'safety_monitor' in globals():
        safety_monitor.stop()
    sys.exit(0)


def main():
    """Main entry point for the standalone safety monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrator Safety Monitor")
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
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and start safety monitor
        global safety_monitor
        safety_monitor = SafetyMonitor(args.config)
        
        if not safety_monitor.start():
            print("Failed to start safety monitor")
            sys.exit(1)
        
        print("Safety monitor started. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while safety_monitor.running:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if 'safety_monitor' in globals():
            safety_monitor.stop()


if __name__ == "__main__":
    main()