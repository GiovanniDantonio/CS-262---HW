"""
GUI client adapter for fault-tolerant chat system.
"""
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, ttk, messagebox, scrolledtext
import hashlib
import logging
from datetime import datetime
import json
import os

from .client import ChatClient as FTClient
from ..common.protocol import MessageType, StatusCode

logger = logging.getLogger(__name__)

class GUIClient:
    def __init__(self, master):
        self.master = master
        self.master.title('Fault-Tolerant Chat Client - Login')
        self.master.geometry('600x800')
        
        # Initialize fault-tolerant client
        config_path = os.path.join(os.path.dirname(__file__), "..", "cluster_config.json")
        self.ft_client = FTClient(config_path)
        
        # GUI state
        self.username = None
        self._logging_out = False
        
        # Create initial connection
        try:
            if not self.ft_client.connect():
                raise ConnectionError("Could not connect to any node in the cluster")
            logger.info("Connected to cluster successfully")
            
            # Register broadcast handler
            self.ft_client.register_handler(MessageType.BROADCAST,
                                         self.handle_broadcast_message)
            
        except Exception as e:
            logger.error(f"Could not connect to cluster: {e}")
            messagebox.showerror('Connection Error', f'Could not connect to cluster: {e}')
            self.master.destroy()
            return
        
        self.create_login_widgets()
    
    def create_login_widgets(self):
        """Create the login interface."""
        self.clear_window()
        self.login_frame = ttk.Frame(self.master, padding="10")
        self.login_frame.pack(expand=True)
        
        ttk.Label(self.login_frame, text='Username:').grid(row=0, column=0, sticky='e', pady=5)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.login_frame, text='Password:').grid(row=1, column=0, sticky='e', pady=5)
        self.password_entry = ttk.Entry(self.login_frame, show='*')
        self.password_entry.grid(row=1, column=1, padx=5)
        
        button_frame = ttk.Frame(self.login_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.register_button = ttk.Button(button_frame, text='Register', command=self.register)
        self.register_button.pack(side=tk.LEFT, padx=5)
        
        self.login_button = ttk.Button(button_frame, text='Login', command=self.login)
        self.login_button.pack(side=tk.LEFT, padx=5)
    
    def create_chat_widgets(self):
        """Create the main chat interface."""
        self.clear_window()
        self.master.title(f'Fault-Tolerant Chat Client - {self.username}')
        
        # Main container
        self.chat_frame = ttk.Frame(self.master, padding="10")
        self.chat_frame.pack(fill='both', expand=True)

        # Top frame for user list and search
        top_frame = ttk.Frame(self.chat_frame)
        top_frame.pack(fill='x', pady=(0, 10))
        
        # User list frame
        user_frame = ttk.LabelFrame(top_frame, text="Online Users", padding="5")
        user_frame.pack(side=tk.LEFT, fill='both', expand=True)
        
        self.user_search = ttk.Entry(user_frame)
        self.user_search.pack(fill='x', pady=(0, 5))
        
        self.user_listbox = tk.Listbox(user_frame, height=5)
        self.user_listbox.pack(fill='both', expand=True)
        
        refresh_users_btn = ttk.Button(user_frame, text="Refresh Users", command=self.list_accounts)
        refresh_users_btn.pack(fill='x', pady=(5, 0))
        
        # Add logout button to top frame
        self.logout_button = ttk.Button(top_frame, text='Logout', command=self.logout)
        self.logout_button.pack(side=tk.RIGHT, padx=5)

        # Chat display
        chat_display_frame = ttk.LabelFrame(self.chat_frame, text="Messages", padding="5")
        chat_display_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create Treeview for messages
        self.chat_display = ttk.Treeview(
            chat_display_frame,
            columns=('timestamp', 'sender', 'content'),
            show='headings',
            selectmode='extended'
        )
        
        # Configure columns
        self.chat_display.heading('timestamp', text='Time')
        self.chat_display.heading('sender', text='From')
        self.chat_display.heading('content', text='Message')
        
        # Set column widths
        self.chat_display.column('timestamp', width=100)
        self.chat_display.column('sender', width=100)
        self.chat_display.column('content', width=300)
        
        # Configure unread message tag with light yellow background
        self.chat_display.tag_configure('unread', background='#013f4f')
        
        # Bind click event to mark messages as read
        self.chat_display.bind('<ButtonRelease-1>', self.on_message_click)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(chat_display_frame, orient=tk.VERTICAL, command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=scrollbar.set)
        
        # Pack the Treeview and scrollbar
        self.chat_display.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')

        # System message display
        self.system_display = scrolledtext.ScrolledText(
            chat_display_frame,
            wrap=tk.WORD,
            height=4
        )
        self.system_display.pack(fill='x', pady=(5, 0))
        
        # Message input area
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill='x')
        
        ttk.Label(input_frame, text='To:').pack(side=tk.LEFT)
        self.recipient_entry = ttk.Entry(input_frame, width=20)
        self.recipient_entry.pack(side=tk.LEFT, padx=5)
        
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        
        send_btn = ttk.Button(input_frame, text='Send', command=self.send_message)
        send_btn.pack(side=tk.LEFT)

        # Start periodic updates
        self.update_messages()
    
    def clear_window(self):
        """Clear all widgets from the window."""
        for widget in self.master.winfo_children():
            widget.destroy()
    
    def register(self):
        """Register a new account."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror('Error', 'Please enter both username and password')
            return
        
        if self.ft_client.create_account(username, password):
            messagebox.showinfo('Success', 'Account created successfully')
            self.username = username
            self.create_chat_widgets()
        else:
            messagebox.showerror('Error', 'Failed to create account')
    
    def login(self):
        """Log in to an existing account."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror('Error', 'Please enter both username and password')
            return
        
        if self.ft_client.login(username, password):
            messagebox.showinfo('Success', 'Logged in successfully')
            self.username = username
            self.create_chat_widgets()
        else:
            messagebox.showerror('Error', 'Failed to log in')
    
    def logout(self):
        """Log out from current account."""
        if self._logging_out:
            return
        
        self._logging_out = True
        if self.ft_client.logout():
            self.username = None
            self.create_login_widgets()
        else:
            messagebox.showerror('Error', 'Failed to log out')
        self._logging_out = False
    
    def send_message(self):
        """Send a message."""
        recipient = self.recipient_entry.get()
        content = self.message_entry.get()
        
        if not recipient or not content:
            messagebox.showerror('Error', 'Please enter both recipient and message')
            return
        
        if self.ft_client.send_message(recipient, content):
            self.message_entry.delete(0, tk.END)
            self.update_messages()
        else:
            messagebox.showerror('Error', 'Failed to send message')
    
    def list_accounts(self):
        """Update the user list."""
        accounts = self.ft_client.list_accounts()
        if accounts:
            self.user_listbox.delete(0, tk.END)
            for account in accounts:
                self.user_listbox.insert(tk.END, account)
    
    def update_messages(self):
        """Update the message display."""
        messages = self.ft_client.get_messages()
        if messages:
            self.chat_display.delete(*self.chat_display.get_children())
            for msg in messages:
                self.chat_display.insert(
                    '',
                    'end',
                    values=(
                        msg.get('timestamp', ''),
                        msg.get('sender', ''),
                        msg.get('content', '')
                    ),
                    tags=('unread',) if not msg.get('read', False) else ()
                )
        
        # Schedule next update
        self.master.after(1000, self.update_messages)
    
    def on_message_click(self, event):
        """Handle message click to mark as read."""
        selection = self.chat_display.selection()
        if selection:
            message_ids = [int(item) for item in selection]
            if self.ft_client.mark_as_read(message_ids):
                for item in selection:
                    self.chat_display.item(item, tags=())
    
    def handle_broadcast_message(self, data):
        """Handle broadcast messages from server."""
        msg_type = data.get('type')
        
        if msg_type == 'users':
            # Update user list
            users = data.get('users', [])
            self.user_listbox.delete(0, tk.END)
            for user in users:
                self.user_listbox.insert(tk.END, user)
        
        elif msg_type == 'messages':
            # Update messages
            self.update_messages()
        
        elif msg_type == 'system':
            # Show system message
            self.system_display.insert(tk.END, f"{data.get('message', '')}\n")
            self.system_display.see(tk.END)

def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start GUI
    root = tk.Tk()
    client = GUIClient(root)
    root.mainloop()

if __name__ == '__main__':
    main()
