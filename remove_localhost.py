#!/usr/bin/env python3
"""
Remove Non-Working Localhost Connection
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager

def remove_localhost():
    """Remove the non-working localhost connection."""
    config = ConfigManager()
    
    connection_name = "Localhost SSH (Optional)"
    
    try:
        success = config.delete_connection(connection_name)
        if success:
            print(f"✅ Successfully removed: {connection_name}")
            return True
        else:
            print(f"❌ Failed to remove: {connection_name}")
            return False
    except Exception as e:
        print(f"❌ Error removing connection: {e}")
        return False

if __name__ == "__main__":
    print("Removing non-working localhost connection...")
    
    if remove_localhost():
        print("\n📋 Testing remaining connections...")
        os.system("python test_connections.py")
    else:
        print("\n❌ Failed to clean up connections")