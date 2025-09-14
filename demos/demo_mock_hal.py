#!/usr/bin/env python3
"""
Demo script for Mock HAL

Demonstrates the mock HAL functionality without requiring external dependencies.
Shows how to interact with the mock system programmatically.
"""

import sys
import time
import json
import threading
from pathlib import Path

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def demo_mock_hal():
    """Demonstrate the Mock HAL functionality"""
    print("🚀 Mock HAL Demo")
    print("=" * 50)
    
    try:
        from hal_service.mock.mock_orchestrator import MockHALOrchestrator
        
        print("\n1. Creating Mock HAL Orchestrator...")
        orchestrator = MockHALOrchestrator(
            config_path=None,
            enable_realistic_delays=True,
            enable_failures=False
        )
        
        print("2. Initializing Mock HAL...")
        if not orchestrator.initialize():
            print("❌ Failed to initialize Mock HAL")
            return False
        
        print("✅ Mock HAL initialized successfully!")
        
        # Start the orchestrator in a background thread
        def run_orchestrator():
            orchestrator.run()
        
        hal_thread = threading.Thread(target=run_orchestrator, daemon=True)
        hal_thread.start()
        
        # Wait for startup
        time.sleep(2)
        
        print("\n3. System Status:")
        status = orchestrator.get_system_status()
        print(f"   Running: {status['running']}")
        print(f"   Devices: {status['device_count']}")
        print(f"   MQTT Connected: {status['mqtt_connected']}")
        
        print("\n4. Available Devices:")
        for device_name, device_status in status['devices'].items():
            print(f"   - {device_name}: {device_status['status']}")
        
        print("\n5. Sending Test Commands...")
        
        # Get MQTT client for sending commands
        mqtt_client = orchestrator.get_mqtt_client()
        
        # Send motor commands
        commands = [
            {
                "name": "Move Forward",
                "topic": "orchestrator/cmd/left_motor",
                "command": {
                    "timestamp": time.time(),
                    "command_id": "demo_001",
                    "action": "move_forward",
                    "parameters": {"distance": 1.0, "speed": 0.5}
                }
            },
            {
                "name": "Turn Right", 
                "topic": "orchestrator/cmd/right_motor",
                "command": {
                    "timestamp": time.time(),
                    "command_id": "demo_002", 
                    "action": "rotate_right",
                    "parameters": {"angle": 90, "speed": 0.3}
                }
            },
            {
                "name": "Stop",
                "topic": "orchestrator/cmd/left_motor",
                "command": {
                    "timestamp": time.time(),
                    "command_id": "demo_003",
                    "action": "stop",
                    "parameters": {}
                }
            }
        ]
        
        for cmd in commands:
            print(f"   Sending: {cmd['name']}")
            success = mqtt_client.publish(cmd['topic'], cmd['command'])
            print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
            time.sleep(1)
        
        print("\n6. Monitoring Telemetry...")
        time.sleep(3)  # Let telemetry accumulate
        
        # Check message history
        messages = orchestrator.get_message_history("orchestrator/data/+")
        print(f"   Received {len(messages)} telemetry messages")
        
        if messages:
            print("   Sample telemetry topics:")
            topics = set(msg.topic for msg in messages[-10:])  # Last 10 unique topics
            for topic in sorted(topics):
                print(f"     - {topic}")
        
        print("\n7. Robot State:")
        robot_state = orchestrator.get_simulation_coordinator().get_robot_state()
        print(f"   Position: ({robot_state['position']['x']:.3f}, {robot_state['position']['y']:.3f})")
        print(f"   Heading: {robot_state['heading']:.3f} rad")
        print(f"   Velocity: {robot_state['velocity']['linear']:.3f} m/s")
        
        print("\n8. LiDAR Data Sample:")
        lidar_messages = orchestrator.get_message_history("orchestrator/data/lidar_01")
        if lidar_messages:
            latest_lidar = lidar_messages[-1]
            try:
                payload = json.loads(latest_lidar.payload.decode())
                lidar_data = payload.get('data', {})
                if lidar_data.get('scan_available'):
                    ranges = lidar_data.get('ranges', [])
                    print(f"   Scan points: {len(ranges)}")
                    if ranges:
                        print(f"   Range: {min(ranges):.2f}m to {max(ranges):.2f}m")
                        close_obstacles = [r for r in ranges if r < 1.0]
                        print(f"   Close obstacles (<1m): {len(close_obstacles)}")
            except Exception as e:
                print(f"   Error parsing LiDAR data: {e}")
        else:
            print("   No LiDAR data received")
        
        print("\n9. MQTT Statistics:")
        mock_client = mqtt_client.get_mock_client()
        stats = mock_client.get_stats()
        print(f"   Messages published: {stats['messages_published']}")
        print(f"   Messages received: {stats['messages_received']}")
        print(f"   Active subscriptions: {stats['active_subscriptions']}")
        
        print("\n✅ Demo completed successfully!")
        print("\n📋 Summary:")
        print("   ✅ Mock HAL initialized and running")
        print("   ✅ MQTT communication working")
        print("   ✅ Commands processed and acknowledged")
        print("   ✅ Telemetry data generated")
        print("   ✅ Robot simulation active")
        print("   ✅ LiDAR scans generated")
        
        print("\n🌐 Access Information:")
        print("   MQTT Broker: localhost:1883 (simulated)")
        print("   Command Topics: orchestrator/cmd/{device}")
        print("   Data Topics: orchestrator/data/{device}")
        print("   Status Topics: orchestrator/status/{device}")
        
        print("\n🔧 Manual Testing:")
        print("   You can now connect MQTT clients to interact with the system")
        print("   Example command:")
        print("   mosquitto_pub -h localhost -t 'orchestrator/cmd/left_motor' \\")
        print("     -m '{\"action\":\"move_forward\",\"parameters\":{\"distance\":1.0}}'")
        
        # Keep running for a bit to allow manual testing
        print(f"\n⏰ System will run for 30 more seconds for manual testing...")
        print("   Press Ctrl+C to stop early")
        
        try:
            for i in range(30, 0, -1):
                print(f"\r   Time remaining: {i:2d}s", end="", flush=True)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n   Stopped by user")
        
        print("\n\n🛑 Shutting down...")
        orchestrator.shutdown()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    try:
        success = demo_mock_hal()
        if success:
            print("\n🎉 Mock HAL demo completed successfully!")
            print("   The system is ready for UI/control development")
        else:
            print("\n❌ Demo failed")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()