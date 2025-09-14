#!/usr/bin/env python3
"""
LiDAR Sensor Example for Orchestrator Platform

This example demonstrates how to use the LidarSensor class for 2D scanning,
obstacle detection, and real-time monitoring.

Usage:
    python lidar_example.py [config_file]
"""

import sys
import time
import signal
import json
from pathlib import Path

# Add the parent directory to the path so we can import hal_service modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hal_service.lidar_sensor import LidarSensor
from hal_service.mqtt_client import MQTTClientWrapper, MQTTConfig
from hal_service.config import ConfigurationService, SensorConfig, UARTConfig
from hal_service.logging_service import get_logging_service


class LidarExample:
    """
    Example application demonstrating LiDAR sensor usage.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the LiDAR example.
        
        Args:
            config_path: Path to configuration file
        """
        self.running = False
        self.lidar_sensor = None
        self.mqtt_client = None
        
        # Setup logging
        logging_service = get_logging_service()
        self.logger = logging_service.get_service_logger("lidar_example")
        
        # Load configuration
        try:
            config_service = ConfigurationService(config_path)
            self.config = config_service.load_config()
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Create default configuration for demonstration
            self.config = self._create_default_config()
    
    def _create_default_config(self):
        """Create a default configuration for demonstration."""
        from hal_service.config import OrchestratorConfig, MQTTConfig as ConfigMQTT, SensorConfig
        
        # Create UART interface config
        uart_config = UARTConfig(
            port="/dev/ttyUSB0",
            baudrate=115200,
            timeout=1.0
        )
        
        # Create LiDAR sensor config
        lidar_config = SensorConfig(
            name="lidar_01",
            type="lidar",
            interface=uart_config,
            publish_rate=10.0,
            calibration={
                "min_range": 0.15,
                "max_range": 12.0,
                "angle_resolution": 1.0,
                "scan_frequency": 10.0,
                "quality_threshold": 10
            }
        )
        
        # Create minimal config
        config = OrchestratorConfig(
            mqtt=ConfigMQTT(),
            sensors=[lidar_config]
        )
        
        return config
    
    def setup_mqtt(self):
        """Setup MQTT client connection."""
        try:
            mqtt_config = MQTTConfig(
                broker_host=self.config.mqtt.broker_host,
                broker_port=self.config.mqtt.broker_port,
                client_id="lidar_example",
                username=getattr(self.config.mqtt, 'username', None),
                password=getattr(self.config.mqtt, 'password', None)
            )
            
            self.mqtt_client = MQTTClientWrapper(mqtt_config)
            
            # Add connection callback
            self.mqtt_client.add_connection_callback(
                "example", 
                self._on_mqtt_connection_change
            )
            
            # Connect to broker
            if self.mqtt_client.connect():
                self.logger.info("Connected to MQTT broker")
                return True
            else:
                self.logger.error("Failed to connect to MQTT broker")
                return False
                
        except Exception as e:
            self.logger.exception("Error setting up MQTT client")
            return False
    
    def _on_mqtt_connection_change(self, connected: bool):
        """Handle MQTT connection status changes."""
        if connected:
            self.logger.info("MQTT connection established")
        else:
            self.logger.warning("MQTT connection lost")
    
    def setup_lidar(self):
        """Setup LiDAR sensor."""
        try:
            # Get LiDAR configuration
            lidar_config = None
            for sensor in self.config.sensors:
                if sensor.type == "lidar":
                    lidar_config = sensor
                    break
            
            if not lidar_config:
                self.logger.error("No LiDAR sensor configuration found")
                return False
            
            # Create LiDAR sensor
            self.lidar_sensor = LidarSensor(
                device_id=lidar_config.name,
                mqtt_client=self.mqtt_client,
                config=lidar_config
            )
            
            # Initialize sensor
            if self.lidar_sensor.initialize():
                self.logger.info("LiDAR sensor initialized successfully")
                return True
            else:
                self.logger.error("Failed to initialize LiDAR sensor")
                return False
                
        except Exception as e:
            self.logger.exception("Error setting up LiDAR sensor")
            return False
    
    def run_monitoring_loop(self):
        """Run the main monitoring loop."""
        self.logger.info("Starting LiDAR monitoring loop...")
        
        obstacle_detection_enabled = True
        safety_distance = 0.5  # meters
        
        try:
            while self.running:
                # Get current scan data
                scan_data = self.lidar_sensor.read_data()
                
                if scan_data.get("scan_available"):
                    # Display scan summary
                    self._display_scan_summary(scan_data)
                    
                    # Check for obstacles if enabled
                    if obstacle_detection_enabled:
                        self._check_obstacles(scan_data, safety_distance)
                    
                    # Log performance metrics
                    self._log_performance_metrics(scan_data)
                
                else:
                    self.logger.warning("No scan data available")
                
                # Wait before next iteration
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring loop interrupted by user")
        except Exception as e:
            self.logger.exception("Error in monitoring loop")
    
    def _display_scan_summary(self, scan_data: dict):
        """Display a summary of the current scan."""
        try:
            closest = scan_data.get("closest_obstacle", {})
            zones = scan_data.get("obstacle_zones", {})
            stats = scan_data.get("scan_statistics", {})
            
            print(f"\n--- LiDAR Scan Summary ---")
            print(f"Timestamp: {scan_data.get('timestamp', 'N/A')}")
            print(f"Points: {scan_data.get('num_points', 0)}")
            print(f"Scan Time: {scan_data.get('scan_time', 0):.3f}s")
            
            print(f"\nClosest Obstacle:")
            print(f"  Distance: {closest.get('distance', float('inf')):.2f}m")
            print(f"  Angle: {closest.get('angle', 0):.1f}°")
            
            print(f"\nObstacle Zones:")
            print(f"  Front: {zones.get('front', 0)} obstacles")
            print(f"  Left: {zones.get('left', 0)} obstacles")
            print(f"  Right: {zones.get('right', 0)} obstacles")
            print(f"  Rear: {zones.get('rear', 0)} obstacles")
            
            print(f"\nStatistics:")
            print(f"  Total Scans: {stats.get('scan_count', 0)}")
            print(f"  Scan Errors: {stats.get('scan_errors', 0)}")
            print(f"  Comm Errors: {stats.get('communication_errors', 0)}")
            
        except Exception as e:
            self.logger.exception("Error displaying scan summary")
    
    def _check_obstacles(self, scan_data: dict, safety_distance: float):
        """Check for obstacles and issue warnings."""
        try:
            closest = scan_data.get("closest_obstacle", {})
            closest_distance = closest.get("distance", float('inf'))
            closest_angle = closest.get("angle", 0)
            
            if closest_distance < safety_distance:
                self.logger.warning(
                    f"OBSTACLE DETECTED! Distance: {closest_distance:.2f}m, "
                    f"Angle: {closest_angle:.1f}°"
                )
                
                # Check if obstacle is in critical front zone
                if -30 <= closest_angle <= 30:
                    self.logger.error("CRITICAL: Obstacle in front zone!")
            
            # Check specific zones
            zones = scan_data.get("obstacle_zones", {})
            front_obstacles = zones.get("front", 0)
            
            if front_obstacles > 3:
                self.logger.warning(f"Multiple obstacles in front zone: {front_obstacles}")
                
        except Exception as e:
            self.logger.exception("Error checking obstacles")
    
    def _log_performance_metrics(self, scan_data: dict):
        """Log performance metrics."""
        try:
            stats = scan_data.get("scan_statistics", {})
            
            # Log every 10 scans
            scan_count = stats.get("scan_count", 0)
            if scan_count % 10 == 0:
                scan_errors = stats.get("scan_errors", 0)
                comm_errors = stats.get("communication_errors", 0)
                
                error_rate = (scan_errors + comm_errors) / max(scan_count, 1) * 100
                
                self.logger.info(
                    f"Performance: {scan_count} scans, "
                    f"{error_rate:.1f}% error rate"
                )
                
        except Exception as e:
            self.logger.exception("Error logging performance metrics")
    
    def run_interactive_mode(self):
        """Run interactive mode with user commands."""
        self.logger.info("Starting interactive mode. Type 'help' for commands.")
        
        try:
            while self.running:
                try:
                    command = input("\nlidar> ").strip().lower()
                    
                    if command == "help":
                        self._show_help()
                    elif command == "status":
                        self._show_status()
                    elif command == "scan":
                        self._show_current_scan()
                    elif command == "obstacles":
                        self._show_obstacles()
                    elif command == "config":
                        self._show_config()
                    elif command == "quit" or command == "exit":
                        break
                    elif command == "":
                        continue
                    else:
                        print(f"Unknown command: {command}. Type 'help' for available commands.")
                        
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            self.logger.exception("Error in interactive mode")
    
    def _show_help(self):
        """Show available commands."""
        print("\nAvailable commands:")
        print("  help      - Show this help message")
        print("  status    - Show sensor status")
        print("  scan      - Show current scan data")
        print("  obstacles - Show obstacle detection info")
        print("  config    - Show sensor configuration")
        print("  quit/exit - Exit the program")
    
    def _show_status(self):
        """Show sensor status."""
        try:
            if self.lidar_sensor:
                status = self.lidar_sensor.get_status()
                print(f"\nLiDAR Sensor Status:")
                print(f"  Device ID: {status.get('device_id')}")
                print(f"  Status: {status.get('status')}")
                print(f"  Initialized: {status.get('initialized')}")
                print(f"  Scanning: {status.get('scanning')}")
                print(f"  Scan Count: {status.get('scan_count')}")
                print(f"  Scan Errors: {status.get('scan_errors')}")
                
                connection = status.get('connection', {})
                print(f"  Port: {connection.get('port')}")
                print(f"  Baudrate: {connection.get('baudrate')}")
                print(f"  Connected: {connection.get('connected')}")
            else:
                print("LiDAR sensor not initialized")
                
        except Exception as e:
            print(f"Error getting status: {e}")
    
    def _show_current_scan(self):
        """Show current scan data."""
        try:
            if self.lidar_sensor:
                scan_data = self.lidar_sensor.read_data()
                if scan_data.get("scan_available"):
                    self._display_scan_summary(scan_data)
                else:
                    print("No scan data available")
            else:
                print("LiDAR sensor not initialized")
                
        except Exception as e:
            print(f"Error getting scan data: {e}")
    
    def _show_obstacles(self):
        """Show obstacle detection information."""
        try:
            if self.lidar_sensor:
                # Check for obstacles in different zones
                front_obstacle = self.lidar_sensor.is_obstacle_detected(1.0, (-30, 30))
                left_obstacle = self.lidar_sensor.is_obstacle_detected(1.0, (60, 120))
                right_obstacle = self.lidar_sensor.is_obstacle_detected(1.0, (240, 300))
                rear_obstacle = self.lidar_sensor.is_obstacle_detected(1.0, (150, 210))
                
                print(f"\nObstacle Detection (within 1.0m):")
                print(f"  Front (-30° to 30°): {'YES' if front_obstacle else 'NO'}")
                print(f"  Left (60° to 120°): {'YES' if left_obstacle else 'NO'}")
                print(f"  Right (240° to 300°): {'YES' if right_obstacle else 'NO'}")
                print(f"  Rear (150° to 210°): {'YES' if rear_obstacle else 'NO'}")
                
                # Get current scan for detailed info
                scan_data = self.lidar_sensor.read_data()
                if scan_data.get("scan_available"):
                    closest = scan_data.get("closest_obstacle", {})
                    print(f"\nClosest Obstacle:")
                    print(f"  Distance: {closest.get('distance', float('inf')):.2f}m")
                    print(f"  Angle: {closest.get('angle', 0):.1f}°")
            else:
                print("LiDAR sensor not initialized")
                
        except Exception as e:
            print(f"Error checking obstacles: {e}")
    
    def _show_config(self):
        """Show sensor configuration."""
        try:
            if self.lidar_sensor:
                status = self.lidar_sensor.get_status()
                config = status.get('config', {})
                
                print(f"\nLiDAR Configuration:")
                print(f"  Min Range: {config.get('min_range')}m")
                print(f"  Max Range: {config.get('max_range')}m")
                print(f"  Scan Frequency: {config.get('scan_frequency')}Hz")
                print(f"  Publish Rate: {config.get('publish_rate')}Hz")
                
                connection = status.get('connection', {})
                print(f"  Port: {connection.get('port')}")
                print(f"  Baudrate: {connection.get('baudrate')}")
            else:
                print("LiDAR sensor not initialized")
                
        except Exception as e:
            print(f"Error getting configuration: {e}")
    
    def start(self, interactive: bool = False):
        """Start the LiDAR example application."""
        self.logger.info("Starting LiDAR example application...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Setup MQTT
            if not self.setup_mqtt():
                return False
            
            # Setup LiDAR
            if not self.setup_lidar():
                return False
            
            self.running = True
            
            if interactive:
                self.run_interactive_mode()
            else:
                self.run_monitoring_loop()
            
            return True
            
        except Exception as e:
            self.logger.exception("Error starting application")
            return False
        finally:
            self.stop()
    
    def stop(self):
        """Stop the application and clean up resources."""
        self.logger.info("Stopping LiDAR example application...")
        
        self.running = False
        
        # Stop LiDAR sensor
        if self.lidar_sensor:
            self.lidar_sensor.stop()
        
        # Disconnect MQTT
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        self.logger.info("Application stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LiDAR Sensor Example")
    parser.add_argument(
        "config", 
        nargs="?", 
        help="Path to configuration file"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    # Create and run example
    example = LidarExample(args.config)
    
    try:
        success = example.start(interactive=args.interactive)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()