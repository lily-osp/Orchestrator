#!/usr/bin/env python3
"""
Standalone Demo of Mock HAL Core Functionality

This demo shows the core mock HAL functionality without external dependencies.
It demonstrates the data generation and simulation capabilities.
"""

import json
import math
import time
import random
import threading
from datetime import datetime
from typing import Dict, Any, List, Tuple


class MockMQTTMessage:
    """Mock MQTT message for simulation"""
    def __init__(self, topic: str, payload: bytes):
        self.topic = topic
        self.payload = payload


class MockMQTTClient:
    """Standalone mock MQTT client"""
    def __init__(self):
        self.connected = True
        self.message_history = []
        self.subscribers = {}
        self.stats = {'published': 0, 'received': 0}
    
    def publish(self, topic: str, payload: Dict[str, Any]) -> bool:
        """Publish a message"""
        message = MockMQTTMessage(topic, json.dumps(payload).encode())
        self.message_history.append(message)
        self.stats['published'] += 1
        
        # Deliver to subscribers
        for pattern, callback in self.subscribers.items():
            if self._topic_matches(topic, pattern):
                callback(message)
                self.stats['received'] += 1
        
        return True
    
    def subscribe(self, pattern: str, callback):
        """Subscribe to topic pattern"""
        self.subscribers[pattern] = callback
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern"""
        if '+' in pattern:
            return True  # Simplified matching
        return topic.startswith(pattern.replace('#', ''))


class RobotSimulation:
    """Standalone robot simulation"""
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0
        self.left_velocity = 0.0
        self.right_velocity = 0.0
        self.wheel_base = 0.3
        
        # Encoder state
        self.left_encoder_ticks = 0
        self.right_encoder_ticks = 0
        self.encoder_resolution = 1000
        self.wheel_diameter = 0.1
        
        # Motor state
        self.left_motor_speed = 0.0
        self.right_motor_speed = 0.0
        self.left_motor_temp = 25.0
        self.right_motor_temp = 25.0
        
        # Environment obstacles (x, y, radius)
        self.obstacles = [
            (2.0, 1.0, 0.3),
            (-1.5, 2.5, 0.4),
            (0.5, -2.0, 0.2),
            (3.0, 0.0, 0.5),
        ]
    
    def update(self, dt: float):
        """Update robot state"""
        # Differential drive kinematics
        linear_velocity = (self.left_velocity + self.right_velocity) / 2.0
        angular_velocity = (self.right_velocity - self.left_velocity) / self.wheel_base
        
        # Update position
        self.x += linear_velocity * math.cos(self.heading) * dt
        self.y += linear_velocity * math.sin(self.heading) * dt
        self.heading += angular_velocity * dt
        
        # Normalize heading
        while self.heading > math.pi:
            self.heading -= 2 * math.pi
        while self.heading < -math.pi:
            self.heading += 2 * math.pi
        
        # Update encoders
        wheel_circumference = math.pi * self.wheel_diameter
        left_distance = self.left_velocity * dt
        right_distance = self.right_velocity * dt
        
        left_ticks = int(left_distance / wheel_circumference * self.encoder_resolution)
        right_ticks = int(right_distance / wheel_circumference * self.encoder_resolution)
        
        self.left_encoder_ticks += left_ticks
        self.right_encoder_ticks += right_ticks
        
        # Update motor temperatures (simple model)
        heating_left = abs(self.left_motor_speed) * 2.0 * dt
        heating_right = abs(self.right_motor_speed) * 2.0 * dt
        cooling = 0.1 * dt
        
        self.left_motor_temp += heating_left - cooling * (self.left_motor_temp - 25.0)
        self.right_motor_temp += heating_right - cooling * (self.right_motor_temp - 25.0)
        
        self.left_motor_temp = max(25.0, self.left_motor_temp)
        self.right_motor_temp = max(25.0, self.right_motor_temp)
    
    def process_motor_command(self, device: str, command: Dict[str, Any]):
        """Process motor command"""
        action = command.get('action', '')
        parameters = command.get('parameters', {})
        
        if 'left' in device:
            if action == 'move_forward':
                speed = parameters.get('speed', 0.5)
                self.left_motor_speed = speed
                self.left_velocity = speed
            elif action == 'move_backward':
                speed = parameters.get('speed', 0.5)
                self.left_motor_speed = speed
                self.left_velocity = -speed
            elif action == 'stop':
                self.left_motor_speed = 0.0
                self.left_velocity = 0.0
        
        elif 'right' in device:
            if action == 'move_forward':
                speed = parameters.get('speed', 0.5)
                self.right_motor_speed = speed
                self.right_velocity = speed
            elif action == 'move_backward':
                speed = parameters.get('speed', 0.5)
                self.right_motor_speed = speed
                self.right_velocity = -speed
            elif action == 'stop':
                self.right_motor_speed = 0.0
                self.right_velocity = 0.0
    
    def generate_lidar_scan(self) -> Dict[str, Any]:
        """Generate LiDAR scan data"""
        ranges = []
        angles = []
        
        for angle_deg in range(0, 360, 2):  # 2-degree resolution
            angle_rad = math.radians(angle_deg)
            
            # Room boundaries (5m x 5m room)
            room_size = 5.0
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            # Calculate distance to walls
            if cos_a > 0:
                dist_x = (room_size/2 - self.x) / cos_a
            elif cos_a < 0:
                dist_x = (-room_size/2 - self.x) / cos_a
            else:
                dist_x = float('inf')
            
            if sin_a > 0:
                dist_y = (room_size/2 - self.y) / sin_a
            elif sin_a < 0:
                dist_y = (-room_size/2 - self.y) / sin_a
            else:
                dist_y = float('inf')
            
            wall_distance = min(abs(dist_x), abs(dist_y))
            
            # Check obstacles
            obstacle_distance = wall_distance
            world_angle = angle_rad + self.heading
            
            for obs_x, obs_y, obs_radius in self.obstacles:
                # Vector from robot to obstacle
                dx = obs_x - self.x
                dy = obs_y - self.y
                
                # Project onto ray
                ray_dx = math.cos(world_angle)
                ray_dy = math.sin(world_angle)
                
                projection = dx * ray_dx + dy * ray_dy
                
                if projection > 0:  # Obstacle in front
                    # Distance from ray to obstacle center
                    closest_x = self.x + projection * ray_dx
                    closest_y = self.y + projection * ray_dy
                    
                    dist_to_ray = math.sqrt((obs_x - closest_x)**2 + (obs_y - closest_y)**2)
                    
                    if dist_to_ray <= obs_radius:
                        # Ray hits obstacle
                        chord_half = math.sqrt(max(0, obs_radius**2 - dist_to_ray**2))
                        intersection_dist = projection - chord_half
                        
                        if intersection_dist > 0:
                            obstacle_distance = min(obstacle_distance, intersection_dist)
            
            # Add noise
            measured_distance = obstacle_distance + random.gauss(0, 0.02)
            measured_distance = max(0.15, min(12.0, measured_distance))
            
            ranges.append(measured_distance)
            angles.append(angle_deg)
        
        return {
            'scan_available': True,
            'ranges': ranges,
            'angles': angles,
            'min_range': 0.15,
            'max_range': 12.0,
            'num_points': len(ranges),
            'robot_position': {'x': self.x, 'y': self.y, 'heading': self.heading}
        }
    
    def get_encoder_data(self, device: str) -> Dict[str, Any]:
        """Get encoder data"""
        if 'left' in device:
            ticks = self.left_encoder_ticks
            velocity = self.left_velocity
        else:
            ticks = self.right_encoder_ticks
            velocity = self.right_velocity
        
        wheel_circumference = math.pi * self.wheel_diameter
        distance = ticks / self.encoder_resolution * wheel_circumference
        
        return {
            'tick_count': ticks,
            'total_distance': distance,
            'velocity': velocity,
            'direction': 1 if velocity >= 0 else -1,
            'wheel_diameter': self.wheel_diameter,
            'encoder_resolution': self.encoder_resolution
        }
    
    def get_motor_data(self, device: str) -> Dict[str, Any]:
        """Get motor telemetry"""
        if 'left' in device:
            speed = self.left_motor_speed
            temp = self.left_motor_temp
        else:
            speed = self.right_motor_speed
            temp = self.right_motor_temp
        
        return {
            'current_speed': speed,
            'target_speed': speed,
            'is_moving': abs(speed) > 0.01,
            'duty_cycle': abs(speed) * 100,
            'motor_temperature': temp,
            'current_draw': 0.1 + abs(speed) * 2.0,
            'voltage': 12.0
        }


class StandaloneMockHAL:
    """Standalone Mock HAL demonstration"""
    
    def __init__(self):
        self.mqtt_client = MockMQTTClient()
        self.robot = RobotSimulation()
        self.running = False
        
        # Setup command subscription
        self.mqtt_client.subscribe("orchestrator/cmd/", self._handle_command)
    
    def _handle_command(self, message: MockMQTTMessage):
        """Handle incoming commands"""
        try:
            command = json.loads(message.payload.decode())
            device = message.topic.split('/')[-1]  # Extract device from topic
            
            print(f"📨 Command received: {device} -> {command.get('action', 'unknown')}")
            
            self.robot.process_motor_command(device, command)
            
            # Send acknowledgment
            ack_topic = f"orchestrator/ack/{device}"
            ack_message = {
                'timestamp': datetime.now().isoformat(),
                'device_id': device,
                'command_id': command.get('command_id', 'unknown'),
                'success': True
            }
            self.mqtt_client.publish(ack_topic, ack_message)
            
        except Exception as e:
            print(f"❌ Error handling command: {e}")
    
    def _publish_telemetry(self):
        """Publish telemetry data"""
        timestamp = datetime.now().isoformat()
        
        # Publish encoder data
        for device in ['left_encoder', 'right_encoder']:
            encoder_data = self.robot.get_encoder_data(device)
            message = {
                'timestamp': timestamp,
                'device_id': device,
                'data': encoder_data
            }
            self.mqtt_client.publish(f"orchestrator/data/{device}", message)
        
        # Publish motor data
        for device in ['left_motor', 'right_motor']:
            motor_data = self.robot.get_motor_data(device)
            message = {
                'timestamp': timestamp,
                'device_id': device,
                'data': motor_data
            }
            self.mqtt_client.publish(f"orchestrator/data/{device}", message)
        
        # Publish LiDAR data
        lidar_data = self.robot.generate_lidar_scan()
        message = {
            'timestamp': timestamp,
            'device_id': 'lidar_01',
            'data': lidar_data
        }
        self.mqtt_client.publish("orchestrator/data/lidar_01", message)
        
        # Publish robot state
        state_message = {
            'timestamp': timestamp,
            'position': {'x': self.robot.x, 'y': self.robot.y},
            'heading': self.robot.heading,
            'velocity': {
                'linear': (self.robot.left_velocity + self.robot.right_velocity) / 2.0,
                'angular': (self.robot.right_velocity - self.robot.left_velocity) / self.robot.wheel_base
            },
            'status': 'active'
        }
        self.mqtt_client.publish("orchestrator/status/robot", state_message)
    
    def run_demo(self):
        """Run the demonstration"""
        print("🚀 Standalone Mock HAL Demo")
        print("=" * 50)
        
        self.running = True
        
        print("\n1. ✅ Mock HAL initialized")
        print("2. ✅ MQTT client ready (simulated)")
        print("3. ✅ Robot simulation active")
        
        print("\n📡 Sending test commands...")
        
        # Test commands
        commands = [
            {
                'topic': 'orchestrator/cmd/left_motor',
                'command': {
                    'timestamp': datetime.now().isoformat(),
                    'command_id': 'demo_001',
                    'action': 'move_forward',
                    'parameters': {'distance': 1.0, 'speed': 0.5}
                }
            },
            {
                'topic': 'orchestrator/cmd/right_motor', 
                'command': {
                    'timestamp': datetime.now().isoformat(),
                    'command_id': 'demo_002',
                    'action': 'move_forward',
                    'parameters': {'distance': 1.0, 'speed': 0.5}
                }
            }
        ]
        
        for cmd in commands:
            print(f"   Sending: {cmd['command']['action']} to {cmd['topic'].split('/')[-1]}")
            self.mqtt_client.publish(cmd['topic'], cmd['command'])
        
        print("\n🔄 Running simulation...")
        
        # Run simulation for 10 seconds
        start_time = time.time()
        last_telemetry = 0
        
        while time.time() - start_time < 10:
            current_time = time.time()
            dt = 0.1  # 100ms timestep
            
            # Update robot simulation
            self.robot.update(dt)
            
            # Publish telemetry every 0.5 seconds
            if current_time - last_telemetry >= 0.5:
                self._publish_telemetry()
                last_telemetry = current_time
            
            time.sleep(dt)
        
        # Stop motors
        stop_command = {
            'timestamp': datetime.now().isoformat(),
            'command_id': 'demo_stop',
            'action': 'stop',
            'parameters': {}
        }
        
        self.mqtt_client.publish('orchestrator/cmd/left_motor', stop_command)
        self.mqtt_client.publish('orchestrator/cmd/right_motor', stop_command)
        
        print("\n📊 Simulation Results:")
        print(f"   Final Position: ({self.robot.x:.3f}, {self.robot.y:.3f})")
        print(f"   Final Heading: {self.robot.heading:.3f} rad ({math.degrees(self.robot.heading):.1f}°)")
        print(f"   Left Encoder: {self.robot.left_encoder_ticks} ticks")
        print(f"   Right Encoder: {self.robot.right_encoder_ticks} ticks")
        print(f"   Left Motor Temp: {self.robot.left_motor_temp:.1f}°C")
        print(f"   Right Motor Temp: {self.robot.right_motor_temp:.1f}°C")
        
        print(f"\n📈 MQTT Statistics:")
        print(f"   Messages Published: {self.mqtt_client.stats['published']}")
        print(f"   Messages Received: {self.mqtt_client.stats['received']}")
        print(f"   Total Messages: {len(self.mqtt_client.message_history)}")
        
        print(f"\n📡 Sample MQTT Topics:")
        topics = set(msg.topic for msg in self.mqtt_client.message_history[-20:])
        for topic in sorted(topics):
            print(f"   - {topic}")
        
        # Show sample LiDAR data
        lidar_messages = [msg for msg in self.mqtt_client.message_history 
                         if 'lidar' in msg.topic]
        if lidar_messages:
            latest_lidar = lidar_messages[-1]
            lidar_payload = json.loads(latest_lidar.payload.decode())
            lidar_data = lidar_payload['data']
            ranges = lidar_data['ranges']
            
            print(f"\n🔍 LiDAR Data Sample:")
            print(f"   Scan Points: {len(ranges)}")
            print(f"   Range: {min(ranges):.2f}m to {max(ranges):.2f}m")
            
            # Count obstacles in different zones
            angles = lidar_data['angles']
            front_obstacles = sum(1 for r, a in zip(ranges, angles) 
                                if -30 <= a <= 30 and r < 2.0)
            print(f"   Front Obstacles (<2m): {front_obstacles}")
        
        print("\n✅ Demo completed successfully!")
        print("\n🎯 What was demonstrated:")
        print("   ✅ MQTT command processing")
        print("   ✅ Robot kinematics simulation")
        print("   ✅ Encoder feedback generation")
        print("   ✅ Motor telemetry simulation")
        print("   ✅ LiDAR scan generation")
        print("   ✅ Real-time state tracking")
        
        print("\n🌐 This mock system provides:")
        print("   • Realistic sensor data for UI development")
        print("   • Command acknowledgment and processing")
        print("   • Coordinated multi-device simulation")
        print("   • MQTT interface compatibility")
        print("   • Physics-based robot behavior")
        
        return True


def main():
    """Main entry point"""
    try:
        demo = StandaloneMockHAL()
        success = demo.run_demo()
        
        if success:
            print("\n🎉 Standalone Mock HAL demo completed!")
            print("   Ready for integration with UI/control systems")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()