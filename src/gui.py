"""
GUI Module for SFTP Client

This module provides the main graphical user interface using tkinter.
It includes connection dialogs, file browsers, and transfer functionality.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from .sftp_client import SFTPClient
from .config_manager import ConfigManager
from .logger import ErrorHandler


class ProgressDialog:
    """Dialog to show transfer progress."""
    
    def __init__(self, parent, title: str, total_size: int = 0):
        self.parent = parent
        self.total_size = total_size
        self.transferred = 0
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x120")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (120 // 2)
        self.dialog.geometry(f"400x120+{x}+{y}")
        
        # Progress widgets
        self.progress_label = ttk.Label(self.dialog, text="Preparing transfer...")
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(
            self.dialog, 
            mode='determinate' if total_size > 0 else 'indeterminate',
            length=350
        )
        self.progress_bar.pack(pady=5)
        
        if total_size == 0:
            self.progress_bar.start()
        
        self.cancel_button = ttk.Button(self.dialog, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=10)
        
        self.cancelled = False
    
    def update_progress(self, transferred: int, total: int):
        """Update progress bar and label."""
        if self.cancelled:
            return
        
        self.transferred = transferred
        if total > 0:
            self.total_size = total
            progress = (transferred / total) * 100
            self.progress_bar['value'] = progress
            
            # Format sizes
            transferred_mb = transferred / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.progress_label.config(
                text=f"Transferred: {transferred_mb:.1f} MB / {total_mb:.1f} MB ({progress:.1f}%)"
            )
    
    def cancel(self):
        """Cancel the operation."""
        self.cancelled = True
        self.dialog.destroy()
    
    def close(self):
        """Close the dialog."""
        if not self.cancelled:
            self.dialog.destroy()


class ConnectionDialog:
    """Dialog for creating/editing server connections."""
    
    def __init__(self, parent, config_manager: ConfigManager, connection_data: Dict = None):
        self.parent = parent
        self.config_manager = config_manager
        self.connection_data = connection_data or {}
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Server Connection" if not connection_data else "Edit Connection")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        self.load_data()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
    
    def create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Connection name
        ttk.Label(main_frame, text="Connection Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        # Host
        ttk.Label(main_frame, text="Host:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.host_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.host_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Port
        ttk.Label(main_frame, text="Port:").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=2)
        self.port_var = tk.StringVar(value="22")
        port_entry = ttk.Entry(main_frame, textvariable=self.port_var, width=8)
        port_entry.grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # Username
        ttk.Label(main_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.username_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.username_var, width=40).grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        # Authentication method
        ttk.Label(main_frame, text="Authentication:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.auth_method = tk.StringVar(value="password")
        auth_frame = ttk.Frame(main_frame)
        auth_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_method, 
                       value="password", command=self.on_auth_change).pack(side=tk.LEFT)
        ttk.Radiobutton(auth_frame, text="Private Key", variable=self.auth_method, 
                       value="key", command=self.on_auth_change).pack(side=tk.LEFT, padx=(20, 0))
        
        # Password
        ttk.Label(main_frame, text="Password:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, 
                                       show="*", width=40)
        self.password_entry.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        # Private key file
        ttk.Label(main_frame, text="Private Key:").grid(row=5, column=0, sticky=tk.W, pady=2)
        key_frame = ttk.Frame(main_frame)
        key_frame.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        self.key_path_var = tk.StringVar()
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_path_var, width=30)
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_button = ttk.Button(key_frame, text="Browse", command=self.browse_key_file)
        self.browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=6, column=0, sticky=tk.W, pady=(10, 2))
        self.description_text = tk.Text(main_frame, height=4, width=40)
        self.description_text.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=4, pady=20)
        
        ttk.Button(button_frame, text="Test Connection", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        
        self.on_auth_change()
    
    def on_auth_change(self):
        """Handle authentication method change."""
        if self.auth_method.get() == "password":
            self.password_entry.config(state="normal")
            self.key_entry.config(state="disabled")
            self.browse_button.config(state="disabled")
        else:
            self.password_entry.config(state="disabled")
            self.key_entry.config(state="normal")
            self.browse_button.config(state="normal")
    
    def browse_key_file(self):
        """Browse for private key file."""
        filename = filedialog.askopenfilename(
            title="Select Private Key File",
            filetypes=[
                ("Private Key Files", "*.pem *.key *.ppk"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.key_path_var.set(filename)
    
    def load_data(self):
        """Load existing connection data."""
        if self.connection_data:
            self.name_var.set(self.connection_data.get("name", ""))
            self.host_var.set(self.connection_data.get("host", ""))
            self.port_var.set(str(self.connection_data.get("port", 22)))
            self.username_var.set(self.connection_data.get("username", ""))
            self.key_path_var.set(self.connection_data.get("private_key_path", ""))
            self.description_text.insert("1.0", self.connection_data.get("description", ""))
            
            if self.connection_data.get("private_key_path"):
                self.auth_method.set("key")
            else:
                self.auth_method.set("password")
            
            self.on_auth_change()
    
    def test_connection(self):
        """Test the connection settings."""
        try:
            # Validate inputs
            if not self.host_var.get() or not self.username_var.get():
                messagebox.showerror("Error", "Host and username are required")
                return
            
            # Create temporary SFTP client
            client = SFTPClient()
            
            success = client.connect(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                username=self.username_var.get(),
                password=self.password_var.get() if self.auth_method.get() == "password" else None,
                private_key_path=self.key_path_var.get() if self.auth_method.get() == "key" else None
            )
            
            if success:
                messagebox.showinfo("Success", "Connection test successful!")
                client.disconnect()
            else:
                messagebox.showerror("Error", "Connection test failed")
                
        except Exception as e:
            messagebox.showerror("Error", f"Connection test failed: {e}")
    
    def save(self):
        """Save the connection."""
        try:
            # Validate inputs
            if not all([self.name_var.get(), self.host_var.get(), self.username_var.get()]):
                messagebox.showerror("Error", "Name, host, and username are required")
                return
            
            self.result = {
                "name": self.name_var.get(),
                "host": self.host_var.get(),
                "port": int(self.port_var.get()),
                "username": self.username_var.get(),
                "password": self.password_var.get() if self.auth_method.get() == "password" else None,
                "private_key_path": self.key_path_var.get() if self.auth_method.get() == "key" else None,
                "description": self.description_text.get("1.0", tk.END).strip()
            }
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save connection: {e}")
    
    def cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()


class FileListFrame(ttk.Frame):
    """Frame containing file list with operations."""
    
    def __init__(self, parent, title: str, is_remote: bool = False):
        super().__init__(parent)
        self.title = title
        self.is_remote = is_remote
        self.current_path = "/" if is_remote else os.getcwd()
        self.sftp_client = None
        self.logger = logging.getLogger(__name__)
        
        self.create_widgets()
        self.refresh_list()
    
    def create_widgets(self):
        """Create the widgets for the file list."""
        # Title and path
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(title_frame, text=self.title, font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Path navigation
        path_frame = ttk.Frame(self)
        path_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.path_var = tk.StringVar(value=self.current_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        path_entry.bind('<Return>', self.on_path_change)
        
        ttk.Button(path_frame, text="Go", command=self.on_path_change).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(path_frame, text="Up", command=self.go_up).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(path_frame, text="Refresh", command=self.refresh_list).pack(side=tk.RIGHT, padx=(5, 0))
        
        # File list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for file list
        columns = ("name", "size", "modified", "permissions")
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings")
        
        # Configure columns
        self.file_tree.heading("#0", text="", anchor=tk.W)
        self.file_tree.column("#0", width=20, minwidth=20)
        
        self.file_tree.heading("name", text="Name", anchor=tk.W)
        self.file_tree.column("name", width=200, minwidth=150)
        
        self.file_tree.heading("size", text="Size", anchor=tk.E)
        self.file_tree.column("size", width=80, minwidth=60)
        
        self.file_tree.heading("modified", text="Modified", anchor=tk.W)
        self.file_tree.column("modified", width=120, minwidth=100)
        
        self.file_tree.heading("permissions", text="Permissions", anchor=tk.W)
        self.file_tree.column("permissions", width=100, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Bind events
        self.file_tree.bind("<Double-1>", self.on_double_click)
        self.file_tree.bind("<Button-3>", self.on_right_click)  # Right-click context menu
    
    def set_sftp_client(self, client: SFTPClient):
        """Set the SFTP client for remote operations."""
        self.sftp_client = client
        if self.is_remote and client and client.is_connected:
            self.current_path = client.current_remote_path
            self.path_var.set(self.current_path)
            self.refresh_list()
    
    def refresh_list(self):
        """Refresh the file list."""
        try:
            # Clear existing items
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            
            if self.is_remote:
                if not self.sftp_client or not self.sftp_client.is_connected:
                    return
                files = self.sftp_client.list_remote_directory(self.current_path)
            else:
                from .sftp_client import SFTPClient
                temp_client = SFTPClient()
                temp_client.current_local_path = self.current_path
                files = temp_client.list_local_directory(self.current_path)
            
            # Add files to tree
            for file_info in files:
                icon = "📁" if file_info["is_directory"] else "📄"
                size_str = self.format_size(file_info["size"]) if not file_info["is_directory"] else ""
                modified_str = file_info["modified"].strftime("%Y-%m-%d %H:%M") if file_info["modified"] else ""
                
                self.file_tree.insert("", tk.END, 
                                    text=icon,
                                    values=(file_info["name"], size_str, modified_str, file_info["permissions"]),
                                    tags=("directory" if file_info["is_directory"] else "file",))
            
            # Configure tags
            self.file_tree.tag_configure("directory", foreground="blue")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh file list: {e}")
            messagebox.showerror("Error", f"Failed to refresh file list: {e}")
    
    def format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    
    def on_path_change(self, event=None):
        """Handle path change."""
        new_path = self.path_var.get()
        if self.change_directory(new_path):
            self.current_path = new_path
            self.refresh_list()
        else:
            self.path_var.set(self.current_path)  # Revert to current path
    
    def go_up(self):
        """Go to parent directory."""
        if self.is_remote:
            parent_path = "/".join(self.current_path.rstrip("/").split("/")[:-1]) or "/"
        else:
            parent_path = str(Path(self.current_path).parent)
        
        if self.change_directory(parent_path):
            self.current_path = parent_path
            self.path_var.set(self.current_path)
            self.refresh_list()
    
    def change_directory(self, path: str) -> bool:
        """Change to the specified directory."""
        try:
            if self.is_remote:
                if self.sftp_client and self.sftp_client.is_connected:
                    return self.sftp_client.change_remote_directory(path)
                return False
            else:
                if os.path.isdir(path):
                    os.chdir(path)
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to change directory: {e}")
            messagebox.showerror("Error", f"Failed to change directory: {e}")
            return False
    
    def on_double_click(self, event):
        """Handle double-click on file/directory."""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item = self.file_tree.item(selection[0])
        filename = item["values"][0]
        
        # Check if it's a directory
        if "directory" in self.file_tree.item(selection[0], "tags"):
            new_path = os.path.join(self.current_path, filename) if not self.is_remote else f"{self.current_path.rstrip('/')}/{filename}"
            if self.change_directory(new_path):
                self.current_path = new_path
                self.path_var.set(self.current_path)
                self.refresh_list()
    
    def on_right_click(self, event):
        """Handle right-click context menu."""
        # This would typically show a context menu
        # For now, just select the item
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
    
    def get_selected_files(self) -> List[str]:
        """Get list of selected filenames."""
        selection = self.file_tree.selection()
        files = []
        for item in selection:
            filename = self.file_tree.item(item)["values"][0]
            files.append(filename)
        return files
    
    def get_current_path(self) -> str:
        """Get the current directory path."""
        return self.current_path