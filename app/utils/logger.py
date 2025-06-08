import logging
import sys
from datetime import datetime
from typing import Any
import json

class CustomFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logger(name: str = "tiktok_api", level: str = "INFO") -> logging.Logger:
    """Setup structured logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger

# Global logger instance
logger = setup_logger()

def log_api_request(endpoint: str, method: str, client_ip: str, **kwargs):
    """Log API request"""
    logger.info(
        f"API Request: {method} {endpoint}",
        extra={
            'event_type': 'api_request',
            'endpoint': endpoint,
            'method': method,
            'client_ip': client_ip,
            **kwargs
        }
    )

def log_api_response(endpoint: str, method: str, status_code: int, duration: float, **kwargs):
    """Log API response"""
    logger.info(
        f"API Response: {method} {endpoint} - {status_code}",
        extra={
            'event_type': 'api_response',
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            **kwargs
        }
    )

def log_ml_prediction(comment_count: int, seeding_count: int, duration: float, **kwargs):
    """Log ML prediction"""
    logger.info(
        f"ML Prediction completed: {comment_count} comments, {seeding_count} seeding detected",
        extra={
            'event_type': 'ml_prediction',
            'comment_count': comment_count,
            'seeding_count': seeding_count,
            'duration_ms': round(duration * 1000, 2),
            **kwargs
        }
    )

def log_error(error: Exception, context: str = "", **kwargs):
    """Log error with context"""
    logger.error(
        f"Error in {context}: {str(error)}",
        extra={
            'event_type': 'error',
            'error_type': type(error).__name__,
            'context': context,
            **kwargs
        },
        exc_info=True
    )