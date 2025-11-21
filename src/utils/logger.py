"""
Structured logging utility for CloudWatch compatibility.

Provides JSON-formatted logging that works well with CloudWatch Logs Insights
for querying and monitoring in production.
"""

import logging
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime


class StructuredLogger:
    """
    JSON structured logger optimized for AWS CloudWatch.

    Features:
    - JSON formatted output for CloudWatch Logs Insights
    - Automatic timestamp inclusion
    - Request ID tracking for tracing
    - Extra context fields support
    - Standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_request_received",
        ...             question_length=100,
        ...             backend="bedrock")
        {"timestamp": "2025-11-21T10:30:00Z", "level": "INFO", ...}
    """

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Add JSON formatter for CloudWatch
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def _log(self, level: str, event: str, exc_info: bool = False, **kwargs):
        """Internal logging method."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **kwargs
        }

        # Map to standard logging levels
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }

        self.logger.log(
            level_map[level],
            json.dumps(log_data, default=str),
            exc_info=exc_info
        )

    def debug(self, event: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", event, **kwargs)

    def info(self, event: str, **kwargs):
        """Log info message."""
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs):
        """Log warning message."""
        self._log("WARNING", event, **kwargs)

    def error(self, event: str, exc_info: bool = False, **kwargs):
        """
        Log error message.

        Args:
            event: Error event name
            exc_info: Include exception traceback
            **kwargs: Additional context fields
        """
        self._log("ERROR", event, exc_info=exc_info, **kwargs)

    def critical(self, event: str, exc_info: bool = False, **kwargs):
        """Log critical message."""
        self._log("CRITICAL", event, exc_info=exc_info, **kwargs)


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON.

    The log record message is already JSON from StructuredLogger,
    so we just pass it through.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        # If exception info exists, add it
        if record.exc_info:
            import traceback
            exc_text = ''.join(traceback.format_exception(*record.exc_info))
            # Parse the existing JSON and add exception
            try:
                log_data = json.loads(record.getMessage())
                log_data['exception'] = exc_text
                return json.dumps(log_data, default=str)
            except json.JSONDecodeError:
                # Fallback if message isn't JSON
                return record.getMessage()

        return record.getMessage()


# Module-level logger cache
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """
    Get or create a structured logger.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)

    Returns:
        StructuredLogger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("processing_started", request_id="abc123")
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]


# Convenience function for Lambda context
def add_lambda_context(context: Any) -> Dict[str, Any]:
    """
    Extract useful context from AWS Lambda context object.

    Args:
        context: AWS Lambda context

    Returns:
        Dict with request_id, function_name, memory_limit

    Example:
        >>> context_data = add_lambda_context(context)
        >>> logger.info("request_received", **context_data)
    """
    if context is None:
        return {}

    return {
        "request_id": getattr(context, 'aws_request_id', None),
        "function_name": getattr(context, 'function_name', None),
        "memory_limit_mb": getattr(context, 'memory_limit_in_mb', None),
        "remaining_time_ms": getattr(context, 'get_remaining_time_in_millis', lambda: None)()
    }
