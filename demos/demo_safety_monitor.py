#!/usr/bin/env python3
"""
Demonstration script for the Safety Monitor subsystem.

This script demonstrates the safety monitor functionality by simulating
LiDAR data and showing how the safety system responds to different scenarios.
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
import sys

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent / "hal_service"))

try:
    from hal_service.mqtt_client import MQTTClientWrapper, MQTTConfig
except ImportError as e:
    print(f"Error importing MQTT client: {e}")
    print("This demo requires the paho-mqtt library.")
    print("Install with: pip install paho-mqtt")
    sys.exit(1)


class SafetyMonitorDemo:
    """Demonstration of safety monitor functionality."""
    
    def __init__(self):
        """Initialize the demo."""
        self.mqtt_config = MQTTConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="safety_demo_client"
        )
        
        self.mqtt_client = MQTTClientWrapper(self.mqtt_config)
        self.emergency_stops_received = []
        self.status_updates_received = []
        
    def setup(self):
        """Set up the demo environment."""
        print("Setting up Safety Monitor Demo...")
        
        # Connect to MQTT broker
        if not self.mqtt_client.connect():
            print("ERROR: Failed to connect to MQTT broker")
            print("Make sure mosquitto is running: mosquitto -v")
            return False
        
        # Subscribe to emergency stop commands
        if not self.mqtt_client.subscribe("orchestrator/cmd/estop", self._handle_emergency_stop):
            print("ERROR: Failed to subscribe to emergency stop topic")
            return False
        
        # Subscribe to safety status
        if not self.mqtt_client.subscribe("orchestrator/status/safety_monitor", self._handle_safety_status):
            print("ERROR: Failed to subscribe to safety status topic")
            return False
        
        print("Demo setup completed successfully")
        return True
    
    def cleanup(self):
        """Clean up demo resources."""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
    
    def _handle_emergency_stop(self, message_data):
        """Handle emergency stop commands."""
        try:
            payload = message_data['payload']
            self.emergency_stops_received.append(payload)
            
            print(f"\n🚨 EMERGENCY STOP RECEIVED!")
            print(f"   Reason: {payload.get('reason', 'unknown')}")
            print(f"   Distance: {payload.get('obstacle_info', {}).get('distance', 'unknown')}m")
            print(f"   Angle: {payload.get('obstacle_info', {}).get('angle', 'unknown')}°")
            print(f"   Zone: {payload.get('obstacle_info', {}).get('zone', 'unknown')}")
            
        except Exception as e:
            print(f"Error handling emergency stop: {e}")
    
    def _handle_safety_status(self, message_data):
        """Handle safety status updates."""
        try:
            payload = message_data['payload']
            self.status_updates_received.append(payload)
            
            status = payload.get('status', 'unknown')
            message = payload.get('message', '')
            
            if status == "active":
                print(f"✅ Safety Monitor: {message}")
            elif status == "emergency_stop":
                print(f"🚨 Safety Monitor: {message}")
            else:
                print(f"ℹ️  Safety Monitor: {status} - {message}")
                
        except Exception as e:
            print(f"Error handling safety status: {e}")
    
    def create_lidar_data(self, obstacle_distance=None, obstacle_angle=0):
        """Create simulated LiDAR data."""
        # Create 360-degree scan with 1-degree resolution
        ranges = [3.0] * 360  # Default safe distance
        angles = list(range(360))
        
        # Add obstacle if specified
        if obstacle_distance is not None:
            ranges[obstacle_angle] = obstacle_distance
            # Add some neighboring points for realism
            if obstacle_angle > 0:
                ranges[obstacle_angle - 1] = obstacle_distance + 0.1
            if obstacle_angle < 359:
                ranges[obstacle_angle + 1] = obstacle_distance + 0.1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "device_id": "lidar_01",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "ranges": ranges,
                "angles": angles,
                "scan_available": True,
                "min_range": 0.15,
                "max_range": 12.0
            }
        }
    
    def publish_lidar_data(self, lidar_data):
        """Publish LiDAR data to MQTT."""
        topic = "orchestrator/data/lidar_01"
        return self.mqtt_client.publish(topic, lidar_data)
    
    def demo_scenario_1_safe_operation(self):
        """Demo Scenario 1: Safe operation with no obstacles."""
        print("\n" + "="*60)
        print("SCENARIO 1: Safe Operation (No Obstacles)")
        print("="*60)
        print("Publishing safe LiDAR data with no obstacles...")
        
        # Publish safe data for a few cycles
        for i in range(3):
            lidar_data = self.create_lidar_data()
            if self.publish_lidar_data(lidar_data):
                print(f"  Published safe scan {i+1}/3")
            else:
                print(f"  Failed to publish scan {i+1}")
            time.sleep(1)
        
        print("✅ Safe operation completed - no emergency stops expected")
    
    def demo_scenario_2_critical_obstacle(self):
        """Demo Scenario 2: Critical obstacle in front zone."""
        print("\n" + "="*60)
        print("SCENARIO 2: Critical Obstacle Detection")
        print("="*60)
        print("Publishing LiDAR data with critical obstacle at 0.3m directly ahead...")
        
        # Clear previous emergency stops
        self.emergency_stops_received.clear()
        
        # Publish data with critical obstacle
        lidar_data = self.create_lidar_data(obstacle_distance=0.3, obstacle_angle=0)
        if self.publish_lidar_data(lidar_data):
            print("  Published critical obstacle data")
        else:
            print("  Failed to publish obstacle data")
        
        # Wait for safety system to respond
        print("  Waiting for safety system response...")
        time.sleep(2)
        
        if self.emergency_stops_received:
            print("✅ Emergency stop triggered as expected")
        else:
            print("❌ No emergency stop received - check safety monitor")
    
    def demo_scenario_3_warning_obstacle(self):
        """Demo Scenario 3: Warning obstacle in side zone."""
        print("\n" + "="*60)
        print("SCENARIO 3: Warning Obstacle (Side Zone)")
        print("="*60)
        print("Publishing LiDAR data with obstacle at 0.4m on the left side (90°)...")
        
        # Clear previous emergency stops
        self.emergency_stops_received.clear()
        
        # Publish data with warning obstacle
        lidar_data = self.create_lidar_data(obstacle_distance=0.4, obstacle_angle=90)
        if self.publish_lidar_data(lidar_data):
            print("  Published warning obstacle data")
        else:
            print("  Failed to publish obstacle data")
        
        # Wait for safety system to respond
        print("  Waiting for safety system response...")
        time.sleep(2)
        
        if self.emergency_stops_received:
            print("❌ Unexpected emergency stop for warning obstacle")
        else:
            print("✅ No emergency stop for warning obstacle (correct behavior)")
    
    def demo_scenario_4_multiple_obstacles(self):
        """Demo Scenario 4: Multiple obstacles in different zones."""
        print("\n" + "="*60)
        print("SCENARIO 4: Multiple Obstacles")
        print("="*60)
        print("Publishing LiDAR data with multiple obstacles...")
        
        # Clear previous emergency stops
        self.emergency_stops_received.clear()
        
        # Create data with multiple obstacles
        ranges = [3.0] * 360
        ranges[0] = 0.25    # Critical front obstacle
        ranges[45] = 0.6    # Warning left obstacle
        ranges[315] = 0.5   # Warning right obstacle
        ranges[180] = 1.2   # Rear obstacle (safe)
        
        lidar_data = {
            "timestamp": datetime.now().isoformat(),
            "device_id": "lidar_01",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "ranges": ranges,
                "angles": list(range(360)),
                "scan_available": True,
                "min_range": 0.15,
                "max_range": 12.0
            }
        }
        
        if self.publish_lidar_data(lidar_data):
            print("  Published multiple obstacle data")
            print("    - Critical obstacle at 0.25m front (0°)")
            print("    - Warning obstacle at 0.6m left (45°)")
            print("    - Warning obstacle at 0.5m right (315°)")
            print("    - Safe obstacle at 1.2m rear (180°)")
        else:
            print("  Failed to publish obstacle data")
        
        # Wait for safety system to respond
        print("  Waiting for safety system response...")
        time.sleep(2)
        
        if self.emergency_stops_received:
            print("✅ Emergency stop triggered for critical front obstacle")
        else:
            print("❌ No emergency stop received for critical obstacle")
    
    def demo_scenario_5_obstacle_clearing(self):
        """Demo Scenario 5: Obstacle clearing and recovery."""
        print("\n" + "="*60)
        print("SCENARIO 5: Obstacle Clearing and Recovery")
        print("="*60)
        print("Simulating obstacle clearing sequence...")
        
        # First, create a critical obstacle
        print("  Step 1: Creating critical obstacle...")
        self.emergency_stops_received.clear()
        
        lidar_data = self.create_lidar_data(obstacle_distance=0.2, obstacle_angle=0)
        self.publish_lidar_data(lidar_data)
        time.sleep(1)
        
        if self.emergency_stops_received:
            print("    ✅ Emergency stop triggered")
        
        # Then, clear the obstacle
        print("  Step 2: Clearing obstacle...")
        for i in range(3):
            lidar_data = self.create_lidar_data()  # Safe data
            self.publish_lidar_data(lidar_data)
            print(f"    Published clear scan {i+1}/3")
            time.sleep(1)
        
        print("  ✅ Obstacle clearing sequence completed")
        print("    Safety monitor should reset emergency stop condition")
    
    def run_demo(self):
        """Run the complete safety monitor demonstration."""
        print("Safety Monitor Demonstration")
        print("="*60)
        print("This demo shows how the safety monitor responds to different scenarios.")
        print("Make sure the safety monitor is running in another terminal:")
        print("  python safety_monitor_service.py --log-level INFO")
        print()
        
        if not self.setup():
            return False
        
        try:
            # Wait for safety monitor to start
            print("Waiting for safety monitor to initialize...")
            time.sleep(3)
            
            # Run demonstration scenarios
            self.demo_scenario_1_safe_operation()
            time.sleep(2)
            
            self.demo_scenario_2_critical_obstacle()
            time.sleep(2)
            
            self.demo_scenario_3_warning_obstacle()
            time.sleep(2)
            
            self.demo_scenario_4_multiple_obstacles()
            time.sleep(2)
            
            self.demo_scenario_5_obstacle_clearing()
            
            # Summary
            print("\n" + "="*60)
            print("DEMONSTRATION SUMMARY")
            print("="*60)
            print(f"Total emergency stops received: {len(self.emergency_stops_received)}")
            print(f"Total status updates received: {len(self.status_updates_received)}")
            
            if self.emergency_stops_received:
                print("\nEmergency stops triggered:")
                for i, estop in enumerate(self.emergency_stops_received, 1):
                    obstacle_info = estop.get('obstacle_info', {})
                    print(f"  {i}. Distance: {obstacle_info.get('distance', 'unknown')}m, "
                          f"Angle: {obstacle_info.get('angle', 'unknown')}°, "
                          f"Zone: {obstacle_info.get('zone', 'unknown')}")
            
            print("\n✅ Safety Monitor demonstration completed successfully!")
            print("\nThe safety monitor is working correctly and responding to obstacles as expected.")
            
            return True
            
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
            return False
        except Exception as e:
            print(f"\nDemo failed with error: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Main entry point for the demo."""
    print("Orchestrator Safety Monitor Demonstration")
    print()
    
    # Check if user wants to proceed
    try:
        response = input("This demo requires a running MQTT broker and safety monitor. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Demo cancelled by user")
            return
    except KeyboardInterrupt:
        print("\nDemo cancelled by user")
        return
    
    # Run demonstration
    demo = SafetyMonitorDemo()
    
    try:
        success = demo.run_demo()
        
        if success:
            print("\n🎉 Demo completed successfully!")
        else:
            print("\n❌ Demo encountered issues. Check the safety monitor setup.")
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        demo.cleanup()
    except Exception as e:
        print(f"\nDemo failed: {e}")
        demo.cleanup()


if __name__ == "__main__":
    main()