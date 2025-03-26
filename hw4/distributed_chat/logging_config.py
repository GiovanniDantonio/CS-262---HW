"""
Centralized logging configuration for the distributed chat system.
Provides consistent logging format and configuration across all components.
"""
import os
import json
import logging
import logging.handlers
from datetime import datetime

def setup_logger(name, log_dir='logs', log_level=logging.DEBUG):
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name (e.g., 'chat_client', 'chat_server')
        log_dir: Directory to store log files
        log_level: Logging level (default: DEBUG)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False  # Don't propagate to parent loggers
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Common log format with more detailed information
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(threadName)s - '
        '%(filename)s:%(lineno)d - %(funcName)s - %(message)s'
    )
    
    # Console handler with color coding
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)
    
    return logger

def log_error(logger, error, context=None):
    """
    Enhanced error logging with context.
    
    Args:
        logger: Logger instance
        error: Exception object
        context: Optional dict with additional context
    """
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {}
    }
    
    if hasattr(error, 'debug_error_string'):
        error_info['debug_info'] = error.debug_error_string()
        
    logger.error(json.dumps(error_info, indent=2))

class RPCLogger:
    """Context manager for logging RPC operations."""
    
    def __init__(self, logger, operation_name, **kwargs):
        self.logger = logger
        self.operation_name = operation_name
        self.context = kwargs
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting {self.operation_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.debug(f"Completed {self.operation_name} in {duration:.3f}s")
        else:
            log_error(self.logger, exc_val, {
                'operation': self.operation_name,
                'duration': duration,
                **self.context
            })
        return False  # Don't suppress exceptions
