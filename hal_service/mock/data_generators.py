"""
Data Generators for Mock HAL Components

Provides realistic data generation for sensors and actuators to simulate
hardware behavior during testing and development.
"""

import math
import time
import random
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SimulationState:
    """Shared simulation state for coordinated mock data"""
    robot_x: float = 0.0
    robot_y: float = 0.0
    robot_heading: float = 0.0  # radians
    robot_velocity: float = 0.0  # m/s
    robot_angular_velocity: float = 0.0  # rad/s
    last_update: float = 0.0
    
    # Environment obstacles (x, y, radius)
    obstacles: List[Tuple[float, float, float]] = None
    
    def __post_init__(self):
        if self.obstacles is None:
            # Default obstacle layout
            self.obstacles = [
                (2.0, 1.0, 0.3),   # Obstacle at 2m, 1m with 30cm radius
                (-1.5, 2.5, 0.4),  # Obstacle at -1.5m, 2.5m with 40cm radius
                (0.5, -2.0, 0.2),  # Small obstacle
                (3.0, 0.0, 0.5),   # Large obstacle
                (-2.0, -1.0, 0.3), # Another obstacle
            ]


class LidarDataGenerator:
    """
    Generates realistic LiDAR scan data with obstacles and noise.
    
    Simulates a 360-degree 2D LiDAR with configurable parameters
    and realistic obstacle detection.
    """
    
    def __init__(self, min_range: float = 0.15, max_range: float = 12.0,
                 angle_resolution: float = 1.0, noise_level: float = 0.02):
        self.min_range = min_range
        self.max_range = max_range
        self.angle_resolution = angle_resolution
        self.noise_level = noise_level
        
        # Simulation parameters
        self.scan_count = 0
        self.base_environment = self._create_base_environment()
        
    def _create_base_environment(self) -> Dict[float, float]:
        """Create a base environment with walls and features"""
        environment = {}
        
        # Room boundaries (5m x 5m room centered at origin)
        room_size = 5.0
        
        for angle_deg in range(0, 360, int(self.angle_resolution)):
            angle_rad = math.radians(angle_deg)
            
            # Calculate distance to room walls
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            # Find intersection with room boundaries
            if cos_a > 0:
                dist_x = room_size / (2 * cos_a)
            elif cos_a < 0:
                dist_x = -room_size / (2 * cos_a)
            else:
                dist_x = float('inf')
            
            if sin_a > 0:
                dist_y = room_size / (2 * sin_a)
            elif sin_a < 0:
                dist_y = -room_size / (2 * sin_a)
            else:
                dist_y = float('inf')
            
            # Take minimum distance to wall
            wall_distance = min(dist_x, dist_y)
            
            # Add some variation to walls (not perfectly straight)
            wall_variation = 0.1 * math.sin(angle_deg * 0.1) * random.uniform(0.8, 1.2)
            wall_distance += wall_variation
            
            environment[angle_deg] = min(wall_distance, self.max_range)
        
        return environment
    
    def generate_scan(self, sim_state: SimulationState) -> Dict[str, Any]:
        """
        Generate a complete LiDAR scan based on current simulation state.
        
        Args:
            sim_state: Current robot simulation state
            
        Returns:
            Dictionary containing LiDAR scan data
        """
        ranges = []
        angles = []
        quality = []
        
        current_time = time.time()
        
        for angle_deg in range(0, 360, int(self.angle_resolution)):
            angle_rad = math.radians(angle_deg)
            
            # Transform angle to world coordinates
            world_angle = angle_rad + sim_state.robot_heading
            
            # Start with base environment distance
            base_distance = self.base_environment.get(angle_deg, self.max_range)
            
            # Check for obstacles
            obstacle_distance = self._check_obstacles(
                sim_state.robot_x, sim_state.robot_y, world_angle, sim_state.obstacles
            )
            
            # Take minimum distance (closest obstacle or wall)
            measured_distance = min(base_distance, obstacle_distance)
            
            # Add noise
            noise = random.gauss(0, self.noise_level * measured_distance)
            measured_distance += noise
            
            # Clamp to valid range
            measured_distance = max(self.min_range, min(self.max_range, measured_distance))
            
            # Calculate quality based on distance and angle
            signal_quality = self._calculate_quality(measured_distance, angle_deg)
            
            ranges.append(measured_distance)
            angles.append(angle_deg)
            quality.append(signal_quality)
        
        self.scan_count += 1
        
        return {
            'scan_available': True,
            'timestamp': datetime.now().isoformat(),
            'ranges': ranges,
            'angles': angles,
            'quality': quality,
            'min_range': self.min_range,
            'max_range': self.max_range,
            'scan_time': 0.1,  # 100ms scan time
            'num_points': len(ranges),
            'scan_count': self.scan_count,
            'robot_position': {
                'x': sim_state.robot_x,
                'y': sim_state.robot_y,
                'heading': sim_state.robot_heading
            }
        }
    
    def _check_obstacles(self, robot_x: float, robot_y: float, angle: float,
                        obstacles: List[Tuple[float, float, float]]) -> float:
        """Check for obstacles along a ray from robot position"""
        min_distance = self.max_range
        
        # Ray direction
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        for obs_x, obs_y, obs_radius in obstacles:
            # Vector from robot to obstacle center
            to_obs_x = obs_x - robot_x
            to_obs_y = obs_y - robot_y
            
            # Project obstacle center onto ray
            projection = to_obs_x * dx + to_obs_y * dy
            
            if projection < 0:
                continue  # Obstacle is behind robot
            
            # Find closest point on ray to obstacle center
            closest_x = robot_x + projection * dx
            closest_y = robot_y + projection * dy
            
            # Distance from obstacle center to ray
            dist_to_ray = math.sqrt(
                (obs_x - closest_x) ** 2 + (obs_y - closest_y) ** 2
            )
            
            # Check if ray intersects obstacle
            if dist_to_ray <= obs_radius:
                # Calculate intersection distance
                # Distance along ray to closest approach
                approach_dist = projection
                # Distance from approach point to intersection
                chord_half = math.sqrt(max(0, obs_radius ** 2 - dist_to_ray ** 2))
                intersection_dist = approach_dist - chord_half
                
                if intersection_dist > 0:
                    min_distance = min(min_distance, intersection_dist)
        
        return min_distance
    
    def _calculate_quality(self, distance: float, angle: float) -> int:
        """Calculate signal quality based on distance and angle"""
        # Base quality decreases with distance
        base_quality = max(0, 255 - int(distance * 20))
        
        # Some angles have better/worse quality (simulating sensor characteristics)
        angle_factor = 1.0 + 0.1 * math.sin(math.radians(angle * 4))
        
        # Add some random variation
        noise_factor = random.uniform(0.9, 1.1)
        
        quality = int(base_quality * angle_factor * noise_factor)
        return max(0, min(255, quality))


class EncoderDataGenerator:
    """
    Generates realistic encoder data based on motor commands and movement.
    
    Simulates wheel encoders with realistic noise, drift, and mechanical
    characteristics.
    """
    
    def __init__(self, wheel_diameter: float = 0.1, encoder_resolution: int = 1000,
                 gear_ratio: float = 1.0, noise_level: float = 0.01):
        self.wheel_diameter = wheel_diameter
        self.encoder_resolution = encoder_resolution
        self.gear_ratio = gear_ratio
        self.noise_level = noise_level
        
        # Encoder state
        self.tick_count = 0
        self.total_distance = 0.0
        self.last_update_time = time.time()
        self.velocity = 0.0
        self.target_velocity = 0.0
        
        # Mechanical simulation
        self.mechanical_efficiency = 0.95
        self.backlash_ticks = 2  # Encoder ticks of backlash
        self.last_direction = 1
        
    def update_from_motor_command(self, command: Dict[str, Any], dt: float):
        """Update encoder state based on motor command"""
        action = command.get('action', '')
        parameters = command.get('parameters', {})
        
        if action in ['move_forward', 'move_backward']:
            speed = parameters.get('speed', 0.0)
            direction = 1 if action == 'move_forward' else -1
            self.target_velocity = speed * direction
        elif action == 'stop':
            self.target_velocity = 0.0
        elif action == 'set_speed':
            speed = parameters.get('speed', 0.0)
            direction = parameters.get('direction', 1)
            self.target_velocity = speed * direction
        
        # Simulate acceleration/deceleration
        velocity_diff = self.target_velocity - self.velocity
        max_accel = 2.0  # m/s²
        max_change = max_accel * dt
        
        if abs(velocity_diff) <= max_change:
            self.velocity = self.target_velocity
        else:
            self.velocity += max_change * (1 if velocity_diff > 0 else -1)
        
        # Apply mechanical efficiency
        actual_velocity = self.velocity * self.mechanical_efficiency
        
        # Handle backlash when changing direction
        current_direction = 1 if actual_velocity >= 0 else -1
        if current_direction != self.last_direction and abs(actual_velocity) > 0.01:
            # Simulate backlash by not counting some ticks during direction change
            backlash_factor = 0.5
            actual_velocity *= backlash_factor
            self.last_direction = current_direction
        
        # Calculate distance traveled
        distance_traveled = actual_velocity * dt
        
        # Add noise
        distance_noise = random.gauss(0, self.noise_level * abs(distance_traveled))
        distance_traveled += distance_noise
        
        # Update encoder counts
        wheel_circumference = math.pi * self.wheel_diameter
        distance_per_tick = wheel_circumference / (self.encoder_resolution * self.gear_ratio)
        
        tick_increment = distance_traveled / distance_per_tick
        self.tick_count += int(tick_increment)
        self.total_distance += distance_traveled
        
        # Update velocity (with some smoothing)
        if dt > 0:
            measured_velocity = distance_traveled / dt
            self.velocity = 0.8 * self.velocity + 0.2 * measured_velocity
    
    def generate_data(self) -> Dict[str, Any]:
        """Generate encoder telemetry data"""
        current_time = time.time()
        
        # Calculate RPM
        wheel_circumference = math.pi * self.wheel_diameter
        if abs(self.velocity) > 0.001:
            wheel_rps = abs(self.velocity) / wheel_circumference
            rpm = wheel_rps * 60.0
        else:
            rpm = 0.0
        
        # Calculate derived values
        distance_per_tick = wheel_circumference / (self.encoder_resolution * self.gear_ratio)
        
        return {
            'tick_count': self.tick_count,
            'total_distance': self.total_distance,
            'velocity': self.velocity,
            'direction': 1 if self.velocity >= 0 else -1,
            'rpm': rpm,
            'distance_per_tick': distance_per_tick,
            'wheel_diameter': self.wheel_diameter,
            'encoder_resolution': self.encoder_resolution,
            'gear_ratio': self.gear_ratio,
            'timestamp': current_time,
            'pins': {
                'encoder_a': 20,  # Mock pin numbers
                'encoder_b': 21
            }
        }
    
    def reset(self):
        """Reset encoder to zero"""
        self.tick_count = 0
        self.total_distance = 0.0
        self.velocity = 0.0
        self.target_velocity = 0.0


class MotorDataGenerator:
    """
    Generates realistic motor telemetry data based on commands and load.
    
    Simulates motor behavior including acceleration, current draw,
    temperature, and mechanical characteristics.
    """
    
    def __init__(self, max_speed: float = 1.0, acceleration: float = 0.5):
        self.max_speed = max_speed
        self.acceleration = acceleration
        
        # Motor state
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.direction = 1
        self.is_moving = False
        self.duty_cycle = 0.0
        
        # Physical simulation
        self.motor_temperature = 25.0  # Celsius
        self.current_draw = 0.0  # Amperes
        self.voltage = 12.0  # Volts
        self.load_factor = 1.0  # Simulated mechanical load
        
        # Command tracking
        self.distance_target = 0.0
        self.distance_traveled = 0.0
        
    def update_from_command(self, command: Dict[str, Any], dt: float):
        """Update motor state based on command"""
        action = command.get('action', '')
        parameters = command.get('parameters', {})
        
        if action == 'move_forward':
            distance = parameters.get('distance', 0.0)
            speed = parameters.get('speed', 0.5)
            self.target_speed = speed * self.max_speed
            self.direction = 1
            self.distance_target = distance
            self.distance_traveled = 0.0
            self.is_moving = True
            
        elif action == 'move_backward':
            distance = parameters.get('distance', 0.0)
            speed = parameters.get('speed', 0.5)
            self.target_speed = speed * self.max_speed
            self.direction = -1
            self.distance_target = distance
            self.distance_traveled = 0.0
            self.is_moving = True
            
        elif action == 'stop':
            self.target_speed = 0.0
            self.is_moving = False
            
        elif action == 'set_speed':
            speed = parameters.get('speed', 0.0)
            direction = parameters.get('direction', 1)
            self.target_speed = speed * self.max_speed
            self.direction = direction
            self.is_moving = speed > 0
            self.distance_target = float('inf')
        
        # Update current speed with acceleration limits
        speed_diff = self.target_speed - self.current_speed
        max_change = self.acceleration * dt
        
        if abs(speed_diff) <= max_change:
            self.current_speed = self.target_speed
        else:
            self.current_speed += max_change * (1 if speed_diff > 0 else -1)
        
        # Update distance traveled
        if self.is_moving:
            distance_increment = abs(self.current_speed) * dt
            self.distance_traveled += distance_increment
            
            # Check if target distance reached
            if self.distance_traveled >= self.distance_target:
                self.is_moving = False
                self.current_speed = 0.0
                self.target_speed = 0.0
        
        # Update physical parameters
        self._update_physical_state(dt)
    
    def _update_physical_state(self, dt: float):
        """Update physical motor parameters"""
        # Calculate duty cycle
        if self.max_speed > 0:
            self.duty_cycle = min(100, abs(self.current_speed) * 100 / self.max_speed)
        else:
            self.duty_cycle = 0
        
        # Calculate current draw (simplified model)
        base_current = 0.1  # Idle current
        load_current = (self.duty_cycle / 100) * 2.0 * self.load_factor  # Load-dependent current
        self.current_draw = base_current + load_current
        
        # Calculate temperature (simplified thermal model)
        ambient_temp = 25.0
        heating_rate = self.current_draw * 5.0  # Heating due to current
        cooling_rate = (self.motor_temperature - ambient_temp) * 0.1  # Cooling to ambient
        
        temp_change = (heating_rate - cooling_rate) * dt
        self.motor_temperature += temp_change
        self.motor_temperature = max(ambient_temp, self.motor_temperature)
    
    def generate_data(self) -> Dict[str, Any]:
        """Generate motor telemetry data"""
        return {
            'motor_id': 'mock_motor',
            'is_moving': self.is_moving,
            'current_speed': self.current_speed,
            'target_speed': self.target_speed,
            'direction': self.direction,
            'duty_cycle': self.duty_cycle,
            'distance_traveled': self.distance_traveled,
            'target_distance': self.distance_target,
            'current_draw': self.current_draw,
            'motor_temperature': self.motor_temperature,
            'voltage': self.voltage,
            'load_factor': self.load_factor,
            'timestamp': time.time()
        }


class SimulationCoordinator:
    """
    Coordinates multiple data generators to maintain consistent simulation state.
    
    Ensures that encoder data matches motor commands, LiDAR data reflects
    robot position, and all components maintain synchronized state.
    """
    
    def __init__(self, wheel_base: float = 0.3):
        self.wheel_base = wheel_base
        self.sim_state = SimulationState()
        
        # Data generators
        self.lidar_generator = LidarDataGenerator()
        self.left_encoder_generator = EncoderDataGenerator()
        self.right_encoder_generator = EncoderDataGenerator()
        self.left_motor_generator = MotorDataGenerator()
        self.right_motor_generator = MotorDataGenerator()
        
        self.last_update = time.time()
    
    def update(self, dt: Optional[float] = None):
        """Update simulation state and all generators"""
        current_time = time.time()
        if dt is None:
            dt = current_time - self.last_update
        
        # Update robot position based on encoder data
        left_velocity = self.left_encoder_generator.velocity
        right_velocity = self.right_encoder_generator.velocity
        
        # Differential drive kinematics
        linear_velocity = (left_velocity + right_velocity) / 2.0
        angular_velocity = (right_velocity - left_velocity) / self.wheel_base
        
        # Update robot pose
        self.sim_state.robot_x += linear_velocity * math.cos(self.sim_state.robot_heading) * dt
        self.sim_state.robot_y += linear_velocity * math.sin(self.sim_state.robot_heading) * dt
        self.sim_state.robot_heading += angular_velocity * dt
        
        # Normalize heading
        while self.sim_state.robot_heading > math.pi:
            self.sim_state.robot_heading -= 2 * math.pi
        while self.sim_state.robot_heading < -math.pi:
            self.sim_state.robot_heading += 2 * math.pi
        
        self.sim_state.robot_velocity = linear_velocity
        self.sim_state.robot_angular_velocity = angular_velocity
        self.sim_state.last_update = current_time
        
        self.last_update = current_time
    
    def process_motor_command(self, motor_id: str, command: Dict[str, Any]):
        """Process motor command and update appropriate generators"""
        dt = time.time() - self.last_update
        
        if 'left' in motor_id.lower():
            self.left_motor_generator.update_from_command(command, dt)
            self.left_encoder_generator.update_from_motor_command(command, dt)
        elif 'right' in motor_id.lower():
            self.right_motor_generator.update_from_command(command, dt)
            self.right_encoder_generator.update_from_motor_command(command, dt)
        
        # Update simulation state
        self.update(dt)
    
    def get_lidar_data(self) -> Dict[str, Any]:
        """Get current LiDAR scan data"""
        return self.lidar_generator.generate_scan(self.sim_state)
    
    def get_encoder_data(self, encoder_id: str) -> Dict[str, Any]:
        """Get encoder data for specified encoder"""
        if 'left' in encoder_id.lower():
            return self.left_encoder_generator.generate_data()
        elif 'right' in encoder_id.lower():
            return self.right_encoder_generator.generate_data()
        else:
            # Default to left encoder
            return self.left_encoder_generator.generate_data()
    
    def get_motor_data(self, motor_id: str) -> Dict[str, Any]:
        """Get motor telemetry data"""
        if 'left' in motor_id.lower():
            return self.left_motor_generator.generate_data()
        elif 'right' in motor_id.lower():
            return self.right_motor_generator.generate_data()
        else:
            # Default to left motor
            return self.left_motor_generator.generate_data()
    
    def get_robot_state(self) -> Dict[str, Any]:
        """Get current robot state"""
        return {
            'position': {
                'x': self.sim_state.robot_x,
                'y': self.sim_state.robot_y
            },
            'heading': self.sim_state.robot_heading,
            'velocity': {
                'linear': self.sim_state.robot_velocity,
                'angular': self.sim_state.robot_angular_velocity
            },
            'timestamp': self.sim_state.last_update
        }
    
    def reset_simulation(self):
        """Reset simulation to initial state"""
        self.sim_state = SimulationState()
        self.left_encoder_generator.reset()
        self.right_encoder_generator.reset()
        self.last_update = time.time()