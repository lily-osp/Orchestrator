#!/usr/bin/env python3
"""
Example script demonstrating the structured logging service.

This script shows how to use the logging service with different components
and demonstrates the JSON output format and standardized message structure.
"""

import time
from hal_service import (
    configure_logging, 
    get_logger, 
    log_startup, 
    log_shutdown,
    get_logging_service
)


def main():
    """Demonstrate the logging service functionality."""
    
    # Configure logging with custom settings
    logging_config = {
        "level": "DEBUG",
        "format": "json",
        "console_output": True,
        "file_output": True,
        "log_dir": "example_logs"
    }
    
    configure_logging(logging_config)
    
    # Log system startup
    log_startup("0.1.0", "example_config.yaml")
    
    # Get different types of loggers
    system_logger = get_logger("system")
    device_logger = get_logging_service().get_device_logger("motor_01")
    service_logger = get_logging_service().get_service_logger("mqtt_client")
    
    # Demonstrate basic logging levels
    system_logger.debug("System debug message", component="example")
    system_logger.info("System started successfully", startup_time=time.time())
    system_logger.warning("This is a warning message", warning_type="example")
    
    # Demonstrate device-specific logging
    device_logger.log_device_event("motor_01", "initialization", "success", voltage=12.5)
    device_logger.log_device_event("motor_01", "command_received", "success", 
                                  command="move_forward", distance=100)
    
    # Demonstrate MQTT event logging
    service_logger.log_mqtt_event("orchestrator/cmd/motor_01", "subscribe", "success")
    service_logger.log_mqtt_event("orchestrator/data/lidar", "publish", "success", 
                                message_size=1024)
    
    # Demonstrate performance metrics
    device_logger.log_performance_metric("motor_speed", 1.5, "m/s", motor_id="motor_01")
    device_logger.log_performance_metric("cpu_usage", 45.2, "%")
    
    # Demonstrate context logging
    with device_logger.context(operation="calibration", phase="startup"):
        device_logger.info("Starting motor calibration")
        time.sleep(0.1)  # Simulate work
        device_logger.info("Calibration completed successfully")
    
    # Demonstrate error logging with exception
    try:
        # Simulate an error
        raise ValueError("Example error for demonstration")
    except Exception:
        device_logger.exception("An error occurred during operation")
    
    # Demonstrate structured context
    device_logger.set_context(motor_type="dc", max_speed=2.0)
    device_logger.info("Motor configuration loaded")
    device_logger.clear_context()
    
    # Log system shutdown
    log_shutdown("example_complete")
    
    print("\nLogging example completed. Check the console output above and 'example_logs/orchestrator.log' file.")


if __name__ == "__main__":
    main()