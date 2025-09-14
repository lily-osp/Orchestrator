"""
State Management Service for Orchestrator Platform

This service subscribes to encoder data to perform odometry calculations,
tracks the robot's estimated X/Y position and heading, and publishes
the official robot state to orchestrator/status/robot.

Requirements covered: 4.3, 5.4
"""

import json
import math
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from .mqtt_client import MQTTClientWrapper, MQTTConfig
from .logging_service import get_logging_service


@dataclass
class Position:
    """Robot position in 2D space"""
    x: float = 0.0
    y: float = 0.0


@dataclass
class Velocity:
    """Robot velocity components"""
    linear: float = 0.0  # m/s forward velocity
    angular: float = 0.0  # rad/s rotational velocity


@dataclass
class RobotState:
    """Complete robot state information"""
    position: Position
    heading: float  # radians, 0 = facing positive X
    velocity: Velocity
    status: str  # active, idle, error, emergency_stop
    mission_status: str  # complete, in_progress, failed, idle
    last_updated: str
    odometry_valid: bool = True
    encoder_data: Optional[Dict[str, Any]] = None


class StateManager:
    """
    State Management Service for robot odometry and status tracking.
    
    This service:
    - Subscribes to encoder telemetry data
    - Calculates robot position and heading using differential drive odometry
    - Tracks velocity and acceleration
    - Publishes comprehensive robot state
    - Handles state transitions and error conditions
    """
    
    def __init__(self, mqtt_config: MQTTConfig, wheel_base: float = 0.3, 
                 publish_rate: float = 10.0):
        """
        Initialize the state manager.
        
        Args:
            mqtt_config: MQTT configuration for communication
            wheel_base: Distance between wheels in meters
            publish_rate: Rate to publish state updates (Hz)
        """
        self.mqtt_client = MQTTClientWrapper(mqtt_config)
        self.wheel_base = wheel_base
        self.publish_rate = publish_rate
        
        # Initialize logging
        logging_service = get_logging_service()
        self.logger = logging_service.get_device_logger("state_manager")
        
        # Robot state
        self.robot_state = RobotState(
            position=Position(),
            heading=0.0,
            velocity=Velocity(),
            status="idle",
            mission_status="idle",
            last_updated=datetime.now().isoformat()
        )
        
        # Encoder tracking
        self.left_encoder_data: Optional[Dict[str, Any]] = None
        self.right_encoder_data: Optional[Dict[str, Any]] = None
        self.last_left_distance = 0.0
        self.last_right_distance = 0.0
        self.last_update_time = time.time()
        
        # State management
        self._running = False
        self._publish_thread: Optional[threading.Thread] = None
        self._state_lock = threading.Lock()
        
        # Performance tracking
        self.update_count = 0
        self.last_encoder_update = 0.0
        
        self.logger.info(f"StateManager initialized with wheel_base={wheel_base}m, publish_rate={publish_rate}Hz")
    
    def start(self) -> bool:
        """
        Start the state management service.
        
        Returns:
            bool: True if started successfully
        """
        try:
            # Connect to MQTT broker
            if not self.mqtt_client.connect():
                self.logger.error("Failed to connect to MQTT broker")
                return False
            
            # Subscribe to encoder data
            self._subscribe_to_encoders()
            
            # Subscribe to system commands
            self._subscribe_to_commands()
            
            # Start state publishing thread
            self._running = True
            self._publish_thread = threading.Thread(target=self._publish_loop, daemon=True)
            self._publish_thread.start()
            
            # Update status
            with self._state_lock:
                self.robot_state.status = "active"
                self.robot_state.last_updated = datetime.now().isoformat()
            
            self.logger.info("StateManager started successfully")
            return True
            
        except Exception as e:
            self.logger.exception("Failed to start StateManager")
            return False
    
    def stop(self):
        """Stop the state management service."""
        try:
            self._running = False
            
            # Stop publishing thread
            if self._publish_thread:
                self._publish_thread.join(timeout=5.0)
            
            # Update status
            with self._state_lock:
                self.robot_state.status = "stopped"
                self.robot_state.last_updated = datetime.now().isoformat()
            
            # Publish final state
            self._publish_state()
            
            # Disconnect MQTT
            self.mqtt_client.disconnect()
            
            self.logger.info("StateManager stopped")
            
        except Exception as e:
            self.logger.exception("Error stopping StateManager")
    
    def _subscribe_to_encoders(self):
        """Subscribe to encoder telemetry data."""
        # Subscribe to left encoder
        self.mqtt_client.subscribe(
            "orchestrator/data/left_encoder",
            self._handle_left_encoder_data
        )
        
        # Subscribe to right encoder  
        self.mqtt_client.subscribe(
            "orchestrator/data/right_encoder", 
            self._handle_right_encoder_data
        )
        
        # Subscribe to any encoder data (fallback)
        self.mqtt_client.subscribe(
            "orchestrator/data/+encoder",
            self._handle_encoder_data
        )
        
        self.logger.info("Subscribed to encoder telemetry topics")
    
    def _subscribe_to_commands(self):
        """Subscribe to state management commands."""
        self.mqtt_client.subscribe(
            "orchestrator/cmd/state_manager",
            self._handle_command
        )
        
        # Subscribe to emergency stop commands
        self.mqtt_client.subscribe(
            "orchestrator/cmd/estop",
            self._handle_emergency_stop
        )
        
        self.logger.info("Subscribed to state management command topics")
    
    def _handle_left_encoder_data(self, message_data: Dict[str, Any]):
        """Handle left encoder telemetry data."""
        try:
            payload = message_data['payload']
            encoder_data = payload.get('data', {})
            
            self.left_encoder_data = encoder_data
            self.last_encoder_update = time.time()
            
            # Update odometry if we have both encoders
            if self.right_encoder_data:
                self._update_odometry()
                
        except Exception as e:
            self.logger.exception("Error handling left encoder data")
    
    def _handle_right_encoder_data(self, message_data: Dict[str, Any]):
        """Handle right encoder telemetry data."""
        try:
            payload = message_data['payload']
            encoder_data = payload.get('data', {})
            
            self.right_encoder_data = encoder_data
            self.last_encoder_update = time.time()
            
            # Update odometry if we have both encoders
            if self.left_encoder_data:
                self._update_odometry()
                
        except Exception as e:
            self.logger.exception("Error handling right encoder data")
    
    def _handle_encoder_data(self, message_data: Dict[str, Any]):
        """Handle generic encoder data (fallback handler)."""
        try:
            topic = message_data['topic']
            payload = message_data['payload']
            encoder_data = payload.get('data', {})
            
            # Determine which encoder based on topic or device_id
            device_id = payload.get('device_id', '')
            
            if 'left' in topic.lower() or 'left' in device_id.lower():
                self.left_encoder_data = encoder_data
            elif 'right' in topic.lower() or 'right' in device_id.lower():
                self.right_encoder_data = encoder_data
            else:
                # If we can't determine which encoder, log warning
                self.logger.warning(f"Cannot determine encoder side for topic: {topic}")
                return
            
            self.last_encoder_update = time.time()
            
            # Update odometry if we have both encoders
            if self.left_encoder_data and self.right_encoder_data:
                self._update_odometry()
                
        except Exception as e:
            self.logger.exception("Error handling generic encoder data")
    
    def _handle_command(self, message_data: Dict[str, Any]):
        """Handle state management commands."""
        try:
            payload = message_data['payload']
            action = payload.get('action', '')
            
            if action == 'reset_odometry':
                self._reset_odometry()
            elif action == 'set_position':
                x = payload.get('x', 0.0)
                y = payload.get('y', 0.0)
                heading = payload.get('heading', 0.0)
                self._set_position(x, y, heading)
            elif action == 'set_status':
                status = payload.get('status', 'idle')
                self._set_status(status)
            else:
                self.logger.warning(f"Unknown command action: {action}")
                
        except Exception as e:
            self.logger.exception("Error handling state management command")
    
    def _handle_emergency_stop(self, message_data: Dict[str, Any]):
        """Handle emergency stop commands."""
        try:
            with self._state_lock:
                self.robot_state.status = "emergency_stop"
                self.robot_state.velocity = Velocity(0.0, 0.0)
                self.robot_state.last_updated = datetime.now().isoformat()
            
            self.logger.warning("Emergency stop activated")
            
        except Exception as e:
            self.logger.exception("Error handling emergency stop")
    
    def _update_odometry(self):
        """Update robot odometry based on encoder data."""
        try:
            current_time = time.time()
            dt = current_time - self.last_update_time
            
            if dt < 0.001:  # Avoid division by very small numbers
                return
            
            # Get current distances from encoders
            left_distance = self.left_encoder_data.get('total_distance', 0.0)
            right_distance = self.right_encoder_data.get('total_distance', 0.0)
            
            # Calculate distance deltas
            delta_left = left_distance - self.last_left_distance
            delta_right = right_distance - self.last_right_distance
            
            # Calculate robot motion
            delta_distance = (delta_left + delta_right) / 2.0  # Average distance
            delta_heading = (delta_right - delta_left) / self.wheel_base  # Differential heading
            
            with self._state_lock:
                # Update heading
                self.robot_state.heading += delta_heading
                
                # Normalize heading to [-pi, pi]
                while self.robot_state.heading > math.pi:
                    self.robot_state.heading -= 2 * math.pi
                while self.robot_state.heading < -math.pi:
                    self.robot_state.heading += 2 * math.pi
                
                # Update position (using current heading for direction)
                self.robot_state.position.x += delta_distance * math.cos(self.robot_state.heading)
                self.robot_state.position.y += delta_distance * math.sin(self.robot_state.heading)
                
                # Update velocities
                self.robot_state.velocity.linear = delta_distance / dt
                self.robot_state.velocity.angular = delta_heading / dt
                
                # Update metadata
                self.robot_state.last_updated = datetime.now().isoformat()
                self.robot_state.odometry_valid = True
                self.robot_state.encoder_data = {
                    'left': self.left_encoder_data,
                    'right': self.right_encoder_data
                }
            
            # Update tracking variables
            self.last_left_distance = left_distance
            self.last_right_distance = right_distance
            self.last_update_time = current_time
            self.update_count += 1
            
            # Log performance metrics periodically
            if self.update_count % 100 == 0:
                self.logger.log_performance_metric("odometry_update_rate", 1.0/dt, "Hz")
                
        except Exception as e:
            self.logger.exception("Error updating odometry")
            with self._state_lock:
                self.robot_state.odometry_valid = False
    
    def _reset_odometry(self):
        """Reset odometry to origin."""
        try:
            with self._state_lock:
                self.robot_state.position = Position(0.0, 0.0)
                self.robot_state.heading = 0.0
                self.robot_state.velocity = Velocity(0.0, 0.0)
                self.robot_state.last_updated = datetime.now().isoformat()
            
            # Reset tracking variables
            if self.left_encoder_data:
                self.last_left_distance = self.left_encoder_data.get('total_distance', 0.0)
            if self.right_encoder_data:
                self.last_right_distance = self.right_encoder_data.get('total_distance', 0.0)
            
            self.logger.info("Odometry reset to origin")
            
        except Exception as e:
            self.logger.exception("Error resetting odometry")
    
    def _set_position(self, x: float, y: float, heading: float):
        """Set robot position manually."""
        try:
            with self._state_lock:
                self.robot_state.position.x = x
                self.robot_state.position.y = y
                self.robot_state.heading = heading
                self.robot_state.last_updated = datetime.now().isoformat()
            
            self.logger.info(f"Position set to ({x:.3f}, {y:.3f}), heading={heading:.3f}")
            
        except Exception as e:
            self.logger.exception("Error setting position")
    
    def _set_status(self, status: str):
        """Set robot status."""
        try:
            valid_statuses = ["active", "idle", "error", "emergency_stop"]
            if status not in valid_statuses:
                self.logger.warning(f"Invalid status: {status}")
                return
            
            with self._state_lock:
                old_status = self.robot_state.status
                self.robot_state.status = status
                self.robot_state.last_updated = datetime.now().isoformat()
            
            self.logger.info(f"Status changed from {old_status} to {status}")
            
        except Exception as e:
            self.logger.exception("Error setting status")
    
    def _publish_loop(self):
        """Main loop for publishing robot state."""
        interval = 1.0 / self.publish_rate
        
        while self._running:
            try:
                start_time = time.time()
                
                self._publish_state()
                
                # Calculate sleep time to maintain publish rate
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.exception("Error in state publish loop")
                time.sleep(interval)
    
    def _publish_state(self):
        """Publish current robot state to MQTT."""
        try:
            with self._state_lock:
                # Create state message
                state_dict = asdict(self.robot_state)
                
                # Add additional metadata
                state_dict.update({
                    'wheel_base': self.wheel_base,
                    'update_count': self.update_count,
                    'last_encoder_update': self.last_encoder_update,
                    'publish_rate': self.publish_rate
                })
            
            # Publish to MQTT
            success = self.mqtt_client.publish(
                "orchestrator/status/robot",
                state_dict,
                qos=1  # Ensure delivery for status updates
            )
            
            if not success:
                self.logger.warning("Failed to publish robot state")
                
        except Exception as e:
            self.logger.exception("Error publishing robot state")
    
    def get_current_state(self) -> RobotState:
        """Get current robot state (thread-safe)."""
        with self._state_lock:
            # Return a copy to avoid external modification
            return RobotState(
                position=Position(self.robot_state.position.x, self.robot_state.position.y),
                heading=self.robot_state.heading,
                velocity=Velocity(self.robot_state.velocity.linear, self.robot_state.velocity.angular),
                status=self.robot_state.status,
                mission_status=self.robot_state.mission_status,
                last_updated=self.robot_state.last_updated,
                odometry_valid=self.robot_state.odometry_valid,
                encoder_data=self.robot_state.encoder_data
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        return {
            'service': 'state_manager',
            'running': self._running,
            'mqtt_connected': self.mqtt_client.is_connected,
            'wheel_base': self.wheel_base,
            'publish_rate': self.publish_rate,
            'update_count': self.update_count,
            'last_encoder_update': self.last_encoder_update,
            'has_left_encoder': self.left_encoder_data is not None,
            'has_right_encoder': self.right_encoder_data is not None,
            'current_state': asdict(self.get_current_state())
        }