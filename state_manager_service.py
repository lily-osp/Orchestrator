#!/usr/bin/env python3
"""
State Manager Service - Standalone service for robot state management

This script runs the state management service as a standalone process,
suitable for deployment as a systemd service.

Usage:
    python3 state_manager_service.py [--config CONFIG_FILE]
"""

import argparse
import signal
import sys
import time
from pathlib import Path

# Add hal_service to path
sys.path.insert(0, str(Path(__file__).parent / "hal_service"))

from hal_service.state_manager import StateManager
from hal_service.mqtt_client import MQTTConfig
from hal_service.config import load_config
from hal_service.logging_service import get_logging_service


class StateManagerService:
    """Standalone State Manager Service"""
    
    def __init__(self, config_path: str = None):
        """Initialize the service with configuration."""
        self.config_path = config_path
        self.state_manager = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the state manager service."""
        try:
            # Load configuration
            print("Loading configuration...")
            config = load_config(self.config_path)
            
            # Initialize logging
            logging_service = get_logging_service()
            logging_service.configure_logging(config.system.logging)
            logger = logging_service.get_device_logger("state_manager_service")
            
            logger.info("Starting State Manager Service")
            
            # Create MQTT configuration
            mqtt_config = MQTTConfig(
                broker_host=config.mqtt.broker_host,
                broker_port=config.mqtt.broker_port,
                keepalive=config.mqtt.keepalive,
                client_id="state_manager_service",
                username=getattr(config.mqtt, 'username', None),
                password=getattr(config.mqtt, 'password', None)
            )
            
            # Get wheel base from configuration (default to 0.3m)
            wheel_base = 0.3  # Default wheel base
            
            # Try to get wheel base from motor configuration
            if config.motors and len(config.motors) >= 2:
                # Calculate wheel base from motor positions if available
                # For now, use default value
                pass
            
            # Create and start state manager
            self.state_manager = StateManager(
                mqtt_config=mqtt_config,
                wheel_base=wheel_base,
                publish_rate=10.0  # 10 Hz state publishing
            )
            
            if not self.state_manager.start():
                logger.error("Failed to start state manager")
                return False
            
            self.running = True
            logger.info("State Manager Service started successfully")
            
            # Main service loop
            try:
                while self.running:
                    time.sleep(1.0)
                    
                    # Check if state manager is still running
                    if not self.state_manager._running:
                        logger.error("State manager stopped unexpectedly")
                        break
                        
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
            
            return True
            
        except Exception as e:
            print(f"Error starting service: {e}")
            if hasattr(self, 'logger'):
                self.logger.exception("Failed to start State Manager Service")
            return False
    
    def stop(self):
        """Stop the state manager service."""
        self.running = False
        
        if self.state_manager:
            print("Stopping state manager...")
            self.state_manager.stop()
            
        print("State Manager Service stopped")
    
    def status(self):
        """Get service status."""
        if self.state_manager:
            return self.state_manager.get_status()
        else:
            return {"service": "state_manager", "running": False}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="State Manager Service")
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show service status and exit"
    )
    
    args = parser.parse_args()
    
    # Create service instance
    service = StateManagerService(args.config)
    
    if args.status:
        # Show status and exit
        status = service.status()
        print(f"State Manager Service Status: {status}")
        return
    
    # Start service
    print("Starting State Manager Service...")
    print("Press Ctrl+C to stop")
    
    try:
        success = service.start()
        if not success:
            print("Failed to start service")
            sys.exit(1)
    except Exception as e:
        print(f"Service error: {e}")
        sys.exit(1)
    finally:
        service.stop()


if __name__ == "__main__":
    main()