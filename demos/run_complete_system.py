#!/usr/bin/env python3
"""
Complete System Launcher for Orchestrator Platform

This script launches the complete Orchestrator system including:
1. Mock HAL (Hardware Abstraction Layer)
2. MQTT Broker (Mosquitto)
3. Node-RED with Dashboard UI

Provides a complete development environment for testing and demonstration.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import json
from pathlib import Path
from typing import Optional, List

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

class SystemLauncher:
    """Manages the complete Orchestrator system startup and shutdown"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.mock_hal_thread: Optional[threading.Thread] = None
        self.running = False
        self.project_root = Path(__file__).parent
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down system...")
        self.shutdown()
        sys.exit(0)
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        print("🔍 Checking system dependencies...")
        
        # Check if mosquitto is available
        try:
            result = subprocess.run(['mosquitto', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            print("✅ Mosquitto MQTT broker found")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Mosquitto MQTT broker not found")
            print("   Install with: sudo apt-get install mosquitto mosquitto-clients")
            return False
        
        # Check if Node.js is available
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            version = result.stdout.strip()
            print(f"✅ Node.js found: {version}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Node.js not found")
            print("   Install from: https://nodejs.org/")
            return False
        
        # Check if Node-RED is available
        try:
            result = subprocess.run(['node-red', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            version = result.stdout.strip()
            print(f"✅ Node-RED found: {version}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Node-RED not found")
            print("   Install with: npm install -g node-red")
            return False
        
        return True
    
    def start_mqtt_broker(self) -> bool:
        """Start the MQTT broker"""
        print("\n🚀 Starting MQTT Broker...")
        
        try:
            # Check if mosquitto is already running
            result = subprocess.run(['pgrep', 'mosquitto'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ MQTT broker already running")
                return True
            
            # Start mosquitto
            process = subprocess.Popen(
                ['mosquitto', '-v'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(process)
            
            # Wait a moment for startup
            time.sleep(2)
            
            # Check if it's running
            if process.poll() is None:
                print("✅ MQTT broker started successfully")
                return True
            else:
                print("❌ MQTT broker failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting MQTT broker: {e}")
            return False
    
    def start_mock_hal(self) -> bool:
        """Start the Mock HAL in a separate thread"""
        print("\n🤖 Starting Mock HAL...")
        
        try:
            def run_mock_hal():
                try:
                    from hal_service.mock.mock_orchestrator import MockHALOrchestrator
                    
                    # Create mock orchestrator
                    orchestrator = MockHALOrchestrator(
                        config_path=None,  # Use default config
                        enable_realistic_delays=True,
                        enable_failures=False
                    )
                    
                    # Initialize and run
                    if orchestrator.initialize():
                        print("✅ Mock HAL initialized successfully")
                        orchestrator.run()
                    else:
                        print("❌ Mock HAL initialization failed")
                        
                except Exception as e:
                    print(f"❌ Error in Mock HAL: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Start in separate thread
            self.mock_hal_thread = threading.Thread(target=run_mock_hal, daemon=True)
            self.mock_hal_thread.start()
            
            # Wait a moment for startup
            time.sleep(3)
            
            print("✅ Mock HAL started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error starting Mock HAL: {e}")
            return False
    
    def start_node_red(self) -> bool:
        """Start Node-RED with the Orchestrator configuration"""
        print("\n🌐 Starting Node-RED...")
        
        try:
            node_red_dir = self.project_root / "configs" / "node_red_config"
            
            # Check if Node-RED directory exists
            if not node_red_dir.exists():
                print(f"❌ Node-RED config directory not found: {node_red_dir}")
                return False
            
            # Start Node-RED
            process = subprocess.Popen(
                ['node-red', '--userDir', str(node_red_dir)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(node_red_dir)
            )
            
            self.processes.append(process)
            
            # Wait for startup
            print("   Waiting for Node-RED to start...")
            time.sleep(10)
            
            # Check if it's running
            if process.poll() is None:
                print("✅ Node-RED started successfully")
                return True
            else:
                stdout, stderr = process.communicate(timeout=1)
                print(f"❌ Node-RED failed to start")
                print(f"   stdout: {stdout}")
                print(f"   stderr: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Node-RED: {e}")
            return False
    
    def wait_for_services(self) -> bool:
        """Wait for all services to be ready"""
        print("\n⏳ Waiting for services to be ready...")
        
        # Test MQTT connection
        try:
            import paho.mqtt.client as mqtt
            
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            result = client.connect("localhost", 1883, 60)
            if result == 0:
                print("✅ MQTT broker is ready")
                client.disconnect()
            else:
                print("❌ MQTT broker connection failed")
                return False
        except Exception as e:
            print(f"❌ MQTT test failed: {e}")
            return False
        
        # Test Node-RED
        try:
            import urllib.request
            import urllib.error
            
            # Try to access Node-RED admin interface
            try:
                response = urllib.request.urlopen("http://localhost:1880", timeout=5)
                print("✅ Node-RED web interface is ready")
            except urllib.error.URLError:
                print("⚠️  Node-RED web interface not yet ready (this is normal)")
        except Exception as e:
            print(f"⚠️  Node-RED test inconclusive: {e}")
        
        return True
    
    def print_access_info(self):
        """Print information about how to access the system"""
        print("\n" + "=" * 60)
        print("🎉 ORCHESTRATOR SYSTEM READY!")
        print("=" * 60)
        
        print("\n📡 MQTT Broker:")
        print("   Host: localhost")
        print("   Port: 1883")
        print("   Test: mosquitto_pub -h localhost -t test/topic -m 'Hello World'")
        
        print("\n🤖 Mock HAL:")
        print("   Status: Running (simulating hardware)")
        print("   MQTT Topics:")
        print("     Commands: orchestrator/cmd/{device}")
        print("     Data: orchestrator/data/{device}")
        print("     Status: orchestrator/status/{device}")
        
        print("\n🌐 Node-RED Interface:")
        print("   Flow Editor: http://localhost:1880")
        print("   Dashboard: http://localhost:1880/ui")
        print("   API: http://localhost:1880/api")
        
        print("\n🎮 Quick Test Commands:")
        print("   # Send motor command via MQTT")
        print("   mosquitto_pub -h localhost -t 'orchestrator/cmd/left_motor' \\")
        print("     -m '{\"action\":\"move_forward\",\"parameters\":{\"distance\":1.0,\"speed\":0.5}}'")
        print("")
        print("   # Monitor telemetry")
        print("   mosquitto_sub -h localhost -t 'orchestrator/data/+'")
        
        print("\n🛑 To stop the system: Press Ctrl+C")
        print("=" * 60)
    
    def run(self) -> bool:
        """Run the complete system"""
        print("🚀 Starting Orchestrator Platform Complete System")
        print("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            print("\n❌ Dependency check failed. Please install missing components.")
            return False
        
        # Start services in order
        if not self.start_mqtt_broker():
            print("\n❌ Failed to start MQTT broker")
            return False
        
        if not self.start_mock_hal():
            print("\n❌ Failed to start Mock HAL")
            return False
        
        if not self.start_node_red():
            print("\n❌ Failed to start Node-RED")
            return False
        
        # Wait for services to be ready
        if not self.wait_for_services():
            print("\n❌ Services not ready")
            return False
        
        # Print access information
        self.print_access_info()
        
        # Keep running
        self.running = True
        try:
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                for process in self.processes[:]:  # Copy list to avoid modification during iteration
                    if process.poll() is not None:
                        print(f"\n⚠️  Process {process.pid} has stopped")
                        self.processes.remove(process)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
        
        return True
    
    def shutdown(self):
        """Shutdown all services"""
        print("\n🛑 Shutting down Orchestrator system...")
        
        self.running = False
        
        # Stop processes
        for process in self.processes:
            try:
                print(f"   Stopping process {process.pid}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Force killing process {process.pid}...")
                    process.kill()
                    
            except Exception as e:
                print(f"   Error stopping process: {e}")
        
        # Wait for Mock HAL thread
        if self.mock_hal_thread and self.mock_hal_thread.is_alive():
            print("   Waiting for Mock HAL to stop...")
            self.mock_hal_thread.join(timeout=5)
        
        print("✅ System shutdown complete")


def main():
    """Main entry point"""
    launcher = SystemLauncher()
    
    try:
        success = launcher.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        launcher.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()