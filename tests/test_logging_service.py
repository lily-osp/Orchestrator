"""
Unit tests for the structured logging service.

Tests the logging service functionality including JSON formatting,
structured logging, context management, and integration with HAL components.
"""

import json
import logging
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from hal_service.logging_service import (
    JSONFormatter,
    StructuredLogger,
    LoggingService,
    get_logging_service,
    configure_logging,
    get_logger
)


class TestJSONFormatter:
    """Test the JSON formatter functionality."""
    
    def test_basic_formatting(self):
        """Test basic log record formatting to JSON."""
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
        
        # Format the record
        formatted = formatter.format(record)
        
        # Parse the JSON output
        log_data = json.loads(formatted)
        
        # Verify required fields
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
        assert "process" in log_data
        assert "thread" in log_data
    
    def test_extra_fields(self):
        """Test inclusion of extra fields in JSON output."""
        formatter = JSONFormatter(include_extra=True)
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.device_id = "motor_01"
        record.event_type = "command_received"
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Verify extra fields are included
        assert "extra" in log_data
        assert log_data["extra"]["device_id"] == "motor_01"
        assert log_data["extra"]["event_type"] == "command_received"
    
    def test_exception_formatting(self):
        """Test exception information formatting."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/test/path.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Verify exception information
        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test exception"
        assert log_data["exception"]["traceback"] is not None


class TestStructuredLogger:
    """Test the structured logger functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock(spec=logging.Logger)
        self.structured_logger = StructuredLogger("test_device", self.mock_logger)
    
    def test_basic_logging(self):
        """Test basic logging methods."""
        self.structured_logger.info("Test message", extra_field="value")
        
        # Verify the underlying logger was called
        self.mock_logger.log.assert_called_once()
        args, kwargs = self.mock_logger.log.call_args
        
        assert args[0] == logging.INFO
        assert args[1] == "Test message"
        assert "extra_field" in kwargs["extra"]
        assert kwargs["extra"]["component"] == "hal_service"
    
    def test_context_management(self):
        """Test context field management."""
        # Set persistent context
        self.structured_logger.set_context(device_type="motor", voltage=12.0)
        
        self.structured_logger.info("Test with context")
        
        # Verify context fields are included
        args, kwargs = self.mock_logger.log.call_args
        assert kwargs["extra"]["device_type"] == "motor"
        assert kwargs["extra"]["voltage"] == 12.0
    
    def test_temporary_context(self):
        """Test temporary context manager."""
        # Set initial context
        self.structured_logger.set_context(permanent_field="value")
        
        with self.structured_logger.context(temp_field="temp_value"):
            self.structured_logger.info("Message with temp context")
            
            # Verify both permanent and temporary fields
            args, kwargs = self.mock_logger.log.call_args
            assert kwargs["extra"]["permanent_field"] == "value"
            assert kwargs["extra"]["temp_field"] == "temp_value"
        
        # Log after context manager
        self.structured_logger.info("Message after context")
        
        # Verify temporary field is removed
        args, kwargs = self.mock_logger.log.call_args
        assert kwargs["extra"]["permanent_field"] == "value"
        assert "temp_field" not in kwargs["extra"]
    
    def test_device_event_logging(self):
        """Test standardized device event logging."""
        self.structured_logger.log_device_event(
            "motor_01", 
            "initialization", 
            "success",
            voltage=12.5
        )
        
        args, kwargs = self.mock_logger.log.call_args
        assert args[1] == "Device event: initialization"
        assert kwargs["extra"]["device_id"] == "motor_01"
        assert kwargs["extra"]["event_type"] == "initialization"
        assert kwargs["extra"]["event_status"] == "success"
        assert kwargs["extra"]["voltage"] == 12.5
    
    def test_mqtt_event_logging(self):
        """Test standardized MQTT event logging."""
        self.structured_logger.log_mqtt_event(
            "orchestrator/cmd/motor", 
            "publish", 
            "success",
            message_size=256
        )
        
        args, kwargs = self.mock_logger.log.call_args
        assert args[1] == "MQTT publish: orchestrator/cmd/motor"
        assert kwargs["extra"]["mqtt_topic"] == "orchestrator/cmd/motor"
        assert kwargs["extra"]["mqtt_action"] == "publish"
        assert kwargs["extra"]["mqtt_status"] == "success"
        assert kwargs["extra"]["message_size"] == 256
    
    def test_performance_metric_logging(self):
        """Test performance metric logging."""
        self.structured_logger.log_performance_metric("cpu_usage", 45.2, "%")
        
        args, kwargs = self.mock_logger.log.call_args
        assert args[1] == "Performance metric: cpu_usage = 45.2 %"
        assert kwargs["extra"]["metric_name"] == "cpu_usage"
        assert kwargs["extra"]["metric_value"] == 45.2
        assert kwargs["extra"]["metric_unit"] == "%"
        assert kwargs["extra"]["metric_type"] == "performance"


class TestLoggingService:
    """Test the logging service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "level": "DEBUG",
            "format": "json",
            "log_dir": self.temp_dir,
            "console_output": False,  # Disable console for tests
            "file_output": True
        }
    
    def test_service_initialization(self):
        """Test logging service initialization."""
        service = LoggingService(self.config)
        assert service.config == self.config
        assert not service._configured
    
    def test_configuration(self):
        """Test logging service configuration."""
        service = LoggingService()
        service.configure(self.config)
        
        assert service._configured
        
        # Verify log directory was created
        log_dir = Path(self.temp_dir)
        assert log_dir.exists()
    
    def test_logger_creation(self):
        """Test structured logger creation."""
        service = LoggingService(self.config)
        
        logger1 = service.get_logger("test_component")
        logger2 = service.get_logger("test_component")
        
        # Should return the same instance
        assert logger1 is logger2
        assert isinstance(logger1, StructuredLogger)
    
    def test_device_logger(self):
        """Test device-specific logger creation."""
        service = LoggingService(self.config)
        
        device_logger = service.get_device_logger("motor_01")
        
        assert isinstance(device_logger, StructuredLogger)
        assert device_logger.name == "device.motor_01"
    
    def test_service_logger(self):
        """Test service-specific logger creation."""
        service = LoggingService(self.config)
        
        service_logger = service.get_service_logger("mqtt_client")
        
        assert isinstance(service_logger, StructuredLogger)
        assert service_logger.name == "service.mqtt_client"
    
    def test_log_level_change(self):
        """Test dynamic log level changes."""
        service = LoggingService(self.config)
        service.configure()
        
        # Change log level
        service.set_log_level("ERROR")
        
        # Verify root logger level changed
        root_logger = logging.getLogger()
        assert root_logger.level == logging.ERROR


class TestGlobalFunctions:
    """Test global convenience functions."""
    
    def test_get_logging_service_singleton(self):
        """Test that get_logging_service returns singleton."""
        # Clear any existing instance
        import hal_service.logging_service
        hal_service.logging_service._logging_service = None
        
        service1 = get_logging_service()
        service2 = get_logging_service()
        
        assert service1 is service2
    
    def test_configure_logging_convenience(self):
        """Test configure_logging convenience function."""
        config = {"level": "WARNING"}
        
        configure_logging(config)
        
        # Verify configuration was applied
        service = get_logging_service()
        assert service._configured
    
    def test_get_logger_convenience(self):
        """Test get_logger convenience function."""
        logger = get_logger("test_component")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test_component"


class TestThreadSafety:
    """Test thread safety of logging service."""
    
    def test_concurrent_logger_creation(self):
        """Test concurrent logger creation is thread-safe."""
        service = LoggingService()
        loggers = {}
        
        def create_logger(name):
            loggers[name] = service.get_logger(f"test_{name}")
        
        # Create multiple threads creating loggers
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_logger, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all loggers were created
        assert len(loggers) == 10
        for i in range(10):
            assert f"test_{i}" in loggers
    
    def test_concurrent_context_updates(self):
        """Test concurrent context updates are thread-safe."""
        service = LoggingService()
        logger = service.get_logger("test_concurrent")
        
        results = []
        
        def update_context(thread_id):
            with logger.context(thread_id=thread_id):
                time.sleep(0.01)  # Small delay to increase chance of race condition
                # Context should be isolated per thread
                results.append(thread_id)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_context, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should have completed successfully
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__])