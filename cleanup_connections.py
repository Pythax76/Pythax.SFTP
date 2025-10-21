#!/usr/bin/env python3
"""
Clean Up SFTP Connections - Remove Non-Working Servers

This script removes non-working test servers and keeps only the verified working ones.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager

def clean_connections():
    """Remove non-working connections and keep only verified working ones."""
    config = ConfigManager()
    
    # Get all current connections
    connections = config.load_connections()
    
    # Define which connections to keep (working ones from our tests)
    keep_connections = {
        "Rebex SFTP Test Server",
        "Rebex FTPS Test (SFTP mode)"
    }
    
    # Define which connections to remove (non-working ones)
    remove_connections = {
        "SFTPGo Demo Server",
        "FileZilla SFTP Test", 
        "Alternative Test Server",
        "Local SSH Server (if available)",
        "Rebex with Key Auth (demo)"
    }
    
    print("Current connections:")
    for name in connections.keys():
        status = "✅ KEEP" if name in keep_connections else "❌ REMOVE"
        print(f"  {status} - {name}")
    
    print(f"\nRemoving {len(remove_connections)} non-working connections...")
    print("=" * 50)
    
    removed_count = 0
    for name in list(connections.keys()):
        if name in remove_connections:
            try:
                success = config.delete_connection(name)
                if success:
                    print(f"🗑️  Removed: {name}")
                    removed_count += 1
                else:
                    print(f"❌ Failed to remove: {name}")
            except Exception as e:
                print(f"❌ Error removing '{name}': {e}")
        elif name in keep_connections:
            print(f"✅ Kept: {name}")
        else:
            # Unknown connection - ask what to do
            print(f"❓ Unknown connection: {name} (keeping)")
    
    return removed_count

def add_one_more_working_server():
    """Add one more potentially working server for variety."""
    config = ConfigManager()
    
    # Add a localhost option for users who might have SSH running
    localhost_conn = {
        "name": "Localhost SSH (Optional)",
        "host": "localhost",
        "port": 22,
        "username": os.getenv('USER', 'user'),
        "password": "",
        "private_key_path": os.path.expanduser("~/.ssh/id_rsa"),
        "description": f"Local SSH server for testing\nUser: {os.getenv('USER', 'user')}\nRequires SSH server running\nUses SSH key (~/.ssh/id_rsa)"
    }
    
    try:
        # Only add if it doesn't exist
        if not config.get_connection(localhost_conn['name']):
            success = config.save_connection(
                name=localhost_conn['name'],
                host=localhost_conn['host'],
                port=localhost_conn['port'],
                username=localhost_conn['username'],
                password=None,
                private_key_path=localhost_conn['private_key_path'],
                description=localhost_conn['description']
            )
            
            if success:
                print(f"✅ Added optional: {localhost_conn['name']}")
                return True
        else:
            print(f"⚠️  Already exists: {localhost_conn['name']}")
            
    except Exception as e:
        print(f"❌ Error adding localhost connection: {e}")
    
    return False

if __name__ == "__main__":
    print("Cleaning up SFTP test connections...")
    print("Removing non-working servers, keeping verified ones")
    print("=" * 60)
    
    try:
        removed = clean_connections()
        added = add_one_more_working_server()
        
        print(f"\n🎉 Cleanup completed!")
        print(f"   🗑️  Removed: {removed} non-working connections")
        print(f"   ➕ Added: {1 if added else 0} optional connections")
        
        print(f"\n📋 Remaining connections:")
        config = ConfigManager()
        connections = config.load_connections()
        for i, name in enumerate(connections.keys(), 1):
            print(f"   {i}. {name}")
        
        print(f"\n🧪 To test remaining connections:")
        print("   python test_connections.py")
        
        print(f"\n🚀 To use in SFTP client:")
        print("   Open app → Connect → Select 'Rebex SFTP Test Server'")
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)