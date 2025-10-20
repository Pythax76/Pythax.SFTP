#!/usr/bin/env python3
"""
SFTP Client - Main Entry Point

This is the main entry point for the SFTP client application.
Run this file to start the GUI application.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from src.main_app import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)