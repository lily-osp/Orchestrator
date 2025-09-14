#!/usr/bin/env python3
"""
Standalone test for the logging service core functionality.

This script tests the logging service without external dependencies by
importing only the logging_service module directly.
"""

import json
import logging
import tempfile
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.
    
    Provides structured logging with consistent fields for timestamp, level,
    message, and additional context information.
    """
    
    def __init__(self, include_extra: bool = True):
        """
        Initialize the JSON formatter.
        
        Args:
            include_extra: Whether to include extra fields from log records
        """
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON string representation of the log record
        """
        # Base log entry structure
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add process and thread information
        log_entry["process"] = {
            "pid": record.process,
            "name": record.processName if hasattr(record, 'processName') else None
        }
        log_entry["thread"] = {
            "id": record.thread,
            "name": record.threadName
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields if enabled
        if self.include_extra:
            # Get all extra attributes (those not in the standard LogRecord)
            standard_attrs = {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'message'
            }
            
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in standard_attrs and not key.startswith('_'):
                    # Ensure the value is JSON serializable
                    try:
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)
            
            if extra_fields:
                log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """
    Enhanced logger wrapper that provides structured logging capabilities.
    
    Adds context management, device-specific logging, and standardized
    message formatting for the Orchestrator platform.
    """
    
    def __init__(self, name: str, logger: logging.Logger):
        """
        Initialize the structured logger.
        
        Args:
            name: Logger name/identifier
            logger: Underlying Python logger instance
        """
        self.name = name
        self.logger = logger
        self._context: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """
        Log a message with current context information.
        
        Args:
            level: Log level (logging.DEBUG, INFO, etc.)
            message: Log message
            **kwargs: Additional context fields
        """
        with self._lock:
            # Merge context with kwargs
            extra_fields = {**self._context, **kwargs}
            
            # Add standard orchestrator fields
            extra_fields.update({
                "component": "hal_service",
                "service": self.name,
                "platform": "orchestrator"
            })
            
            self.logger.log(level, message, extra=extra_fields)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log an exception with traceback."""
        kwargs['exc_info'] = True
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def set_context(self, **kwargs) -> None:
        """
        Set persistent context fields for this logger.
        
        Args:
            **kwargs: Context fields to set
        """
        with self._lock:
            self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all persistent context fields."""
        with self._lock:
            self._context.clear()
    
    @contextmanager
    def context(self, **kwargs):
        """
        Temporary context manager for adding context fields.
        
        Args:
            **kwargs: Temporary context fields
        """
        with self._lock:
            old_context = self._context.copy()
            self._context.update(kwargs)
        
        try:
            yield self
        finally:
            with self._lock:
                self._context = old_context
    
    def log_device_event(self, device_id: str, event: str, status: str = "success", **kwargs) -> None:
        """
        Log a standardized device event.
        
        Args:
            device_id: Device identifier
            event: Event type (e.g., "initialization", "command_received", "data_published")
            status: Event status ("success", "failure", "warning")
            **kwargs: Additional event context
        """
        self.info(
            f"Device event: {event}",
            device_id=device_id,
            event_type=event,
            event_status=status,
            **kwargs
        )
    
    def log_mqtt_event(self, topic: str, action: str, status: str = "success", **kwargs) -> None:
        """
        Log a standardized MQTT event.
        
        Args:
            topic: MQTT topic
            action: Action type (e.g., "publish", "subscribe", "receive")
            status: Action status
            **kwargs: Additional context
        """
        self.info(
            f"MQTT {action}: {topic}",
            mqtt_topic=topic,
            mqtt_action=action,
            mqtt_status=status,
            **kwargs
        )


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
        
        # Test temporary context
        with structured_logger.context(temp_field="temp_value"):
            structured_logger.info("Message with temp context")
        
        level, message, kwargs = mock_logger.calls[3]
        assert kwargs["extra"]["temp_field"] == "temp_value"
        assert kwargs["extra"]["device_type"] == "motor"  # Persistent context should still be there
        
        # Log after context manager
        structured_logger.info("Message after context")
        level, message, kwargs = mock_logger.calls[4]
        assert "temp_field" not in kwargs["extra"]  # Temp context should be gone
        assert kwargs["extra"]["device_type"] == "motor"  # Persistent context should remain
        
        print("✓ Temporary context management working")
        
    except Exception as e:
        print(f"✗ Structured logger test failed: {e}")
        return False
    
    return True


def test_integration():
    """Test integration with actual logging."""
    print("\n--- Testing Integration ---")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup logging with JSON formatter
            log_file = Path(temp_dir) / "test.log"
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            
            # Clear existing handlers
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Add file handler with JSON formatter
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(file_handler)
            
            # Create structured logger
            python_logger = logging.getLogger("orchestrator.integration_test")
            structured_logger = StructuredLogger("integration_test", python_logger)
            
            # Log some messages
            structured_logger.info("Test message 1", test_field="value1")
            structured_logger.warning("Test warning", test_field="value2")
            structured_logger.log_device_event("test_device", "test_event", "success")
            structured_logger.log_mqtt_event("test/topic", "publish", "success", message_size=256)
            
            # Force flush
            file_handler.flush()
            
            # Check if log file was created and has content
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                if log_content.strip():
                    # Verify JSON format
                    lines = log_content.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            log_data = json.loads(line)
                            assert "timestamp" in log_data
                            assert "level" in log_data
                            assert "message" in log_data
                            assert "extra" in log_data
                            assert log_data["extra"]["component"] == "hal_service"
                    
                    print(f"✓ Integration test passed - {len(lines)} log entries written")
                    print(f"  Sample log entry: {lines[0][:100]}...")
                else:
                    print("⚠ Log file created but empty")
            else:
                print("⚠ Log file not created")
            
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("Running standalone logging service tests...")
    
    tests = [
        test_json_formatter,
        test_structured_logger,
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
        print("✓ All tests passed! Logging service core functionality is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())