"""
Main GUI Application for SFTP Client

This module contains the main application window and orchestrates
all the GUI components.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from typing import Optional, Dict, Any
import logging

from .sftp_client import SFTPClient
from .config_manager import ConfigManager
from .logger import setup_application_logging, ErrorHandler
from .gui import ConnectionDialog, FileListFrame, ProgressDialog


class SFTPClientApp:
    """Main SFTP Client Application."""
    
    def __init__(self):
        """Initialize the SFTP client application."""
        # Set up logging first
        self.logger, self.error_handler, self.exception_handler = setup_application_logging()
        self.logger.info("Starting SFTP Client Application")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.sftp_client = SFTPClient()
        
        # GUI components
        self.root = None
        self.local_frame = None
        self.remote_frame = None
        self.status_var = None
        self.progress_dialog = None
        
        # Connection state
        self.is_connected = False
        self.current_connection = None
        
        # Setup callbacks
        self.sftp_client.set_status_callback(self.update_status)
        self.sftp_client.set_progress_callback(self.update_progress)
        self.error_handler.add_error_callback(self.show_error)
        
        self.create_gui()
        self.load_settings()
    
    def create_gui(self):
        """Create the main GUI."""
        self.root = tk.Tk()
        self.root.title("SFTP Client")
        self.root.geometry("1200x800")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.create_menu()
        self.create_toolbar()
        self.create_main_content()
        self.create_status_bar()
        
        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Connection", command=self.new_connection)
        file_menu.add_command(label="Quick Connect", command=self.quick_connect)
        file_menu.add_separator()
        file_menu.add_command(label="Import Connections", command=self.import_connections)
        file_menu.add_command(label="Export Connections", command=self.export_connections)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Connection menu
        conn_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Connection", menu=conn_menu)
        conn_menu.add_command(label="Connect", command=self.connect_to_saved)
        conn_menu.add_command(label="Disconnect", command=self.disconnect)
        conn_menu.add_separator()
        conn_menu.add_command(label="Manage Connections", command=self.manage_connections)
        
        # Transfer menu
        transfer_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Transfer", menu=transfer_menu)
        transfer_menu.add_command(label="Upload", command=self.upload_files)
        transfer_menu.add_command(label="Download", command=self.download_files)
        transfer_menu.add_separator()
        transfer_menu.add_command(label="Create Directory", command=self.create_directory)
        transfer_menu.add_command(label="Delete", command=self.delete_selected)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.refresh_all)
        view_menu.add_command(label="Show Hidden Files", command=self.toggle_hidden_files)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Connection controls
        ttk.Label(toolbar, text="Connection:").pack(side=tk.LEFT)
        
        self.connection_var = tk.StringVar()
        connection_combo = ttk.Combobox(toolbar, textvariable=self.connection_var, 
                                       state="readonly", width=20)
        connection_combo.pack(side=tk.LEFT, padx=(5, 10))
        connection_combo.bind("<<ComboboxSelected>>", self.on_connection_selected)
        self.connection_combo = connection_combo
        
        ttk.Button(toolbar, text="Connect", command=self.connect_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Disconnect", command=self.disconnect).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="New", command=self.new_connection).pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Transfer controls
        ttk.Button(toolbar, text="Upload", command=self.upload_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Download", command=self.download_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_all).pack(side=tk.LEFT, padx=2)
        
        self.refresh_connection_list()
    
    def create_main_content(self):
        """Create the main content area."""
        # Create paned window for local and remote panels
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Local files frame
        local_container = ttk.Frame(paned)
        paned.add(local_container, weight=1)
        
        self.local_frame = FileListFrame(local_container, "Local Files", is_remote=False)
        self.local_frame.pack(fill=tk.BOTH, expand=True)
        
        # Remote files frame
        remote_container = ttk.Frame(paned)
        paned.add(remote_container, weight=1)
        
        self.remote_frame = FileListFrame(remote_container, "Remote Files", is_remote=True)
        self.remote_frame.pack(fill=tk.BOTH, expand=True)
    
    def create_status_bar(self):
        """Create the status bar."""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Connection status indicator
        self.connection_status_var = tk.StringVar(value="Disconnected")
        connection_label = ttk.Label(status_frame, textvariable=self.connection_status_var)
        connection_label.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def refresh_connection_list(self):
        """Refresh the connection dropdown list."""
        connections = self.config_manager.load_connections()
        self.connection_combo['values'] = list(connections.keys())
    
    def new_connection(self):
        """Create a new connection."""
        dialog = ConnectionDialog(self.root, self.config_manager)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # Save the connection
            conn_data = dialog.result
            success = self.config_manager.save_connection(
                name=conn_data["name"],
                host=conn_data["host"],
                port=conn_data["port"],
                username=conn_data["username"],
                password=conn_data.get("password"),
                private_key_path=conn_data.get("private_key_path"),
                description=conn_data.get("description", "")
            )
            
            if success:
                self.refresh_connection_list()
                self.connection_var.set(conn_data["name"])
                messagebox.showinfo("Success", "Connection saved successfully")
            else:
                messagebox.showerror("Error", "Failed to save connection")
    
    def quick_connect(self):
        """Quick connect dialog."""
        dialog = ConnectionDialog(self.root, self.config_manager)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # Connect directly without saving
            self.connect_with_params(dialog.result)
    
    def connect_selected(self):
        """Connect to the selected connection."""
        connection_name = self.connection_var.get()
        if not connection_name:
            messagebox.showwarning("Warning", "Please select a connection")
            return
        
        connection_data = self.config_manager.get_connection(connection_name)
        if not connection_data:
            messagebox.showerror("Error", "Connection not found")
            return
        
        self.connect_with_params(connection_data)
    
    def connect_with_params(self, params: Dict[str, Any]):
        """Connect with given parameters."""
        def connect_thread():
            try:
                self.update_status("Connecting...")
                success = self.sftp_client.connect(
                    host=params["host"],
                    port=params["port"],
                    username=params["username"],
                    password=params.get("password"),
                    private_key_path=params.get("private_key_path")
                )
                
                if success:
                    self.is_connected = True
                    self.current_connection = params
                    self.root.after(0, self.on_connected)
                else:
                    self.root.after(0, lambda: self.update_status("Connection failed"))
                    
            except Exception as e:
                self.logger.error(f"Connection error: {e}")
                self.root.after(0, lambda: self.update_status("Connection failed"))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def on_connected(self):
        """Handle successful connection."""
        self.connection_status_var.set("Connected")
        self.update_status(f"Connected to {self.current_connection['host']}")
        self.remote_frame.set_sftp_client(self.sftp_client)
        self.refresh_all()
    
    def disconnect(self):
        """Disconnect from server."""
        if self.is_connected:
            self.sftp_client.disconnect()
            self.is_connected = False
            self.current_connection = None
            self.connection_status_var.set("Disconnected")
            self.update_status("Disconnected")
            self.remote_frame.set_sftp_client(None)
            self.remote_frame.refresh_list()
    
    def upload_files(self):
        """Upload selected files to remote server."""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Not connected to server")
            return
        
        selected_files = self.local_frame.get_selected_files()
        if not selected_files:
            messagebox.showwarning("Warning", "Please select files to upload")
            return
        
        self.transfer_files(selected_files, upload=True)
    
    def download_files(self):
        """Download selected files from remote server."""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Not connected to server")
            return
        
        selected_files = self.remote_frame.get_selected_files()
        if not selected_files:
            messagebox.showwarning("Warning", "Please select files to download")
            return
        
        self.transfer_files(selected_files, upload=False)
    
    def transfer_files(self, files: list, upload: bool):
        """Transfer files between local and remote."""
        def transfer_thread():
            try:
                for filename in files:
                    if upload:
                        local_path = os.path.join(self.local_frame.get_current_path(), filename)
                        remote_path = f"{self.remote_frame.get_current_path().rstrip('/')}/{filename}"
                        
                        if os.path.isfile(local_path):
                            self.sftp_client.upload_file(local_path, remote_path)
                    else:
                        remote_path = f"{self.remote_frame.get_current_path().rstrip('/')}/{filename}"
                        local_path = os.path.join(self.local_frame.get_current_path(), filename)
                        
                        self.sftp_client.download_file(remote_path, local_path)
                
                # Refresh both panels
                self.root.after(0, self.refresh_all)
                self.root.after(0, lambda: self.update_status("Transfer completed"))
                
            except Exception as e:
                self.logger.error(f"Transfer error: {e}")
                self.root.after(0, lambda: self.update_status("Transfer failed"))
        
        threading.Thread(target=transfer_thread, daemon=True).start()
    
    def refresh_all(self):
        """Refresh both file panels."""
        self.local_frame.refresh_list()
        if self.is_connected:
            self.remote_frame.refresh_list()
    
    def update_status(self, message: str):
        """Update status bar."""
        if self.status_var:
            self.status_var.set(message)
            self.logger.info(f"Status: {message}")
    
    def update_progress(self, transferred: int, total: int):
        """Update progress dialog."""
        if self.progress_dialog:
            self.progress_dialog.update_progress(transferred, total)
    
    def show_error(self, error_info: Dict[str, Any], user_message: str = None):
        """Show error to user."""
        message = user_message or error_info.get('message', 'An error occurred')
        if error_info.get('critical'):
            messagebox.showerror("Critical Error", message)
        else:
            messagebox.showerror("Error", message)
    
    def load_settings(self):
        """Load application settings."""
        settings = self.config_manager.load_settings()
        
        # Apply window settings
        window_settings = settings.get('window', {})
        if window_settings.get('remember_size', True):
            width = window_settings.get('width', 1200)
            height = window_settings.get('height', 800)
            self.root.geometry(f"{width}x{height}")
            
            if window_settings.get('maximized', False):
                self.root.state('zoomed')
    
    def save_settings(self):
        """Save application settings."""
        settings = self.config_manager.load_settings()
        
        # Save window settings
        if self.root.state() == 'zoomed':
            settings['window']['maximized'] = True
        else:
            settings['window']['maximized'] = False
            geometry = self.root.geometry()
            width, height = geometry.split('+')[0].split('x')
            settings['window']['width'] = int(width)
            settings['window']['height'] = int(height)
        
        self.config_manager.save_settings(settings)
    
    def on_closing(self):
        """Handle application closing."""
        try:
            self.save_settings()
            if self.is_connected:
                self.disconnect()
            
            # Cleanup logging
            if hasattr(self, 'exception_handler'):
                self.exception_handler.uninstall()
            
            self.logger.info("Application closing")
            self.root.destroy()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
            self.root.destroy()
    
    def run(self):
        """Run the application."""
        try:
            self.logger.info("Starting GUI main loop")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            raise
    
    # Additional methods for menu actions
    def connect_to_saved(self):
        """Show dialog to select and connect to saved connection."""
        self.connect_selected()
    
    def manage_connections(self):
        """Show connection management dialog."""
        # This would open a more comprehensive connection manager
        messagebox.showinfo("Info", "Connection management dialog would open here")
    
    def import_connections(self):
        """Import connections from file."""
        filename = filedialog.askopenfilename(
            title="Import Connections",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filename:
            if self.config_manager.import_connections(filename):
                self.refresh_connection_list()
                messagebox.showinfo("Success", "Connections imported successfully")
            else:
                messagebox.showerror("Error", "Failed to import connections")
    
    def export_connections(self):
        """Export connections to file."""
        filename = filedialog.asksaveasfilename(
            title="Export Connections",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filename:
            if self.config_manager.export_connections(filename):
                messagebox.showinfo("Success", "Connections exported successfully")
            else:
                messagebox.showerror("Error", "Failed to export connections")
    
    def create_directory(self):
        """Create new directory."""
        # This would show a dialog to create directory
        messagebox.showinfo("Info", "Create directory dialog would open here")
    
    def delete_selected(self):
        """Delete selected files/directories."""
        # This would delete selected items with confirmation
        messagebox.showinfo("Info", "Delete confirmation dialog would open here")
    
    def toggle_hidden_files(self):
        """Toggle showing hidden files."""
        # This would toggle hidden file visibility
        messagebox.showinfo("Info", "Hidden files toggle would happen here")
    
    def on_connection_selected(self, event=None):
        """Handle connection selection from dropdown."""
        # This could auto-populate quick connect fields
        pass
    
    def show_about(self):
        """Show about dialog."""
        about_text = """SFTP Client v1.0
        
A full-featured SFTP client built with Python and tkinter.

Features:
- Secure file transfers
- Connection management
- Dual-pane interface
- Progress tracking
- Comprehensive logging

Built with Python, Paramiko, and tkinter."""
        
        messagebox.showinfo("About SFTP Client", about_text)


def main():
    """Main entry point for the application."""
    try:
        app = SFTPClientApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()