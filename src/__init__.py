"""
SFTP Client Package

A comprehensive SFTP client with GUI interface built using Python and tkinter.
"""

__version__ = "1.0.0"
__author__ = "SFTP Client Development Team"
__description__ = "A full-featured SFTP client application"

from .sftp_client import SFTPClient
from .config_manager import ConfigManager
from .main_app import SFTPClientApp

__all__ = ['SFTPClient', 'ConfigManager', 'SFTPClientApp']