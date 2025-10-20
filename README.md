# SFTP Client

A full-featured SFTP (SSH File Transfer Protocol) client with a graphical user interface built using Python and tkinter. This application provides secure file transfers between local and remote servers with an intuitive dual-pane interface.

## Features

### Core Functionality
- **Secure SFTP Connections**: Connect to SFTP servers using password or private key authentication
- **Dual-Pane Interface**: Side-by-side local and remote file browsers
- **File Operations**: Upload, download, delete, and create directories
- **Connection Management**: Save and manage multiple server connections
- **Progress Tracking**: Real-time progress bars for file transfers
- **Comprehensive Logging**: Detailed logging with rotation and error tracking

### Security Features
- **Encrypted Password Storage**: Passwords are encrypted before being saved
- **Private Key Support**: Support for RSA private key authentication
- **Secure Configuration**: Configuration files with appropriate permissions

### User Interface
- **Intuitive GUI**: Clean, modern interface built with tkinter
- **File Browser**: Navigate directories with double-click and keyboard shortcuts
- **Connection Toolbar**: Quick access to connection management
- **Status Bar**: Real-time connection and operation status
- **Menu System**: Comprehensive menu system for all operations

## Installation

### Prerequisites
- **Python 3.7+**: Required for the application
- **macOS/Linux/Windows**: Cross-platform compatibility
- **SSH Access**: Target servers must support SFTP

### Quick Setup

1. **Clone or download** the project to your desired location
2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```
3. **Start the application**:
   ```bash
   ./run.sh
   ```

### Manual Setup

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Getting Started

1. **Launch the application** using one of the methods above
2. **Create a new connection**:
   - Click "New" in the toolbar or use File → New Connection
   - Fill in server details (host, port, username)
   - Choose authentication method (password or private key)
   - Test the connection and save

3. **Connect to a server**:
   - Select a saved connection from the dropdown
   - Click "Connect" button
   - Navigate files using the remote panel

### File Operations

#### Uploading Files
1. Navigate to desired local directory in the left panel
2. Select files or directories to upload
3. Navigate to target remote directory in the right panel
4. Click "Upload" button or use Transfer → Upload menu

#### Downloading Files
1. Navigate to desired remote directory in the right panel
2. Select files or directories to download
3. Navigate to target local directory in the left panel
4. Click "Download" button or use Transfer → Download menu

#### Navigation
- **Double-click** directories to enter them
- **Up button** to go to parent directory
- **Path bar** to type or edit current path
- **Refresh button** to reload current directory

### Connection Management

#### Saving Connections
1. Use File → New Connection or click "New" button
2. Enter connection details:
   - **Name**: Friendly name for the connection
   - **Host**: Server hostname or IP address
   - **Port**: SSH port (default: 22)
   - **Username**: Your username on the server
   - **Authentication**: Choose password or private key
   - **Description**: Optional notes about the connection

#### Managing Saved Connections
- **Edit**: Select connection and use Connection → Manage Connections
- **Delete**: Remove unwanted connections
- **Import/Export**: Share connections between installations

### Configuration

The application stores configuration in the `config/` directory:

- **connections.json**: Encrypted connection profiles
- **settings.yaml**: Application preferences
- **.key**: Encryption key for password security

#### Settings
Customize the application through the settings file:

```yaml
appearance:
  theme: light
  font_size: 12
  font_family: Arial

transfer:
  default_local_path: "~"
  confirm_overwrites: true
  preserve_timestamps: true
  create_missing_directories: true

connection:
  timeout: 30
  keep_alive_interval: 60
  auto_reconnect: true

logging:
  level: INFO
  max_log_files: 10
  max_log_size_mb: 10

window:
  width: 1200
  height: 800
  maximized: false
  remember_size: true
```

### Logging

Logs are stored in the `logs/` directory:

- **sftp_client.log**: Main application log with all activities
- **sftp_client_errors.log**: Error-specific log for troubleshooting

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Troubleshooting

### Common Issues

#### Connection Problems
- **Authentication Failed**: Verify username and password/key
- **Connection Timeout**: Check host address and port
- **Permission Denied**: Ensure proper SSH access and permissions

#### File Transfer Issues
- **Upload Failed**: Check remote directory permissions
- **Download Failed**: Ensure local directory is writable
- **Large Files**: Monitor progress dialog for transfer status

#### Application Issues
- **GUI Not Loading**: Ensure tkinter is installed (`pip install tk`)
- **Import Errors**: Verify all dependencies are installed
- **Permission Errors**: Check file/directory permissions

### Log Analysis

Check the log files for detailed error information:

```bash
tail -f logs/sftp_client.log        # Monitor real-time activity
grep ERROR logs/sftp_client.log     # Find error messages
```

### Getting Help

1. **Check the logs** for specific error messages
2. **Verify connection settings** using the test connection feature
3. **Ensure server accessibility** using standard SSH tools
4. **Review file permissions** on both local and remote systems

## Development

### Project Structure

```
SFTP/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── sftp_client.py     # Core SFTP functionality
│   ├── config_manager.py  # Configuration management
│   ├── logger.py          # Logging and error handling
│   ├── gui.py             # GUI components
│   └── main_app.py        # Main application class
├── config/                # Configuration files
├── logs/                  # Application logs
├── tests/                 # Unit tests (for future development)
├── venv/                  # Python virtual environment
├── main.py               # Application entry point
├── run.sh                # Launch script
├── setup.sh              # Setup script
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

### Dependencies

Core dependencies:
- **paramiko**: SSH/SFTP protocol implementation
- **cryptography**: Encryption for password storage
- **pyyaml**: Configuration file handling
- **tkinter**: GUI framework (usually included with Python)

Additional dependencies:
- **pillow**: Image processing for GUI icons
- **tqdm**: Progress bars
- **pytest**: Testing framework
- **pathlib2**: Enhanced path handling

### Architecture

The application follows a modular architecture:

1. **SFTPClient**: Core SFTP operations using paramiko
2. **ConfigManager**: Configuration and connection management
3. **Logger/ErrorHandler**: Comprehensive logging and error handling
4. **GUI Components**: Modular tkinter interface
5. **Main Application**: Orchestrates all components

### Contributing

To contribute to this project:

1. **Fork the repository** and create a feature branch
2. **Follow the existing code style** and add appropriate documentation
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description

## Security Considerations

### Password Security
- Passwords are encrypted using Fernet (AES 128) before storage
- Encryption keys are stored separately with restricted permissions
- Configuration files containing sensitive data are in `.gitignore`

### Connection Security
- All connections use SSH protocol with encryption
- Private key authentication is supported and recommended
- Host key verification follows SSH standards

### File Permissions
- Configuration files are created with restricted permissions
- Logs may contain sensitive information - secure accordingly
- Private keys should have appropriate file permissions (600)

## License

This project is provided as-is for educational and personal use. Please ensure compliance with your organization's security policies when using this tool for business purposes.

## Version History

### v1.0.0
- Initial release with full SFTP functionality
- GUI interface with dual-pane file browser
- Connection management with encrypted password storage
- Comprehensive logging and error handling
- Cross-platform compatibility

---

For support or questions, please check the troubleshooting section or review the application logs for detailed error information.