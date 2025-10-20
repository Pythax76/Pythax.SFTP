"""
Logging and Error Handling Module

This module sets up comprehensive logging and provides utilities
for error handling throughout the SFTP client application.
"""

import os
import logging
import logging.handlers
import traceback
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import threading


class SFTPLogger:
    """
    Custom logger setup for the SFTP client application.
    Provides file and console logging with rotation.
    """
    
    def __init__(self, log_dir: str = None, app_name: str = "sftp_client"):
        """
        Initialize the logger.
        
        Args:
            log_dir: Directory for log files
            app_name: Application name for log files
        """
        self.app_name = app_name
        
        if log_dir is None:
            # Default to logs directory relative to application
            self.log_dir = Path(__file__).parent.parent / "logs"
        else:
            self.log_dir = Path(log_dir)
        
        self.log_dir.mkdir(exist_ok=True)
        
        self.main_log_file = self.log_dir / f"{app_name}.log"
        self.error_log_file = self.log_dir / f"{app_name}_errors.log"
        
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create main logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler for all logs with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.main_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # File handler for errors only
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Log startup
        self.logger.info(f"Logger initialized for {self.app_name}")
        self.logger.info(f"Log directory: {self.log_dir}")
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (uses app name if None)
            
        Returns:
            Logger instance
        """
        if name is None:
            return self.logger
        else:
            return logging.getLogger(f"{self.app_name}.{name}")
    
    def set_level(self, level: str):
        """
        Set the logging level.
        
        Args:
            level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Update console handler level
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(numeric_level)
                break
    
    def log_exception(self, exception: Exception, context: str = None):
        """
        Log an exception with full traceback.
        
        Args:
            exception: Exception to log
            context: Additional context information
        """
        error_msg = f"Exception occurred: {type(exception).__name__}: {str(exception)}"
        if context:
            error_msg = f"{context} - {error_msg}"
        
        self.logger.error(error_msg)
        self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Clean up log files older than specified days.
        
        Args:
            days: Number of days to keep logs
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file}")
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")


class ErrorHandler:
    """
    Centralized error handling for the SFTP client application.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize the error handler.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.error_callbacks = []
        self._lock = threading.Lock()
    
    def add_error_callback(self, callback):
        """
        Add a callback function to be called when errors occur.
        
        Args:
            callback: Function to call with error information
        """
        with self._lock:
            self.error_callbacks.append(callback)
    
    def remove_error_callback(self, callback):
        """
        Remove an error callback.
        
        Args:
            callback: Callback function to remove
        """
        with self._lock:
            if callback in self.error_callbacks:
                self.error_callbacks.remove(callback)
    
    def handle_error(self, error: Exception, context: str = None, 
                    user_message: str = None, critical: bool = False):
        """
        Handle an error with logging and user notification.
        
        Args:
            error: Exception that occurred
            context: Context where error occurred
            user_message: User-friendly error message
            critical: Whether this is a critical error
        """
        # Log the error
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'critical': critical,
            'timestamp': datetime.now().isoformat(),
            'thread': threading.current_thread().name
        }
        
        if critical:
            self.logger.critical(f"Critical error in {context}: {error}")
        else:
            self.logger.error(f"Error in {context}: {error}")
        
        self.logger.debug(f"Full error details: {error_info}")
        self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Notify callbacks
        with self._lock:
            for callback in self.error_callbacks:
                try:
                    callback(error_info, user_message)
                except Exception as e:
                    self.logger.error(f"Error in error callback: {e}")
    
    def handle_connection_error(self, error: Exception, host: str = None):
        """
        Handle connection-specific errors.
        
        Args:
            error: Connection error
            host: Host that failed to connect
        """
        context = f"connection to {host}" if host else "connection"
        user_message = f"Failed to connect to {host}. Please check your connection settings."
        
        self.handle_error(error, context, user_message)
    
    def handle_transfer_error(self, error: Exception, operation: str, 
                            file_path: str = None):
        """
        Handle file transfer errors.
        
        Args:
            error: Transfer error
            operation: Type of operation (upload/download)
            file_path: File path that failed
        """
        context = f"{operation} of {file_path}" if file_path else operation
        user_message = f"Failed to {operation} file. Please check file permissions and connection."
        
        self.handle_error(error, context, user_message)
    
    def handle_authentication_error(self, error: Exception, username: str = None):
        """
        Handle authentication errors.
        
        Args:
            error: Authentication error
            username: Username that failed authentication
        """
        context = f"authentication for {username}" if username else "authentication"
        user_message = "Authentication failed. Please check your username and password."
        
        self.handle_error(error, context, user_message)
    
    def handle_permission_error(self, error: Exception, path: str = None):
        """
        Handle permission errors.
        
        Args:
            error: Permission error
            path: Path that caused the permission error
        """
        context = f"permission error for {path}" if path else "permission error"
        user_message = "Permission denied. You may not have access to this file or directory."
        
        self.handle_error(error, context, user_message)


class ApplicationExceptionHandler:
    """
    Global exception handler for unhandled exceptions.
    """
    
    def __init__(self, logger: logging.Logger, error_handler: ErrorHandler):
        """
        Initialize the global exception handler.
        
        Args:
            logger: Logger instance
            error_handler: Error handler instance
        """
        self.logger = logger
        self.error_handler = error_handler
        self.original_excepthook = sys.excepthook
        
    def install(self):
        """Install the global exception handler."""
        sys.excepthook = self.handle_exception
        threading.excepthook = self.handle_thread_exception
        
    def uninstall(self):
        """Restore the original exception handler."""
        sys.excepthook = self.original_excepthook
        threading.excepthook = threading.__excepthook__
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Handle unhandled exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't handle keyboard interrupt
            self.original_excepthook(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"Unhandled exception: {exc_type.__name__}: {exc_value}"
        self.logger.critical(error_msg)
        self.logger.critical("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        
        # Call error handler
        self.error_handler.handle_error(
            exc_value, 
            "unhandled exception", 
            "An unexpected error occurred. Please check the logs for details.",
            critical=True
        )
    
    def handle_thread_exception(self, args):
        """
        Handle unhandled exceptions in threads.
        
        Args:
            args: Thread exception arguments
        """
        error_msg = f"Unhandled exception in thread {args.thread.name}: {args.exc_type.__name__}: {args.exc_value}"
        self.logger.critical(error_msg)
        self.logger.critical("".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)))
        
        # Call error handler
        self.error_handler.handle_error(
            args.exc_value,
            f"thread {args.thread.name}",
            "An unexpected error occurred in a background thread.",
            critical=True
        )


def setup_application_logging(log_dir: str = None, log_level: str = "INFO") -> tuple:
    """
    Set up logging for the entire application.
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level
        
    Returns:
        Tuple of (logger, error_handler, exception_handler)
    """
    # Create logger
    sftp_logger = SFTPLogger(log_dir)
    sftp_logger.set_level(log_level)
    
    main_logger = sftp_logger.get_logger()
    
    # Create error handler
    error_handler = ErrorHandler(main_logger)
    
    # Create and install global exception handler
    exception_handler = ApplicationExceptionHandler(main_logger, error_handler)
    exception_handler.install()
    
    main_logger.info("Application logging setup complete")
    
    return main_logger, error_handler, exception_handler


# Decorator for automatic error handling
def handle_errors(error_handler: ErrorHandler, context: str = None, 
                 user_message: str = None):
    """
    Decorator for automatic error handling in methods.
    
    Args:
        error_handler: Error handler instance
        context: Context for error messages
        user_message: User-friendly error message
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_context = context or f"{func.__name__}"
                error_handler.handle_error(e, func_context, user_message)
                raise
        return wrapper
    return decorator