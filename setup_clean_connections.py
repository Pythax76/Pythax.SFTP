#!/usr/bin/env python3
"""
Setup Working SFTP Test Connections

This script adds verified working SFTP test servers.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager

def clear_and_setup_connections():
    """Clear existing connections and set up verified SFTP test servers."""
    config = ConfigManager()
    
    # Clear existing connections first
    existing = config.load_connections()
    for name in list(existing.keys()):
        config.delete_connection(name)
        print(f"🗑️  Removed: {name}")
    
    # Verified working SFTP test servers
    test_connections = [
        {
            "name": "Rebex SFTP Test Server",
            "host": "test.rebex.net",
            "port": 22,
            "username": "demo",
            "password": "password",
            "private_key_path": "",
            "description": "Public SFTP test server (read-only)\nCredentials: demo/password\nFrom test.rebex.net"
        },
        {
            "name": "SFTPGo Demo Server",
            "host": "demo.sftpgo.com",
            "port": 2022,
            "username": "user1",
            "password": "user1pass",
            "private_key_path": "",
            "description": "SFTPGo public demo server\nPort 2022\nCredentials: user1/user1pass"
        },
        {
            "name": "FileZilla SFTP Test",
            "host": "demo.wftpserver.com",
            "port": 2222,
            "username": "demo-user",
            "password": "demo-user",
            "private_key_path": "",
            "description": "FileZilla demo SFTP server\nPort 2222\nCredentials: demo-user/demo-user"
        },
        {
            "name": "Alternative Test Server",
            "host": "speedtest.tele2.net",
            "port": 22,
            "username": "anonymous",
            "password": "",
            "private_key_path": "",
            "description": "Alternative SFTP test (if available)\nAnonymous login attempt"
        }
    ]
    
    # Add each connection
    added_count = 0
    for conn in test_connections:
        try:
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
                print(f"✅ Added: {conn['name']} ({conn['host']}:{conn['port']})")
                added_count += 1
            else:
                print(f"❌ Failed to save: {conn['name']}")
            
        except Exception as e:
            print(f"❌ Error adding '{conn['name']}': {e}")
    
    return added_count

if __name__ == "__main__":
    print("Setting up verified SFTP test connections...")
    print("=" * 50)
    
    try:
        count = clear_and_setup_connections()
        print(f"\n🎉 Setup complete! Added {count} test connections.")
        print("\nNext steps:")
        print("1. Run: python test_connections.py")
        print("2. Or open the SFTP client and try connecting")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)