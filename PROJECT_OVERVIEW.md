# SFTP Client Project Overview

## Project Summary

This is a fully-featured SFTP client application built with Python 3.14 and tkinter. The application provides a comprehensive solution for secure file transfers with a dual-pane graphical interface.

## Quick Start

### Installation & Setup
```bash
# Make setup script executable and run it
chmod +x setup.sh
./setup.sh

# Launch the application
./run.sh
```

### Manual Launch
```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python main.py
```

## Project Structure

```
SFTP/
├── src/                    # Core application source code
│   ├── __init__.py        # Package initialization
│   ├── sftp_client.py     # Core SFTP operations (paramiko)
│   ├── config_manager.py  # Configuration & connection management
│   ├── logger.py          # Logging & error handling
│   ├── gui.py             # GUI components (tkinter)
│   └── main_app.py        # Main application orchestrator
├── config/                # Application configuration files
├── logs/                  # Application logs
├── tests/                 # Unit tests (for future development)
├── venv/                  # Python virtual environment
├── main.py               # Application entry point
├── run.sh                # Launch script (executable)
├── setup.sh              # Setup script (executable)
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore patterns
├── README.md            # Comprehensive documentation
└── PROJECT_OVERVIEW.md   # This file
```

## Key Features

### Core Functionality
- ✅ Secure SFTP connections (password & private key auth)
- ✅ Dual-pane file browser (local & remote)
- ✅ File upload/download with progress tracking
- ✅ Directory navigation and management
- ✅ Connection profile management
- ✅ Encrypted password storage

### Technical Features
- ✅ Comprehensive logging with rotation
- ✅ Robust error handling
- ✅ Configuration management
- ✅ Cross-platform compatibility
- ✅ Virtual environment setup
- ✅ Modular architecture

### User Interface
- ✅ Clean tkinter GUI
- ✅ Connection toolbar
- ✅ Menu system
- ✅ Status bar
- ✅ Progress dialogs
- ✅ Connection management dialogs

## Architecture

### Core Components

1. **SFTPClient** (`sftp_client.py`)
   - Paramiko-based SFTP operations
   - Connection management
   - File transfer operations
   - Progress callbacks

2. **ConfigManager** (`config_manager.py`)
   - Connection profile storage
   - Encrypted password handling
   - Application settings
   - Import/export functionality

3. **Logger** (`logger.py`)
   - Comprehensive logging setup
   - Error handling framework
   - Global exception handling
   - Log rotation

4. **GUI Components** (`gui.py`, `main_app.py`)
   - Main application window
   - File browser panels
   - Connection dialogs
   - Progress tracking

### Data Flow
```
User Input → GUI → Main App → SFTP Client → Server
                ↓              ↓
          Config Manager → Logger → Log Files
```

## Dependencies

### Core Dependencies
- **paramiko** (3.4.0+): SSH/SFTP protocol implementation
- **cryptography** (41.0.0+): Password encryption
- **pyyaml** (6.0.1+): Configuration file handling
- **tkinter**: GUI framework (included with Python)

### Additional Dependencies
- **pillow** (10.0.0+): Image processing
- **tqdm** (4.66.0+): Progress bars
- **pathlib2** (2.3.7+): Enhanced path handling
- **python-dateutil** (2.8.2+): Date/time utilities
- **jsonschema** (4.19.0+): JSON validation

### Development Dependencies
- **pytest** (7.4.0+): Testing framework
- **pytest-cov** (4.1.0+): Coverage testing
- **black** (23.7.0+): Code formatting
- **flake8** (6.0.0+): Code linting

## Configuration

### Connection Storage
- Connections saved in `config/connections.json`
- Passwords encrypted using Fernet (AES)
- Encryption key stored in `config/.key`
- Import/export functionality available

### Application Settings
- Settings stored in `config/settings.yaml`
- Window size/position memory
- Transfer preferences
- Logging configuration
- Connection timeouts

### Logging
- Main log: `logs/sftp_client.log`
- Error log: `logs/sftp_client_errors.log`
- Automatic log rotation (10MB max, 10 files)
- Configurable log levels

## Security Features

### Password Protection
- All passwords encrypted before storage
- Unique encryption key per installation
- Key file with restricted permissions (600)

### Connection Security
- SSH protocol with full encryption
- Private key authentication support
- Host key verification
- Configurable connection timeouts

### File Security
- Configuration files in .gitignore
- Restricted permissions on sensitive files
- Secure temporary file handling

## Development Guidelines

### Code Organization
- Modular design with clear separation of concerns
- Comprehensive error handling throughout
- Extensive logging for debugging
- Type hints for better code documentation

### Testing
- Unit test structure in place
- Integration test capabilities
- Manual testing procedures documented

### Extensibility
- Plugin architecture ready
- Configuration-driven behavior
- Callback system for progress tracking
- Event-driven GUI updates

## Future Enhancements

### Planned Features
- Batch file operations
- File synchronization
- SSH tunnel management
- Plugin system
- Themes and customization
- Command-line interface

### Potential Improvements
- Multi-threaded transfers
- Resume interrupted transfers
- File comparison tools
- Bookmark system
- Integration with cloud services

## Deployment

### macOS Deployment
- Virtual environment included
- Shell scripts for easy launching
- Compatible with macOS security requirements

### Cross-Platform Notes
- Core functionality is cross-platform
- GUI tested on macOS, should work on Linux/Windows
- Path handling uses pathlib for compatibility

## Support

### Troubleshooting
1. Check logs in `logs/` directory
2. Verify virtual environment activation
3. Test connectivity with standard SSH tools
4. Review file permissions

### Common Issues
- Import errors: Check virtual environment
- Connection issues: Verify server details
- Permission errors: Check file/directory permissions
- GUI issues: Ensure tkinter is available

### Getting Help
- Review comprehensive README.md
- Check application logs for specific errors
- Test connections using built-in test feature
- Verify server accessibility independently

---

**Project Status**: ✅ Complete and Ready for Use
**Python Version**: 3.14.0
**Platform**: macOS (Cross-platform compatible)
**License**: Educational/Personal Use