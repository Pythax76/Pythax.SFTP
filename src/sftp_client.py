"""
SFTP Client Core Module

This module provides the core SFTP functionality using paramiko.
It handles connections, file operations, and directory management.
"""

import os
import stat
import logging
import paramiko
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
import threading
import time


class SFTPClient:
    """
    A comprehensive SFTP client class that provides all necessary
    file transfer and remote directory operations.
    """
    
    def __init__(self):
        """Initialize the SFTP client."""
        self.ssh_client = None
        self.sftp_client = None
        self.is_connected = False
        self.host = None
        self.port = 22
        self.username = None
        self.current_remote_path = "/"
        self.current_local_path = os.getcwd()
        self.logger = logging.getLogger(__name__)
        
        # Connection timeout in seconds
        self.timeout = 30
        
        # Callbacks for progress and status updates
        self.progress_callback = None
        self.status_callback = None
    
    def connect(self, host: str, username: str, password: str = None, 
                private_key_path: str = None, port: int = 22) -> bool:
        """
        Connect to an SFTP server.
        
        Args:
            host: Server hostname or IP address
            username: Username for authentication
            password: Password for authentication (optional if using key)
            private_key_path: Path to private key file (optional)
            port: Server port (default: 22)
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.host = host
            self.port = port
            self.username = username
            
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Prepare authentication parameters
            auth_kwargs = {
                'hostname': host,
                'port': port,
                'username': username,
                'timeout': self.timeout
            }
            
            # Use private key or password authentication
            if private_key_path and os.path.exists(private_key_path):
                try:
                    private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
                    auth_kwargs['pkey'] = private_key
                except paramiko.PasswordRequiredException:
                    # Key is encrypted, need password
                    if password:
                        private_key = paramiko.RSAKey.from_private_key_file(
                            private_key_path, password=password
                        )
                        auth_kwargs['pkey'] = private_key
                    else:
                        self.logger.error("Private key is encrypted but no password provided")
                        return False
                except Exception as e:
                    self.logger.error(f"Failed to load private key: {e}")
                    # Fall back to password authentication
                    if password:
                        auth_kwargs['password'] = password
                    else:
                        return False
            elif password:
                auth_kwargs['password'] = password
            else:
                self.logger.error("No authentication method provided")
                return False
            
            # Connect to server
            self.ssh_client.connect(**auth_kwargs)
            
            # Open SFTP session
            self.sftp_client = self.ssh_client.open_sftp()
            self.is_connected = True
            
            # Get initial remote directory
            self.current_remote_path = self.sftp_client.getcwd() or "/"
            
            self.logger.info(f"Connected to {host}:{port} as {username}")
            if self.status_callback:
                self.status_callback(f"Connected to {host}")
                
            return True
            
        except paramiko.AuthenticationException:
            self.logger.error("Authentication failed")
            if self.status_callback:
                self.status_callback("Authentication failed")
            return False
        except paramiko.SSHException as e:
            self.logger.error(f"SSH connection error: {e}")
            if self.status_callback:
                self.status_callback(f"Connection error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            if self.status_callback:
                self.status_callback(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the SFTP server."""
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.sftp_client = None
            
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
            
            self.is_connected = False
            self.logger.info("Disconnected from server")
            if self.status_callback:
                self.status_callback("Disconnected")
                
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def list_remote_directory(self, path: str = None) -> List[Dict[str, Any]]:
        """
        List files and directories in the remote path.
        
        Args:
            path: Remote directory path (uses current path if None)
            
        Returns:
            List of file/directory information dictionaries
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            if path is None:
                path = self.current_remote_path
            
            files = []
            for item in self.sftp_client.listdir_attr(path):
                file_info = {
                    'name': item.filename,
                    'size': item.st_size or 0,
                    'modified': datetime.fromtimestamp(item.st_mtime) if item.st_mtime else None,
                    'permissions': stat.filemode(item.st_mode) if item.st_mode else '---------',
                    'is_directory': stat.S_ISDIR(item.st_mode) if item.st_mode else False,
                    'is_file': stat.S_ISREG(item.st_mode) if item.st_mode else False,
                    'raw_mode': item.st_mode
                }
                files.append(file_info)
            
            # Sort: directories first, then files, both alphabetically
            files.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list remote directory: {e}")
            raise
    
    def list_local_directory(self, path: str = None) -> List[Dict[str, Any]]:
        """
        List files and directories in the local path.
        
        Args:
            path: Local directory path (uses current path if None)
            
        Returns:
            List of file/directory information dictionaries
        """
        try:
            if path is None:
                path = self.current_local_path
            
            files = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                stat_info = os.stat(full_path)
                
                file_info = {
                    'name': item,
                    'size': stat_info.st_size,
                    'modified': datetime.fromtimestamp(stat_info.st_mtime),
                    'permissions': stat.filemode(stat_info.st_mode),
                    'is_directory': os.path.isdir(full_path),
                    'is_file': os.path.isfile(full_path),
                    'full_path': full_path
                }
                files.append(file_info)
            
            # Sort: directories first, then files, both alphabetically
            files.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list local directory: {e}")
            raise
    
    def change_remote_directory(self, path: str) -> bool:
        """
        Change current remote directory.
        
        Args:
            path: Remote directory path
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            # Handle relative paths
            if path == "..":
                # Go to parent directory
                current_parts = self.current_remote_path.rstrip('/').split('/')
                if len(current_parts) > 1:
                    new_path = '/'.join(current_parts[:-1]) or '/'
                else:
                    new_path = '/'
            elif path.startswith('/'):
                # Absolute path
                new_path = path
            else:
                # Relative path
                new_path = f"{self.current_remote_path.rstrip('/')}/{path}"
            
            # Test if directory exists by listing it
            self.sftp_client.listdir(new_path)
            self.current_remote_path = new_path
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to change remote directory: {e}")
            return False
    
    def change_local_directory(self, path: str) -> bool:
        """
        Change current local directory.
        
        Args:
            path: Local directory path
            
        Returns:
            bool: True if successful
        """
        try:
            if path == "..":
                # Go to parent directory
                new_path = os.path.dirname(self.current_local_path)
            elif os.path.isabs(path):
                # Absolute path
                new_path = path
            else:
                # Relative path
                new_path = os.path.join(self.current_local_path, path)
            
            if os.path.isdir(new_path):
                self.current_local_path = os.path.abspath(new_path)
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to change local directory: {e}")
            return False
    
    def upload_file(self, local_path: str, remote_path: str, 
                    progress_callback=None) -> bool:
        """
        Upload a file to the remote server.
        
        Args:
            local_path: Local file path
            remote_path: Remote file path
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file not found: {local_path}")
            
            file_size = os.path.getsize(local_path)
            
            def progress_wrapper(transferred, total):
                if progress_callback:
                    progress_callback(transferred, total)
                elif self.progress_callback:
                    self.progress_callback(transferred, total)
            
            self.sftp_client.put(local_path, remote_path, callback=progress_wrapper)
            self.logger.info(f"Uploaded {local_path} to {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str, 
                      progress_callback=None) -> bool:
        """
        Download a file from the remote server.
        
        Args:
            remote_path: Remote file path
            local_path: Local file path
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
            
            def progress_wrapper(transferred, total):
                if progress_callback:
                    progress_callback(transferred, total)
                elif self.progress_callback:
                    self.progress_callback(transferred, total)
            
            self.sftp_client.get(remote_path, local_path, callback=progress_wrapper)
            self.logger.info(f"Downloaded {remote_path} to {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return False
    
    def delete_remote_file(self, remote_path: str) -> bool:
        """
        Delete a file on the remote server.
        
        Args:
            remote_path: Remote file path
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            self.sftp_client.remove(remote_path)
            self.logger.info(f"Deleted remote file: {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete remote file: {e}")
            return False
    
    def create_remote_directory(self, remote_path: str) -> bool:
        """
        Create a directory on the remote server.
        
        Args:
            remote_path: Remote directory path
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            self.sftp_client.mkdir(remote_path)
            self.logger.info(f"Created remote directory: {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create remote directory: {e}")
            return False
    
    def delete_remote_directory(self, remote_path: str) -> bool:
        """
        Delete a directory on the remote server.
        
        Args:
            remote_path: Remote directory path
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            self.sftp_client.rmdir(remote_path)
            self.logger.info(f"Deleted remote directory: {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete remote directory: {e}")
            return False
    
    def get_remote_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a remote file or directory.
        
        Args:
            remote_path: Remote file/directory path
            
        Returns:
            Dictionary with file information or None if not found
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
        
        try:
            stat_info = self.sftp_client.stat(remote_path)
            return {
                'size': stat_info.st_size,
                'modified': datetime.fromtimestamp(stat_info.st_mtime) if stat_info.st_mtime else None,
                'permissions': stat.filemode(stat_info.st_mode) if stat_info.st_mode else '---------',
                'is_directory': stat.S_ISDIR(stat_info.st_mode) if stat_info.st_mode else False,
                'is_file': stat.S_ISREG(stat_info.st_mode) if stat_info.st_mode else False,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get file info: {e}")
            return None
    
    def set_progress_callback(self, callback):
        """Set the progress callback function."""
        self.progress_callback = callback
    
    def set_status_callback(self, callback):
        """Set the status callback function."""
        self.status_callback = callback
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.is_connected:
            self.disconnect()