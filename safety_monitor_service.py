#!/usr/bin/env python3
"""
Standalone Safety Monitor Service for Orchestrator Platform

This script runs the safety monitoring subsystem as a dedicated, high-priority process
that operates independently of the main HAL service.

Usage:
    python safety_monitor_service.py [--config config.yaml] [--priority high]
    
Requirements covered: 5.1, 5.2, 5.3, 5.4
"""

import os
import sys
import time
import signal
import argparse
import logging
from pathlib import Path

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent / "hal_service"))

from hal_service.safety_monitor import SafetyMonitor


def set_process_priority():
    """Set high process priority for safety-critical operation."""
    try:
        import psutil
        
        # Get current process
        process = psutil.Process()
        
        # Set high priority (requires appropriate permissions)
        if sys.platform == "linux":
            # Set nice value to -10 (higher priority)
            os.nice(-10)
            print("Set process priority to high (nice -10)")
        elif sys.platform == "win32":
            # Set high priority class on Windows
            process.nice(psutil.HIGH_PRIORITY_CLASS)
            print("Set process priority to HIGH_PRIORITY_CLASS")
        else:
            print(f"Priority setting not implemented for platform: {sys.platform}")
            
    except ImportError:
        print("psutil not available - cannot set process priority")
    except PermissionError:
        print("Insufficient permissions to set high priority")
    except Exception as e:
        print(f"Failed to set process priority: {e}")


def setup_logging(log_level: str):
    """Set up logging for the safety monitor service."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "safety_monitor.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("paho.mqtt").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down safety monitor service...")
    if 'safety_monitor' in globals():
        safety_monitor.stop()
    sys.exit(0)


def check_dependencies():
    """Check that required dependencies are available."""
    required_modules = [
        "paho.mqtt.client",
        "yaml", 
        "pydantic"
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("ERROR: Missing required dependencies:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nInstall missing dependencies with:")
        print("  pip install paho-mqtt PyYAML pydantic")
        return False
    
    return True


def validate_config(config_path: str) -> bool:
    """Validate that the configuration file exists and is readable."""
    if not config_path:
        return True  # Will use default config
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        return False
    
    if not config_file.is_file():
        print(f"ERROR: Configuration path is not a file: {config_path}")
        return False
    
    try:
        with open(config_file, 'r') as f:
            import yaml
            yaml.safe_load(f)
        print(f"Configuration file validated: {config_path}")
        return True
    except Exception as e:
        print(f"ERROR: Invalid configuration file: {e}")
        return False


def main():
    """Main entry point for the safety monitor service."""
    parser = argparse.ArgumentParser(
        description="Orchestrator Safety Monitor Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python safety_monitor_service.py
  python safety_monitor_service.py --config config.yaml --priority high
  python safety_monitor_service.py --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file (default: config.yaml)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--priority",
        type=str,
        choices=["normal", "high"],
        default="high",
        help="Process priority level (default: high)"
    )
    
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon process (background)"
    )
    
    parser.add_argument(
        "--pid-file",
        type=str,
        help="Write process ID to specified file"
    )
    
    args = parser.parse_args()
    
    # Validate dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Validate configuration
    if not validate_config(args.config):
        sys.exit(1)
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Set process priority if requested
    if args.priority == "high":
        set_process_priority()
    
    # Write PID file if requested
    if args.pid_file:
        try:
            with open(args.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"PID written to {args.pid_file}")
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Handle daemon mode
    if args.daemon:
        try:
            # Fork to background (Unix only)
            if os.fork() > 0:
                sys.exit(0)  # Parent process exits
        except AttributeError:
            logger.warning("Daemon mode not supported on this platform")
        except OSError as e:
            logger.error(f"Failed to fork daemon process: {e}")
            sys.exit(1)
    
    try:
        logger.info("Starting Orchestrator Safety Monitor Service")
        logger.info(f"Configuration: {args.config or 'default'}")
        logger.info(f"Log level: {args.log_level}")
        logger.info(f"Priority: {args.priority}")
        logger.info(f"PID: {os.getpid()}")
        
        # Create and start safety monitor
        global safety_monitor
        safety_monitor = SafetyMonitor(args.config)
        
        if not safety_monitor.start():
            logger.error("Failed to start safety monitor")
            sys.exit(1)
        
        logger.info("Safety monitor started successfully")
        print("Safety monitor service is running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while safety_monitor.running:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.exception(f"Fatal error in safety monitor service: {e}")
        sys.exit(1)
    finally:
        # Clean up
        if 'safety_monitor' in globals():
            safety_monitor.stop()
        
        # Remove PID file
        if args.pid_file and os.path.exists(args.pid_file):
            try:
                os.remove(args.pid_file)
                logger.info(f"Removed PID file {args.pid_file}")
            except Exception as e:
                logger.error(f"Failed to remove PID file: {e}")
        
        logger.info("Safety monitor service stopped")


if __name__ == "__main__":
    main()