"""
Structured Logging Service for the Orchestrator HAL.

This module provides centralized logging functionality with JSON output format,
standardized log levels, and consistent message formatting for easy parsing and monitoring.
"""

import json
import logging
import logging.handlers
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
        with self._lock:
            # Merge context with kwargs
            extra_fields = {**self._context, **kwargs}
            
            # Add standard orchestrator fields
            extra_fields.update({
                "component": "hal_service",
                "service": self.name,
                "platform": "orchestrator"
            })
            
            # Use exc_info=True directly in the log call, not in extra
            self.logger.log(logging.ERROR, message, extra=extra_fields, exc_info=True)
    
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
    
    def log_performance_metric(self, metric_name: str, value: Union[int, float], unit: str = "", **kwargs) -> None:
        """
        Log a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            **kwargs: Additional context
        """
        self.info(
            f"Performance metric: {metric_name} = {value} {unit}",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            metric_type="performance",
            **kwargs
        )


class LoggingService:
    """
    Centralized logging service for the Orchestrator platform.
    
    Provides configuration, setup, and management of structured logging
    across all HAL components with JSON output and standardized formatting.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the logging service.
        
        Args:
            config: Logging configuration dictionary
        """
        self.config = config or {}
        self._loggers: Dict[str, StructuredLogger] = {}
        self._configured = False
        self._lock = threading.Lock()
        
        # Default configuration
        self.default_config = {
            "level": "INFO",
            "format": "json",
            "max_log_size": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5,
            "log_dir": "logs",
            "console_output": True,
            "file_output": True
        }
    
    def configure(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Configure the logging system.
        
        Args:
            config: Configuration dictionary to merge with defaults
        """
        if config:
            self.config.update(config)
        
        # Merge with defaults
        final_config = {**self.default_config, **self.config}
        
        # Set root logger level
        log_level = getattr(logging, final_config["level"].upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        # Create log directory if needed
        if final_config["file_output"]:
            log_dir = Path(final_config["log_dir"])
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger handlers
        root_logger = logging.getLogger()
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Setup JSON formatter
        json_formatter = JSONFormatter(include_extra=True)
        
        # Console handler
        if final_config["console_output"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(json_formatter)
            console_handler.setLevel(log_level)
            root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if final_config["file_output"]:
            log_file = Path(final_config["log_dir"]) / "orchestrator.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=final_config["max_log_size"],
                backupCount=final_config["backup_count"],
                encoding='utf-8'
            )
            file_handler.setFormatter(json_formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
        
        self._configured = True
    
    def get_logger(self, name: str) -> StructuredLogger:
        """
        Get or create a structured logger instance.
        
        Args:
            name: Logger name/identifier
            
        Returns:
            StructuredLogger instance
        """
        with self._lock:
            if name not in self._loggers:
                # Ensure logging is configured
                if not self._configured:
                    self.configure()
                
                # Create underlying Python logger
                python_logger = logging.getLogger(f"orchestrator.{name}")
                
                # Create structured logger wrapper
                structured_logger = StructuredLogger(name, python_logger)
                self._loggers[name] = structured_logger
            
            return self._loggers[name]
    
    def get_device_logger(self, device_id: str) -> StructuredLogger:
        """
        Get a logger specifically for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            StructuredLogger with device context pre-configured
        """
        logger = self.get_logger(f"device.{device_id}")
        logger.set_context(device_id=device_id, component_type="device")
        return logger
    
    def get_service_logger(self, service_name: str) -> StructuredLogger:
        """
        Get a logger specifically for a service.
        
        Args:
            service_name: Service name
            
        Returns:
            StructuredLogger with service context pre-configured
        """
        logger = self.get_logger(f"service.{service_name}")
        logger.set_context(service_name=service_name, component_type="service")
        return logger
    
    def log_system_startup(self, version: str, config_path: str) -> None:
        """
        Log system startup information.
        
        Args:
            version: System version
            config_path: Configuration file path
        """
        logger = self.get_service_logger("system")
        logger.info(
            "Orchestrator HAL system starting up",
            system_version=version,
            config_path=config_path,
            startup_time=datetime.now().isoformat(),
            event_type="system_startup"
        )
    
    def log_system_shutdown(self, reason: str = "normal") -> None:
        """
        Log system shutdown information.
        
        Args:
            reason: Shutdown reason
        """
        logger = self.get_service_logger("system")
        logger.info(
            "Orchestrator HAL system shutting down",
            shutdown_reason=reason,
            shutdown_time=datetime.now().isoformat(),
            event_type="system_shutdown"
        )
    
    def flush_logs(self) -> None:
        """Force flush all log handlers."""
        for handler in logging.getLogger().handlers:
            handler.flush()
    
    def set_log_level(self, level: str) -> None:
        """
        Change the log level for all loggers.
        
        Args:
            level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        # Update all handlers
        for handler in logging.getLogger().handlers:
            handler.setLevel(log_level)


# Global logging service instance
_logging_service: Optional[LoggingService] = None


def get_logging_service(config: Optional[Dict[str, Any]] = None) -> LoggingService:
    """
    Get the global logging service instance.
    
    Args:
        config: Configuration dictionary (only used on first call)
        
    Returns:
        LoggingService: Global logging service instance
    """
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService(config)
    return _logging_service


def get_logger(name: str) -> StructuredLogger:
    """
    Convenience function to get a structured logger.
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    service = get_logging_service()
    return service.get_logger(name)


def configure_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Convenience function to configure the logging system.
    
    Args:
        config: Configuration dictionary
    """
    service = get_logging_service()
    service.configure(config)


def log_startup(version: str = "unknown", config_path: str = "unknown") -> None:
    """
    Convenience function to log system startup.
    
    Args:
        version: System version
        config_path: Configuration file path
    """
    service = get_logging_service()
    service.log_system_startup(version, config_path)


def log_shutdown(reason: str = "normal") -> None:
    """
    Convenience function to log system shutdown.
    
    Args:
        reason: Shutdown reason
    """
    service = get_logging_service()
    service.log_system_shutdown(reason)