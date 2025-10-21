"""
GUI Module for SFTP Client

This module provides the main graphical user interface using tkinter.
It includes connection dialogs, file browsers, transfer functionality,
and drag-and-drop support.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from sftp_client import SFTPClient
from config_manager import ConfigManager
from logger import ErrorHandler


class DragDropConfirmDialog:
    """Dialog to confirm drag-and-drop operations."""
    
    def __init__(self, parent, source_files: List[str], source_type: str, 
                 dest_type: str, config_manager: ConfigManager):
        self.parent = parent
        self.source_files = source_files
        self.source_type = source_type  # "local" or "remote"
        self.dest_type = dest_type      # "local" or "remote"
        self.config_manager = config_manager
        self.result = None
        self.dont_prompt = False
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Confirm File Transfer")
        self.dialog.geometry("450x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"450x200+{x}+{y}")
        
        self.create_widgets()
        
        # Focus on the confirm button
        self.confirm_button.focus_set()
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.confirm())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icon and message
        message_frame = ttk.Frame(main_frame)
        message_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Icon (you could add an actual icon here)
        icon_label = ttk.Label(message_frame, text="📁→📁", font=("Arial", 16))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Message
        action = "upload" if self.source_type == "local" else "download"
        direction = f"{self.source_type} to {self.dest_type}"
        
        if len(self.source_files) == 1:
            message = f"Copy '{self.source_files[0]}' from {direction}?"
        else:
            message = f"Copy {len(self.source_files)} items from {direction}?"
        
        message_label = ttk.Label(message_frame, text=message, wraplength=350)
        message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # File list (if multiple files)
        if len(self.source_files) > 1:
            files_frame = ttk.LabelFrame(main_frame, text="Files to transfer:", padding="5")
            files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            # Create scrollable listbox for files
            listbox_frame = ttk.Frame(files_frame)
            listbox_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(listbox_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, height=4)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar.config(command=listbox.yview)
            
            for file in self.source_files:
                listbox.insert(tk.END, file)
        
        # Don't prompt checkbox
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.dont_prompt_var = tk.BooleanVar()
        self.dont_prompt_checkbox = ttk.Checkbutton(
            checkbox_frame, 
            text="Don't prompt for this action in the future",
            variable=self.dont_prompt_var
        )
        self.dont_prompt_checkbox.pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        self.confirm_button = ttk.Button(button_frame, text="Copy", command=self.confirm)
        self.confirm_button.pack(side=tk.RIGHT)
    
    def confirm(self):
        """Confirm the transfer."""
        self.result = True
        self.dont_prompt = self.dont_prompt_var.get()
        
        # Save the preference if requested
        if self.dont_prompt:
            key = f"transfer.confirm_{self.source_type}_to_{self.dest_type}"
            self.config_manager.set_setting(key, False)
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel the transfer."""
        self.result = False
        self.dialog.destroy()


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
    """Frame containing file list with operations and drag-and-drop support."""
    
    def __init__(self, parent, title: str, is_remote: bool = False):
        super().__init__(parent)
        self.title = title
        self.is_remote = is_remote
        self.current_path = "/" if is_remote else os.getcwd()
        self.sftp_client = None
        self.logger = logging.getLogger(__name__)
        self.config_manager = None
        self.transfer_callback = None
        
        # Drag and drop state (keeping for future use)
        self.drag_data = {"items": [], "start_x": 0, "start_y": 0}
        self.drop_target = None
        self.double_click_pending = False
        
        # Clipboard for copy/cut operations
        self.clipboard = {"files": [], "operation": None, "source_frame": None}
        
        self.create_widgets()
        self.refresh_list()
    
    def set_config_manager(self, config_manager):
        """Set the configuration manager for drag-drop preferences."""
        self.config_manager = config_manager
    
    def set_transfer_callback(self, callback):
        """Set the callback function for file transfers."""
        self.transfer_callback = callback
    
    def set_drop_target(self, target_frame):
        """Set the target frame for drag-and-drop operations."""
        self.drop_target = target_frame
    
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
        
        # TEMPORARILY DISABLED: Drag and drop events - use different binding pattern to avoid conflicts
        # self.file_tree.bind("<Button-1>", self.on_mouse_down)
        # self.file_tree.bind("<B1-Motion>", self.on_mouse_drag)
        # self.file_tree.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # Track double-click state to prevent drag interference
        self.double_click_pending = False
        
        # Keyboard shortcuts
        self.file_tree.bind("<Control-c>", self.copy_files)
        self.file_tree.bind("<Control-x>", self.cut_files)
        self.file_tree.bind("<Control-v>", self.paste_files)
        self.file_tree.bind("<Delete>", self.delete_files)
        self.file_tree.bind("<F5>", lambda e: self.refresh_list())
        
        # Focus handling for keyboard shortcuts
        self.file_tree.bind("<FocusIn>", self.on_focus_in)
        
        # Clipboard for copy/cut operations
        self.clipboard = {"files": [], "operation": None, "source_frame": None}
    
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
                from sftp_client import SFTPClient
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
        
        self.logger.info(f"Double-click on: {filename}, is_directory: {'directory' in self.file_tree.item(selection[0], 'tags')}")
        
        # Check if it's a directory
        if "directory" in self.file_tree.item(selection[0], "tags"):
            new_path = os.path.join(self.current_path, filename) if not self.is_remote else f"{self.current_path.rstrip('/')}/{filename}"
            self.logger.info(f"Attempting to change directory to: {new_path}")
            
            if self.change_directory(new_path):
                self.current_path = new_path
                self.path_var.set(self.current_path)
                self.refresh_list()
                self.logger.info(f"Successfully changed to directory: {new_path}")
            else:
                self.logger.error(f"Failed to change to directory: {new_path}")
        else:
            self.logger.info(f"Double-clicked on file: {filename}")
    
    def on_right_click(self, event):
        """Handle right-click context menu."""
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.show_context_menu(event)
    
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
    
    # Drag and Drop Event Handlers
    
    def on_mouse_down(self, event):
        """Handle mouse down event for drag start."""
        # Don't start drag operations during double-click
        if self.double_click_pending:
            return
            
        item = self.file_tree.identify_row(event.y)
        if item:
            # Select the item if not already selected
            if item not in self.file_tree.selection():
                self.file_tree.selection_set(item)
            
            # Store initial drag position and selected items
            self.drag_data["start_x"] = event.x
            self.drag_data["start_y"] = event.y
            self.drag_data["items"] = list(self.file_tree.selection())
    
    def on_mouse_drag(self, event):
        """Handle mouse drag event."""
        # Don't perform drag operations during double-click
        if self.double_click_pending:
            return
            
        # Check if we've moved far enough to start a drag operation
        if (self.drag_data["items"] and 
            (abs(event.x - self.drag_data["start_x"]) > 5 or 
             abs(event.y - self.drag_data["start_y"]) > 5)):
            
            # Change cursor to indicate drag operation
            self.file_tree.config(cursor="hand2")
            
            # Highlight selected items
            for item in self.drag_data["items"]:
                self.file_tree.set(item, "name", f"▶ {self.file_tree.item(item)['values'][0]}")
    
    def on_mouse_release(self, event):
        """Handle mouse release event for drag end."""
        # Don't handle drag release during double-click
        if self.double_click_pending:
            return
            
        # Reset cursor
        self.file_tree.config(cursor="")
        
        # Check if we're over a valid drop target
        if self.drop_target and self.drag_data["items"]:
            # Get the widget under the mouse
            widget = event.widget.winfo_containing(event.x_root, event.y_root)
            
            # Check if we're dropping on the target frame
            if widget and self.is_widget_in_frame(widget, self.drop_target):
                self.perform_drop()
        
        # Clean up drag highlighting (only if not during double-click)
        if not self.double_click_pending:
            self.refresh_list()
        
        # Clear drag data
        self.drag_data = {"items": [], "start_x": 0, "start_y": 0}
    
    def on_drag_enter(self, event):
        """Handle drag enter event."""
        if hasattr(self, 'drop_target') and self.drop_target:
            # Visual feedback when entering drop zone
            self.configure(relief="solid", borderwidth=2)
    
    def on_drag_leave(self, event):
        """Handle drag leave event."""
        # Remove visual feedback when leaving drop zone
        self.configure(relief="flat", borderwidth=0)
    
    def is_widget_in_frame(self, widget, frame):
        """Check if a widget is contained within a frame."""
        try:
            parent = widget
            while parent:
                if parent == frame or parent == frame.file_tree:
                    return True
                parent = parent.master
            return False
        except:
            return False
    
    def show_context_menu(self, event):
        """Show context menu for file operations."""
        context_menu = tk.Menu(self, tearoff=0)
        
        selection = self.file_tree.selection()
        if not selection:
            return
        
        # Get selected items info
        selected_files = self.get_selected_files()
        is_single_dir = (len(selected_files) == 1 and 
                        "directory" in self.file_tree.item(selection[0], "tags"))
        
        # File operations
        if selected_files:
            context_menu.add_command(label="Copy", command=self.copy_files, accelerator="Ctrl+C")
            context_menu.add_command(label="Cut", command=self.cut_files, accelerator="Ctrl+X")
            context_menu.add_separator()
            
            # Transfer operations
            if self.drop_target:
                if self.is_remote:
                    context_menu.add_command(label="Download to Local", command=self.download_selected)
                else:
                    context_menu.add_command(label="Upload to Remote", command=self.upload_selected)
                context_menu.add_separator()
            
            # Single directory operations
            if is_single_dir:
                context_menu.add_command(label="Open", command=lambda: self.on_double_click(event))
                context_menu.add_separator()
            
            context_menu.add_command(label="Delete", command=self.delete_files, accelerator="Del")
            context_menu.add_command(label="Rename", command=self.rename_file)
            context_menu.add_separator()
        
        # Paste operation
        if self.clipboard["files"]:
            paste_label = f"Paste ({len(self.clipboard['files'])} items)"
            context_menu.add_command(label=paste_label, command=self.paste_files, accelerator="Ctrl+V")
            context_menu.add_separator()
        
        # General operations
        context_menu.add_command(label="New Folder", command=self.create_folder)
        context_menu.add_command(label="Refresh", command=self.refresh_list, accelerator="F5")
        
        # Properties
        if len(selected_files) == 1:
            context_menu.add_separator()
            context_menu.add_command(label="Properties", command=self.show_properties)
        
        # Show the menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def copy_files(self, event=None):
        """Copy selected files to clipboard."""
        selected_files = self.get_selected_files()
        if selected_files:
            self.clipboard = {
                "files": selected_files,
                "operation": "copy",
                "source_frame": self
            }
            self.logger.info(f"Copied {len(selected_files)} files to clipboard")
            # Visual feedback
            self.after(100, lambda: messagebox.showinfo("Copy", f"Copied {len(selected_files)} items"))
    
    def cut_files(self, event=None):
        """Cut selected files to clipboard."""
        selected_files = self.get_selected_files()
        if selected_files:
            self.clipboard = {
                "files": selected_files,
                "operation": "cut",
                "source_frame": self
            }
            self.logger.info(f"Cut {len(selected_files)} files to clipboard")
            # Visual feedback - could highlight cut files differently
            self.after(100, lambda: messagebox.showinfo("Cut", f"Cut {len(selected_files)} items"))
    
    def paste_files(self, event=None):
        """Paste files from clipboard."""
        if not self.clipboard["files"] or not self.clipboard["source_frame"]:
            messagebox.showwarning("Paste", "No files in clipboard")
            return
        
        source_frame = self.clipboard["source_frame"]
        operation = self.clipboard["operation"]
        files = self.clipboard["files"]
        
        # Determine if this is a transfer operation
        if source_frame != self and self.drop_target:
            # This is a transfer between panels
            source_type = "remote" if source_frame.is_remote else "local"
            dest_type = "remote" if self.is_remote else "local"
            
            # Show confirmation dialog
            confirm_key = f"transfer.confirm_{source_type}_to_{dest_type}"
            should_confirm = True
            
            if self.config_manager:
                should_confirm = self.config_manager.get_setting(confirm_key, True)
            
            if should_confirm and self.config_manager:
                dialog = DragDropConfirmDialog(
                    self.winfo_toplevel(),
                    files,
                    source_type,
                    dest_type,
                    self.config_manager
                )
                self.wait_window(dialog.dialog)
                
                if not dialog.result:
                    return  # User cancelled
            
            # Perform transfer
            if self.transfer_callback:
                if self.is_remote:
                    # Upload from local to remote
                    self.transfer_callback(files, upload=True)
                else:
                    # Download from remote to local  
                    self.transfer_callback(files, upload=False)
                
                # Clear clipboard after cut operation
                if operation == "cut":
                    self.clipboard = {"files": [], "operation": None, "source_frame": None}
            else:
                messagebox.showerror("Error", "Transfer functionality not available")
        else:
            # Local file operations (copy/move within same panel)
            messagebox.showinfo("Paste", f"Local {operation} operations not yet implemented")
    
    def download_selected(self):
        """Download selected files from remote to local."""
        selected_files = self.get_selected_files()
        if selected_files and self.transfer_callback:
            if self.is_remote:
                self.transfer_callback(selected_files, upload=False)
            else:
                messagebox.showwarning("Download", "This is already the local panel")
    
    def upload_selected(self):
        """Upload selected files from local to remote."""
        selected_files = self.get_selected_files()
        if selected_files and self.transfer_callback:
            if not self.is_remote:
                self.transfer_callback(selected_files, upload=True)
            else:
                messagebox.showwarning("Upload", "This is already the remote panel")
    
    def delete_files(self, event=None):
        """Delete selected files."""
        selected_files = self.get_selected_files()
        if not selected_files:
            return
        
        # Confirm deletion
        file_list = "\n".join(selected_files[:5])  # Show first 5 files
        if len(selected_files) > 5:
            file_list += f"\n... and {len(selected_files) - 5} more"
        
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_files)} item(s)?\n\n{file_list}",
            icon="warning"
        )
        
        if result:
            self.logger.info(f"Deleting {len(selected_files)} files")
            messagebox.showinfo("Delete", f"Delete operation for {len(selected_files)} items not yet implemented")
    
    def rename_file(self):
        """Rename selected file."""
        selected_files = self.get_selected_files()
        if len(selected_files) != 1:
            messagebox.showwarning("Rename", "Please select exactly one item to rename")
            return
        
        old_name = selected_files[0]
        new_name = simpledialog.askstring("Rename", f"Rename '{old_name}' to:", initialvalue=old_name)
        
        if new_name and new_name != old_name:
            self.logger.info(f"Renaming '{old_name}' to '{new_name}'")
            messagebox.showinfo("Rename", f"Rename operation not yet implemented")
    
    def create_folder(self):
        """Create a new folder."""
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        
        if folder_name:
            self.logger.info(f"Creating folder: {folder_name}")
            messagebox.showinfo("New Folder", f"Create folder operation not yet implemented")
    
    def show_properties(self):
        """Show properties of selected file."""
        selected_files = self.get_selected_files()
        if len(selected_files) != 1:
            return
        
        filename = selected_files[0]
        selection = self.file_tree.selection()[0]
        item = self.file_tree.item(selection)
        
        properties = f"Name: {filename}\n"
        properties += f"Size: {item['values'][1]}\n"
        properties += f"Modified: {item['values'][2]}\n"
        properties += f"Permissions: {item['values'][3]}\n"
        properties += f"Type: {'Directory' if 'directory' in self.file_tree.item(selection, 'tags') else 'File'}"
        
        messagebox.showinfo(f"Properties - {filename}", properties)
    
    def on_focus_in(self, event):
        """Handle focus in event for keyboard shortcuts."""
        # This ensures keyboard shortcuts work when the file list has focus
        pass