#!/usr/bin/env python3
"""
Demonstration of the structured logging service.

This script shows the JSON output format and various logging features
without requiring external dependencies.
"""

import json
import logging
import sys
import time
from pathlib import Path

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from logging_service import (
    JSONFormatter,
    StructuredLogger,
    LoggingService
)


def main():
    """Demonstrate the logging service functionality."""
    
    print("=== Orchestrator Structured Logging Service Demo ===\n")
    
    # Configure logging service
    config = {
        "level": "DEBUG",
        "format": "json",
        "console_output": True,
        "file_output": True,
        "log_dir": "demo_logs"
    }
    
    service = LoggingService(config)
    service.configure()
    
    print("1. System startup logging:")
    service.log_system_startup("0.1.0", "demo_config.yaml")
    
    print("\n2. Device-specific logging:")
    device_logger = service.get_device_logger("motor_01")
    device_logger.log_device_event("motor_01", "initialization", "success", voltage=12.5)
    device_logger.log_device_event("motor_01", "command_received", "success", 
                                  command="move_forward", distance=100)
    
    print("\n3. Service-specific logging:")
    mqtt_logger = service.get_service_logger("mqtt_client")
    mqtt_logger.log_mqtt_event("orchestrator/cmd/motor_01", "subscribe", "success")
    mqtt_logger.log_mqtt_event("orchestrator/data/lidar", "publish", "success", 
                              message_size=1024)
    
    print("\n4. Performance metrics:")
    device_logger.log_performance_metric("motor_speed", 1.5, "m/s")
    device_logger.log_performance_metric("cpu_usage", 45.2, "%")
    
    print("\n5. Context logging:")
    device_logger.set_context(motor_type="dc", max_speed=2.0)
    device_logger.info("Motor configuration loaded")
    
    with device_logger.context(operation="calibration"):
        device_logger.info("Starting motor calibration")
        device_logger.info("Calibration completed successfully")
    
    print("\n6. Error logging:")
    try:
        # Simulate an error
        raise ValueError("Example error for demonstration")
    except Exception:
        device_logger.exception("An error occurred during operation")
    
    print("\n7. Different log levels:")
    system_logger = service.get_logger("system")
    system_logger.debug("Debug message", debug_info="detailed_info")
    system_logger.info("Info message", status="operational")
    system_logger.warning("Warning message", warning_type="configuration")
    system_logger.error("Error message", error_code="E001")
    
    print("\n8. System shutdown logging:")
    service.log_system_shutdown("demo_complete")
    
    # Flush all logs
    service.flush_logs()
    
    print(f"\n=== Demo Complete ===")
    print(f"Check 'demo_logs/orchestrator.log' for the complete JSON log output.")
    
    # Show a sample of what the log file contains
    log_file = Path("demo_logs/orchestrator.log")
    if log_file.exists():
        print(f"\nSample log entries from {log_file}:")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:3]):  # Show first 3 entries
                if line.strip():
                    log_data = json.loads(line)
                    print(f"  {i+1}. {log_data['level']}: {log_data['message']}")
                    print(f"     Timestamp: {log_data['timestamp']}")
                    if 'extra' in log_data:
                        print(f"     Context: {list(log_data['extra'].keys())}")
        
        if len(lines) > 3:
            print(f"     ... and {len(lines) - 3} more entries")


if __name__ == "__main__":
    main()