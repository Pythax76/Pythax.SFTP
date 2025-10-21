#!/usr/bin/env python3
"""
Setup Test SFTP/FTP Connections

This script adds the test server connections to the SFTP client configuration.
Note: This client only supports SFTP (SSH File Transfer Protocol), not regular FTP.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager

def setup_test_connections():
    """Set up test SFTP connections."""
    config = ConfigManager()
    
    # Test connections - Only SFTP servers since our client doesn't support FTP
    test_connections = [
        {
            "name": "Rebex Test Server (SFTP)",
            "host": "test.rebex.net",
            "port": 22,
            "username": "demo",
            "password": "password",
            "private_key_path": "",
            "description": "Public SFTP test server (read-only)\nSupports SFTP on port 22\nFrom test.rebex.net"
        },
        {
            "name": "Demo WFTP Server",
            "host": "demo.wftpserver.com", 
            "port": 2222,
            "username": "demo",
            "password": "demo",
            "private_key_path": "",
            "description": "Public SFTP test server\nPort 2222\nFrom sftp.net public server list"
        },
        {
            "name": "SFTPGo Demo Server",
            "host": "demo.sftpgo.com",
            "port": 2022,
            "username": "test_user_1",
            "password": "test_password_1",
            "private_key_path": "",
            "description": "SFTPGo public demo server\nPort 2022\nAlternative test server"
        },
        {
            "name": "Local SFTP Test (localhost)",
            "host": "localhost",
            "port": 22,
            "username": "testuser",
            "password": "testpass",
            "private_key_path": "",
            "description": "Local SFTP server for testing\nRequires local SSH server running\nReplace with your local credentials"
        }
    ]
    
    # Add each connection
    added_count = 0
    for conn in test_connections:
        try:
            # Check if connection already exists
            existing_connections = config.load_connections()
            if conn['name'] in existing_connections:
                print(f"⚠️  Connection '{conn['name']}' already exists, skipping")
                continue
                
            # Add the connection using the correct method signature
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
                print(f"✅ Added connection: {conn['name']} ({conn['host']}:{conn['port']})")
                added_count += 1
            else:
                print(f"❌ Failed to save connection '{conn['name']}'")
            
        except Exception as e:
            print(f"❌ Failed to add connection '{conn['name']}': {e}")
    
    print(f"\n🎉 Successfully added {added_count} test connections!")
    print("\nNote: This SFTP client only supports SFTP protocol, not regular FTP.")
    print("The FTP servers from your list won't work with this client.")
    print("\nTo test the connections:")
    print("1. Open the SFTP client")
    print("2. Click 'Connect' to see the saved connections")
    print("3. Select a test server and click 'Connect'")
    
    return added_count > 0

if __name__ == "__main__":
    print("Setting up test SFTP connections...")
    print("=" * 50)
    
    try:
        success = setup_test_connections()
        if success:
            print("\n✅ Test connections setup completed!")
        else:
            print("\n⚠️  No new connections were added.")
    except Exception as e:
        print(f"\n❌ Error setting up connections: {e}")
        sys.exit(1)