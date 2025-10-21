#!/usr/bin/env python3
"""
Test SFTP Connections

This script tests all configured SFTP connections to verify they work.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager
from sftp_client import SFTPClient

def test_connection(name, connection_data):
    """Test a single SFTP connection."""
    print(f"\n🔗 Testing: {name}")
    print(f"   Host: {connection_data['host']}:{connection_data['port']}")
    print(f"   User: {connection_data['username']}")
    
    client = SFTPClient()
    try:
        # Attempt connection
        success = client.connect(
            host=connection_data['host'],
            port=connection_data['port'],
            username=connection_data['username'],
            password=connection_data.get('password'),
            private_key_path=connection_data.get('private_key_path')
        )
        
        if success:
            print(f"   ✅ Connection successful!")
            
            # Try to list directory
            try:
                files = client.list_remote_directory("/")
                print(f"   📁 Found {len(files)} items in root directory")
                
                # Show first few items
                for i, file_info in enumerate(files[:3]):
                    file_type = "📁" if file_info["is_directory"] else "📄"
                    print(f"      {file_type} {file_info['name']}")
                
                if len(files) > 3:
                    print(f"      ... and {len(files) - 3} more items")
                    
            except Exception as e:
                print(f"   ⚠️  Connected but couldn't list directory: {e}")
            
            # Disconnect
            client.disconnect()
            return True
            
        else:
            print(f"   ❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_all_connections():
    """Test all configured connections."""
    config = ConfigManager()
    connection_names = list(config.load_connections().keys())
    
    if not connection_names:
        print("❌ No connections found. Run setup_test_connections.py first.")
        return
    
    print(f"Testing {len(connection_names)} configured connections...")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for name in connection_names:
        # Use get_connection to get decrypted passwords
        connection_data = config.get_connection(name)
        if connection_data:
            if test_connection(name, connection_data):
                successful += 1
            else:
                failed += 1
        else:
            print(f"❌ Could not load connection: {name}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {successful}/{len(connection_names)} ({successful/len(connection_names)*100:.1f}%)")
    
    if successful > 0:
        print(f"\n🎉 You have {successful} working SFTP test server(s)!")
    else:
        print(f"\n😞 No working connections found. This might be due to:")
        print("   - Network connectivity issues")
        print("   - Firewall blocking SFTP ports")
        print("   - Test servers being temporarily unavailable")

if __name__ == "__main__":
    print("SFTP Connection Testing Tool")
    print("This will test all configured SFTP connections")
    print()
    
    try:
        test_all_connections()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        sys.exit(1)