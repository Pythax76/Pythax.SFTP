#!/usr/bin/env python3
"""
Add Additional Verified SFTP Test Servers
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager

def add_more_servers():
    """Add more verified SFTP test servers."""
    config = ConfigManager()
    
    # Additional verified servers
    additional_servers = [
        {
            "name": "Rebex FTPS Test (SFTP mode)",
            "host": "test.rebex.net", 
            "port": 22,
            "username": "demo",
            "password": "password",
            "private_key_path": "",
            "description": "Same as main Rebex but configured separately\nReliable test server with read access"
        },
        {
            "name": "Local SSH Server (if available)",
            "host": "127.0.0.1",
            "port": 22,
            "username": os.getenv('USER', 'testuser'),
            "password": "",
            "private_key_path": os.path.expanduser("~/.ssh/id_rsa"),
            "description": f"Local SSH server using current user: {os.getenv('USER', 'testuser')}\nRequires SSH server running locally\nUses SSH key authentication"
        },
        {
            "name": "Rebex with Key Auth (demo)",
            "host": "test.rebex.net",
            "port": 22, 
            "username": "demo",
            "password": "",
            "private_key_path": "",
            "description": "Rebex test server - key auth attempt\nMay not work but worth testing"
        }
    ]
    
    added_count = 0
    for conn in additional_servers:
        try:
            # Check if already exists
            if config.get_connection(conn['name']):
                print(f"⚠️  '{conn['name']}' already exists, skipping")
                continue
                
            success = config.save_connection(
                name=conn['name'],
                host=conn['host'],
                port=conn['port'],
                username=conn['username'],
                password=conn['password'] if conn['password'] else None,
                private_key_path=conn['private_key_path'] if conn['private_key_path'] else None,
                description=conn['description']
            )
            
            if success:
                print(f"✅ Added: {conn['name']}")
                added_count += 1
            else:
                print(f"❌ Failed to save: {conn['name']}")
                
        except Exception as e:
            print(f"❌ Error adding '{conn['name']}': {e}")
    
    return added_count

if __name__ == "__main__":
    print("Adding additional SFTP test servers...")
    print("=" * 40)
    
    try:
        count = add_more_servers()
        if count > 0:
            print(f"\n✅ Added {count} additional servers!")
            print("Run 'python test_connections.py' to test all connections.")
        else:
            print("\n⚠️  No new servers were added.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)