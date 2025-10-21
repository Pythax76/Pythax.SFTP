"""
Configuration Management Module

This module handles loading and saving application configuration,
including server connections and user preferences.
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet
import base64


class ConfigManager:
    """
    Manages application configuration including connection profiles
    and user preferences with encryption support for sensitive data.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory for configuration files
        """
        if config_dir is None:
            # Default to config directory relative to application
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(exist_ok=True)
        
        self.connections_file = self.config_dir / "connections.json"
        self.settings_file = self.config_dir / "settings.yaml"
        self.key_file = self.config_dir / ".key"
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption key
        self._encryption_key = None
        self._load_or_create_key()
        
        # Default settings
        self.default_settings = {
            "appearance": {
                "theme": "light",
                "font_size": 12,
                "font_family": "Arial"
            },
            "transfer": {
                "default_local_path": os.path.expanduser("~"),
                "confirm_overwrites": True,
                "preserve_timestamps": True,
                "create_missing_directories": True,
                "confirm_local_to_remote": True,
                "confirm_remote_to_local": True
            },
            "connection": {
                "timeout": 30,
                "keep_alive_interval": 60,
                "auto_reconnect": True
            },
            "logging": {
                "level": "INFO",
                "max_log_files": 10,
                "max_log_size_mb": 10
            },
            "window": {
                "width": 1200,
                "height": 800,
                "maximized": False,
                "remember_size": True
            }
        }
    
    def _load_or_create_key(self):
        """Load existing encryption key or create a new one."""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    self._encryption_key = f.read()
            else:
                # Create new key
                self._encryption_key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(self._encryption_key)
                # Make key file readable only by owner
                os.chmod(self.key_file, 0o600)
        except Exception as e:
            self.logger.error(f"Failed to load/create encryption key: {e}")
            # Fallback to a default key (not secure, but allows operation)
            self._encryption_key = base64.urlsafe_b64encode(b"default_key_not_secure" + b"0" * 16)[:32]
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt a password for storage."""
        try:
            fernet = Fernet(self._encryption_key)
            encrypted = fernet.encrypt(password.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.logger.error(f"Failed to encrypt password: {e}")
            return ""
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a stored password."""
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt password: {e}")
            return ""
    
    def save_connection(self, name: str, host: str, port: int, username: str,
                       password: str = None, private_key_path: str = None,
                       description: str = None) -> bool:
        """
        Save a connection profile.
        
        Args:
            name: Connection profile name
            host: Server hostname or IP
            port: Server port
            username: Username
            password: Password (will be encrypted)
            private_key_path: Path to private key file
            description: Optional description
            
        Returns:
            bool: True if successful
        """
        try:
            connections = self.load_connections()
            
            connection_data = {
                "host": host,
                "port": port,
                "username": username,
                "description": description or "",
                "created": str(Path().resolve()),  # Current timestamp as string
                "private_key_path": private_key_path or ""
            }
            
            # Encrypt password if provided
            if password:
                connection_data["encrypted_password"] = self._encrypt_password(password)
            
            connections[name] = connection_data
            
            with open(self.connections_file, 'w') as f:
                json.dump(connections, f, indent=2)
            
            self.logger.info(f"Saved connection profile: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save connection: {e}")
            return False
    
    def load_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all connection profiles.
        
        Returns:
            Dictionary of connection profiles
        """
        try:
            if not self.connections_file.exists():
                return {}
            
            with open(self.connections_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load connections: {e}")
            return {}
    
    def get_connection(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific connection profile with decrypted password.
        
        Args:
            name: Connection profile name
            
        Returns:
            Connection data dictionary or None if not found
        """
        try:
            connections = self.load_connections()
            if name not in connections:
                return None
            
            connection = connections[name].copy()
            
            # Decrypt password if present
            if "encrypted_password" in connection:
                password = self._decrypt_password(connection["encrypted_password"])
                connection["password"] = password
                del connection["encrypted_password"]
            
            return connection
            
        except Exception as e:
            self.logger.error(f"Failed to get connection: {e}")
            return None
    
    def delete_connection(self, name: str) -> bool:
        """
        Delete a connection profile.
        
        Args:
            name: Connection profile name
            
        Returns:
            bool: True if successful
        """
        try:
            connections = self.load_connections()
            if name in connections:
                del connections[name]
                
                with open(self.connections_file, 'w') as f:
                    json.dump(connections, f, indent=2)
                
                self.logger.info(f"Deleted connection profile: {name}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to delete connection: {e}")
            return False
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save application settings.
        
        Args:
            settings: Settings dictionary
            
        Returns:
            bool: True if successful
        """
        try:
            # Merge with defaults to ensure all required settings exist
            merged_settings = self._merge_settings(self.default_settings, settings)
            
            with open(self.settings_file, 'w') as f:
                yaml.dump(merged_settings, f, default_flow_style=False, indent=2)
            
            self.logger.info("Saved application settings")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Load application settings.
        
        Returns:
            Settings dictionary
        """
        try:
            if not self.settings_file.exists():
                # Return default settings and save them
                self.save_settings(self.default_settings)
                return self.default_settings.copy()
            
            with open(self.settings_file, 'r') as f:
                loaded_settings = yaml.safe_load(f)
            
            # Merge with defaults to ensure all required settings exist
            return self._merge_settings(self.default_settings, loaded_settings)
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            return self.default_settings.copy()
    
    def _merge_settings(self, default: Dict[str, Any], 
                       loaded: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge loaded settings with defaults.
        
        Args:
            default: Default settings dictionary
            loaded: Loaded settings dictionary
            
        Returns:
            Merged settings dictionary
        """
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_setting(self, key_path: str, default=None):
        """
        Get a specific setting using dot notation.
        
        Args:
            key_path: Setting path (e.g., "appearance.theme")
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        try:
            settings = self.load_settings()
            keys = key_path.split('.')
            value = settings
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Failed to get setting {key_path}: {e}")
            return default
    
    def set_setting(self, key_path: str, value) -> bool:
        """
        Set a specific setting using dot notation.
        
        Args:
            key_path: Setting path (e.g., "appearance.theme")
            value: Value to set
            
        Returns:
            bool: True if successful
        """
        try:
            settings = self.load_settings()
            keys = key_path.split('.')
            current = settings
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            
            return self.save_settings(settings)
            
        except Exception as e:
            self.logger.error(f"Failed to set setting {key_path}: {e}")
            return False
    
    def export_connections(self, file_path: str, include_passwords: bool = False) -> bool:
        """
        Export connection profiles to a file.
        
        Args:
            file_path: Export file path
            include_passwords: Whether to include encrypted passwords
            
        Returns:
            bool: True if successful
        """
        try:
            connections = self.load_connections()
            
            if not include_passwords:
                # Remove encrypted passwords from export
                export_data = {}
                for name, conn in connections.items():
                    export_conn = conn.copy()
                    if "encrypted_password" in export_conn:
                        del export_conn["encrypted_password"]
                    export_data[name] = export_conn
            else:
                export_data = connections
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported connections to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export connections: {e}")
            return False
    
    def import_connections(self, file_path: str, overwrite: bool = False) -> bool:
        """
        Import connection profiles from a file.
        
        Args:
            file_path: Import file path
            overwrite: Whether to overwrite existing connections
            
        Returns:
            bool: True if successful
        """
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            current_connections = self.load_connections()
            
            for name, conn_data in import_data.items():
                if name not in current_connections or overwrite:
                    current_connections[name] = conn_data
            
            with open(self.connections_file, 'w') as f:
                json.dump(current_connections, f, indent=2)
            
            self.logger.info(f"Imported connections from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import connections: {e}")
            return False