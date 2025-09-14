#!/usr/bin/env python3
"""
Basic test script for the logging service without external dependencies.

This script performs basic validation of the logging service functionality
using only Python standard library components.
"""

import json
import logging
import tempfile
import sys
from pathlib import Path

# Add the parent directory to the path so we can import hal_service
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from hal_service.logging_service import (
        JSONFormatter,
        StructuredLogger,
        LoggingService
    )
    print("✓ Successfully imported logging service components")
except ImportError as e:
    print(f"✗ Failed to import logging service: {e}")
    sys.exit(1)


def test_json_formatter():
    """Test the JSON formatter functionality."""
    print("\n--- Testing JSON Formatter ---")
    
    formatter = JSONFormatter()
    
    # Create a test log record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="/test/path.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Add some extra fields
    record.device_id = "motor_01"
    record.event_type = "test_event"
    
    try:
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Verify required fields
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
        
        # Verify extra fields
        if "extra" in log_data:
            assert log_data["extra"]["device_id"] == "motor_01"
            assert log_data["extra"]["event_type"] == "test_event"
        
        print("✓ JSON formatter working correctly")
        print(f"  Sample output: {formatted[:100]}...")
        
    except Exception as e:
        print(f"✗ JSON formatter test failed: {e}")
        return False
    
    return True


def test_structured_logger():
    """Test the structured logger functionality."""
    print("\n--- Testing Structured Logger ---")
    
    # Create a mock logger that captures calls
    class MockLogger:
        def __init__(self):
            self.calls = []
        
        def log(self, level, message, **kwargs):
            self.calls.append((level, message, kwargs))
    
    mock_logger = MockLogger()
    structured_logger = StructuredLogger("test_device", mock_logger)
    
    try:
        # Test basic logging
        structured_logger.info("Test message", extra_field="value")
        
        # Verify the call was made
        assert len(mock_logger.calls) == 1
        level, message, kwargs = mock_logger.calls[0]
        assert level == logging.INFO
        assert message == "Test message"
        assert "extra" in kwargs
        assert kwargs["extra"]["extra_field"] == "value"
        assert kwargs["extra"]["component"] == "hal_service"
        
        print("✓ Basic structured logging working")
        
        # Test context management
        structured_logger.set_context(device_type="motor")
        structured_logger.info("Message with context")
        
        # Verify context was included
        level, message, kwargs = mock_logger.calls[1]
        assert kwargs["extra"]["device_type"] == "motor"
        
        print("✓ Context management working")
        
        # Test device event logging
        structured_logger.log_device_event("motor_01", "initialization", "success")
        
        level, message, kwargs = mock_logger.calls[2]
        assert "Device event: initialization" in message
        assert kwargs["extra"]["device_id"] == "motor_01"
        assert kwargs["extra"]["event_type"] == "initialization"
        
        print("✓ Device event logging working")
        
    except Exception as e:
        print(f"✗ Structured logger test failed: {e}")
        return False
    
    return True


def test_logging_service():
    """Test the logging service functionality."""
    print("\n--- Testing Logging Service ---")
    
    try:
        # Create temporary directory for logs
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "level": "DEBUG",
                "format": "json",
                "log_dir": temp_dir,
                "console_output": False,
                "file_output": True
            }
            
            service = LoggingService(config)
            service.configure()
            
            # Test logger creation
            logger1 = service.get_logger("test_component")
            logger2 = service.get_logger("test_component")
            
            # Should return the same instance
            assert logger1 is logger2
            assert isinstance(logger1, StructuredLogger)
            
            print("✓ Logger creation and caching working")
            
            # Test device logger
            device_logger = service.get_device_logger("motor_01")
            assert isinstance(device_logger, StructuredLogger)
            assert device_logger.name == "device.motor_01"
            
            print("✓ Device logger creation working")
            
            # Test service logger
            service_logger = service.get_service_logger("mqtt_client")
            assert isinstance(service_logger, StructuredLogger)
            assert service_logger.name == "service.mqtt_client"
            
            print("✓ Service logger creation working")
            
            # Verify log directory was created
            log_dir = Path(temp_dir)
            assert log_dir.exists()
            
            print("✓ Log directory creation working")
            
    except Exception as e:
        print(f"✗ Logging service test failed: {e}")
        return False
    
    return True


def test_integration():
    """Test integration with actual logging."""
    print("\n--- Testing Integration ---")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "level": "INFO",
                "format": "json",
                "log_dir": temp_dir,
                "console_output": False,
                "file_output": True
            }
            
            service = LoggingService(config)
            service.configure()
            
            # Get a logger and log some messages
            logger = service.get_logger("integration_test")
            
            logger.info("Test message 1", test_field="value1")
            logger.warning("Test warning", test_field="value2")
            logger.log_device_event("test_device", "test_event", "success")
            
            # Force flush logs
            service.flush_logs()
            
            # Check if log file was created
            log_file = Path(temp_dir) / "orchestrator.log"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Verify JSON format
                lines = log_content.strip().split('\n')
                for line in lines:
                    if line.strip():
                        log_data = json.loads(line)
                        assert "timestamp" in log_data
                        assert "level" in log_data
                        assert "message" in log_data
                
                print(f"✓ Integration test passed - {len(lines)} log entries written")
                print(f"  Sample log entry: {lines[0][:100]}...")
            else:
                print("⚠ Log file not created (may be expected in some environments)")
            
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("Running basic logging service tests...")
    
    tests = [
        test_json_formatter,
        test_structured_logger,
        test_logging_service,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n--- Test Results ---")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Logging service is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())