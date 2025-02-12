import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog, ttk, messagebox, scrolledtext
import protocol as protocol
from protocol import MessageType, StatusCode
import hashlib
import logging
from datetime import datetime
import os


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_client")

# configuration
CONFIG_FILE = "client_config.json"
default_config = {
    "host": "127.0.0.1",
    "port": 12345
}

if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        user_config = json.load(f)
    config = {**default_config, **user_config}
else:
    logger.warning(f"No config file found at {CONFIG_FILE}. Using defaults.")
    config = default_config

SERVER_HOST = config["host"]
SERVER_PORT = config["port"]

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title('Chat Client - Login')
        self.master.geometry('600x800')
        
        # Initialize socket and state
        self.sock = None
        self.username = None
        self._logging_out = False  # Track logout state
        self.stop_event = threading.Event()
        self.listener_thread = None
        
        # Message handlers for different message types
        self.message_handlers = {
            MessageType.CREATE_ACCOUNT.value: self.handle_create_account_response,
            MessageType.LOGIN.value: self.handle_login_response,
            MessageType.LIST_ACCOUNTS.value: self.handle_list_accounts_response,
            MessageType.SEND_MESSAGE.value: self.handle_send_message_response,
            MessageType.GET_MESSAGES.value: self.handle_get_messages_response,
            MessageType.DELETE_MESSAGES.value: self.handle_delete_messages_response,
            MessageType.DELETE_ACCOUNT.value: self.handle_delete_account_response,
            MessageType.LOGOUT.value: self.handle_logout_response,
            MessageType.BROADCAST.value: self.handle_broadcast_message,
            MessageType.ERROR.value: self.handle_error_response,
            MessageType.MARK_AS_READ.value: self.handle_mark_as_read_response
        }
        
        # Create initial connection
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            logger.info("Connected to server successfully")
            
            # Start listener thread
            self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            self.listener_thread.start()
            
        except Exception as e:
            logger.error(f"Could not connect to server: {e}")
            messagebox.showerror('Connection Error', f'Could not connect to server: {e}')
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
        self.master.title(f'Chat Client - {self.username}')
        
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

        # System message display (for notifications, errors, etc.)
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

        # Bottom buttons
        button_frame = ttk.Frame(self.chat_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(button_frame, text='Messages to show:').pack(side=tk.LEFT, padx=5)
        self.message_limit = ttk.Combobox(button_frame, values=['10', '25', '50', '100'], width=5, state='readonly')
        self.message_limit.set('10')  # default value
        self.message_limit.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(button_frame, text='Refresh Messages', command=lambda: self.get_messages(int(self.message_limit.get())))
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = ttk.Button(button_frame, text='Delete Selected', command=self.delete_selected_messages)
        delete_btn.pack(side=tk.LEFT, padx=5)

        delete_account_btn = ttk.Button(button_frame, text='Delete Account', command=self.delete_account)
        delete_account_btn.pack(side=tk.LEFT, padx=5)

        # Start automatic refresh
        self.start_auto_refresh()
        
    def delete_account(self):
        """Send a request to delete the currently logged-in account."""
        if not self.username:
            messagebox.showinfo("No user logged in", "You are not currently logged in.")
            return

        # Get messages first to check unread count
        message = protocol.create_message(
            MessageType.GET_MESSAGES,
            {
                "username": self.username,
                "count": 1000  # Get all messages to check unread status
            }
        )
        protocol.send_custom(self.sock, message)
        
        # The response will be handled by handle_get_messages_response_for_deletion
        self._checking_messages_for_deletion = True

    def handle_get_messages_response_for_deletion(self, messages):
        """Handle get messages response specifically for account deletion."""
        self._checking_messages_for_deletion = False
        
        # Count unread messages
        unread_count = sum(1 for msg in messages if not msg.get('delivered', False))
        
        # Show warning with unread message count
        warning_msg = "Are you sure you want to delete your account?"
        if unread_count > 0:
            warning_msg += f"\n\nWARNING: You have {unread_count} unread message(s) that will be permanently deleted!"
        
        if messagebox.askyesno('Confirm Account Deletion', warning_msg):
            # Send delete account request
            message = protocol.create_message(
                MessageType.DELETE_ACCOUNT,
                {"username": self.username}
            )
            protocol.send_custom(self.sock, message)

    def handle_get_messages_response(self, message: dict):
        """Handle get messages response."""
        if message['status'] == StatusCode.SUCCESS.value:
            messages = message['data']['messages']
            
            # If we're checking messages for deletion, handle that separately
            if hasattr(self, '_checking_messages_for_deletion') and self._checking_messages_for_deletion:
                self.handle_get_messages_response_for_deletion(messages)
                return
            
            # Clear existing messages
            for item in self.chat_display.get_children():
                self.chat_display.delete(item)
            
            if messages:
                # Display messages in reverse order (newest last)
                for msg in reversed(messages):
                    msg_id = msg.get('id', '')
                    timestamp = msg.get('timestamp', '')
                    sender = msg.get('sender', 'unknown')
                    content = msg.get('content', '')
                    read = msg.get('read', 0)  # Default to unread if not specified
                    
                    # Insert into treeview with message ID as item ID
                    item_id = self.chat_display.insert('', 'end', iid=str(msg_id),
                                          values=(timestamp, sender, content))
                    
                    # Only apply unread tag if message is unread
                    if not read:
                        self.chat_display.item(item_id, tags=('unread',))
        else:
            error_msg = message['data'].get('message', 'Unknown error')
            messagebox.showerror('Get Messages Error', f'Failed to get messages: {error_msg}')

    def handle_delete_account_response(self, message: dict):
        """Handle server response to account deletion."""
        if message['status'] == StatusCode.SUCCESS.value:
            # Stop auto-refresh
            self.stop_auto_refresh()
            
            # Clear UI and reset state
            self.username = None
            self.clear_window()
            self.create_login_widgets()
            
            messagebox.showinfo('Success', 'Account deleted successfully')
        else:
            error_msg = message['data'].get('message', 'Unknown error')
            messagebox.showerror('Delete Account Error', f'Failed to delete account: {error_msg}')

    def clear_window(self):
        """Clear all widgets from the window."""
        for widget in self.master.winfo_children():
            widget.destroy()

    def register(self):
        """Handle user registration."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning('Input Error', 'Username and password required.')
            return
        
        # Create new socket connection if needed
        if not self.sock or self._logging_out:
            try:
                # Reset logout state
                self._logging_out = False
                
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((SERVER_HOST, SERVER_PORT))
                logger.info("Reconnected to server successfully")
                
                # Restart listener thread
                self.stop_event.clear()
                self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
                self.listener_thread.start()
                
            except Exception as e:
                logger.error(f"Could not connect to server: {e}")
                messagebox.showerror('Connection Error', f'Could not connect to server: {e}')
                return
            
        logger.debug(f"Attempting to register user: {username}")
        message = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": username,
                "password": hash_password(password)
            }
        )
        protocol.send_custom(self.sock, message)

    def login(self):
        """Handle user login."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning('Input Error', 'Username and password required.')
            return
        
        # Create new socket connection
        try:
            # Reset logout state
            self._logging_out = False
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            logger.info("Reconnected to server successfully")
            
            # Restart listener thread
            self.stop_event.clear()
            self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            self.listener_thread.start()
            
        except Exception as e:
            logger.error(f"Could not connect to server: {e}")
            messagebox.showerror('Connection Error', f'Could not connect to server: {e}')
            return
            
        logger.debug(f"Attempting to login user: {username}")
        message = protocol.create_message(
            MessageType.LOGIN,
            {
                "username": username,
                "password": hash_password(password)
            }
        )
        protocol.send_custom(self.sock, message)

    def list_accounts(self, pattern: str = '%'):
        """Request list of accounts matching pattern."""
        logger.debug(f"Requesting account list with pattern: {pattern}")
        message = protocol.create_message(
            MessageType.LIST_ACCOUNTS,
            {
                "pattern": pattern,
                "page": 1,
                "per_page": 50
            }
        )
        protocol.send_custom(self.sock, message)

    def send_message(self):
        """Send a message to another user."""
        recipient = self.recipient_entry.get().strip()
        content = self.message_entry.get().strip()
        
        if not recipient or not content:
            messagebox.showwarning('Input Error', 'Recipient and message required.')
            return
            
        logger.debug(f"Sending message to {recipient}")
        message = protocol.create_message(
            MessageType.SEND_MESSAGE,
            {
                "username": self.username,
                "recipient": recipient,
                "content": content
            }
        )
        protocol.send_custom(self.sock, message)

    def get_messages(self, count: int = 10):
        """Request recent messages."""
        logger.debug("Requesting messages")
        message = protocol.create_message(
            MessageType.GET_MESSAGES,
            {
                "username": self.username,
                "count": count
            }
        )
        protocol.send_custom(self.sock, message)

    def delete_selected_messages(self):
        """Delete selected messages."""
        selected_items = self.chat_display.selection()
        if not selected_items:
            messagebox.showwarning('Selection Error', 'No messages selected.')
            return
        
        # Convert selected items (which are message IDs) to integers
        selected_ids = [int(item) for item in selected_items]
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            'Confirm Deletion',
            f'Are you sure you want to delete {len(selected_ids)} message(s)?'
        )
        if not confirm:
            return
            
        logger.debug(f"Deleting messages: {selected_ids}")
        message = protocol.create_message(
            MessageType.DELETE_MESSAGES,
            {
                "username": self.username,
                "message_ids": selected_ids
            }
        )
        protocol.send_custom(self.sock, message)

    def start_auto_refresh(self):
        """Start automatic refresh of messages and users as backup."""
        self._refresh_after_id = None  # Store the after ID
        
        def refresh():
            if self.username:  # Only refresh if logged in
                self.get_messages(int(self.message_limit.get()))
                self.list_accounts()
                self._refresh_after_id = self.master.after(5000, refresh)  # Store the ID
            # Don't schedule next refresh if logged out
        refresh()

    def stop_auto_refresh(self):
        """Stop the automatic refresh."""
        if hasattr(self, '_refresh_after_id') and self._refresh_after_id:
            self.master.after_cancel(self._refresh_after_id)
            self._refresh_after_id = None

    def append_chat(self, text: str):
        """Append text to system message display."""
        if hasattr(self, 'system_display') and not self.system_display.winfo_exists():
            self.system_display.config(state='normal')
            self.system_display.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {text}\n")
            self.system_display.see(tk.END)
            self.system_display.config(state='disabled')
        else:
          return

    # Message Handlers
    def handle_create_account_response(self, message: dict):
        """Handle create account response."""
        if message['status'] == StatusCode.SUCCESS.value:
            messagebox.showinfo('Success', 'Account created successfully!')
        else:
            messagebox.showerror('Error', message['data'].get('message', 'Unknown error'))

    def handle_login_response(self, message: dict):
        """Handle login response."""
        if message['status'] == StatusCode.SUCCESS.value:
            self.username = message['data']['username']
            unread_count = message['data'].get('unread_count', 0)
            logger.debug(f"Login successful. Unread count for {self.username}: {unread_count}")
            
            # Create the main chat widgets
            self.create_chat_widgets()
            self.master.after(500, lambda: messagebox.showinfo(
            "Unread Messages",
            f"You have {unread_count} unread message(s)."
            ))
            # Initial data load happens in start_auto_refresh
        else:
            messagebox.showerror('Login Error', message['data'].get('message', 'Login failed'))
    
    def handle_logout_response(self, message: dict):
        """Handle server response to the logout request."""
        if message['status'] == StatusCode.SUCCESS.value:
            # UI is already cleared, just show success message
            messagebox.showinfo('Success', 'Logged out successfully')
            self._logging_out = False
        else:
            error_msg = message['data'].get('message', 'Unknown error')
            messagebox.showerror('Logout Error', f'Failed to logout: {error_msg}')
            # On error, restore the chat interface
            self._logging_out = False
            self.username = message['data'].get('username')
            if self.username:
                self.create_chat_widgets()
                self.start_auto_refresh()


    def handle_list_accounts_response(self, message: dict):
        """Handle account list response."""
        if message['status'] == StatusCode.SUCCESS.value:
            self.user_listbox.delete(0, tk.END)
            for account in message['data']['accounts']:
                self.user_listbox.insert(tk.END, account['username'])

    def handle_send_message_response(self, message: dict):
        """Handle send message response."""
        if message['status'] == StatusCode.SUCCESS.value:
            self.message_entry.delete(0, tk.END)  # Clear message input
            # No need to refresh as we'll get a broadcast
        else:
            error_msg = message['data'].get('message', 'Unknown error')
            self.append_chat(f"Error sending message: {error_msg}")

    def handle_get_messages_response(self, message: dict):
        """Handle get messages response."""
        if message['status'] == StatusCode.SUCCESS.value:
            messages = message['data']['messages']
            
            # If we're checking messages for deletion, handle that separately
            if hasattr(self, '_checking_messages_for_deletion') and self._checking_messages_for_deletion:
                self.handle_get_messages_response_for_deletion(messages)
                return
            
            # Clear existing messages
            for item in self.chat_display.get_children():
                self.chat_display.delete(item)
            
            if messages:
                # Display messages in reverse order (newest last)
                for msg in reversed(messages):
                    msg_id = msg.get('id', '')
                    timestamp = msg.get('timestamp', '')
                    sender = msg.get('sender', 'unknown')
                    content = msg.get('content', '')
                    read = msg.get('read', 0)  # Default to unread if not specified
                    
                    # Insert into treeview with message ID as item ID
                    item_id = self.chat_display.insert('', 'end', iid=str(msg_id),
                                          values=(timestamp, sender, content))
                    
                    # Only apply unread tag if message is unread
                    if not read:
                        self.chat_display.item(item_id, tags=('unread',))
        else:
            error_msg = message['data'].get('message', 'Unknown error')
            messagebox.showerror('Get Messages Error', f'Failed to get messages: {error_msg}')

    def handle_delete_messages_response(self, message: dict):
        """Handle delete messages response."""
        if message['status'] == StatusCode.SUCCESS.value:
            deleted_count = message['data'].get('deleted_count', 0)
            self.append_chat(f"Successfully deleted {deleted_count} message(s).")
            # Refresh messages to update the display
            self.get_messages(int(self.message_limit.get()))
        else:
            error_msg = message['data'].get('message', 'Unknown error')
            self.append_chat(f"Error deleting messages: {error_msg}")

    def handle_delete_account_response(self, message: dict):
        """Handle server response to account deletion."""
        if message['status'] == StatusCode.SUCCESS.value:
            # Stop auto-refresh
            self.stop_auto_refresh()
            
            # Clear UI and reset state
            self.username = None
            self.clear_window()
            self.create_login_widgets()
            
            messagebox.showinfo('Success', 'Account deleted successfully')
        else:
            error_msg = message['data'].get('message', 'Unknown error')
            messagebox.showerror('Delete Account Error', f'Failed to delete account: {error_msg}')

    def handle_broadcast_message(self, message: dict):
        """Handle broadcast messages from server."""
        if not hasattr(self, 'chat_display'):
            return  # Ignore broadcasts if not in chat mode
            
        broadcast_type = message['data'].get('type')
        if broadcast_type == 'users':
            # Update online users list
            users = message['data'].get('users', [])
            self.user_listbox.delete(0, tk.END)
            for user in users:
                if user != self.username:  # Don't show current user
                    self.user_listbox.insert(tk.END, user)
                    
        elif broadcast_type == 'messages':
            # Update messages
            messages = message['data'].get('messages', [])
            for msg in messages:
                msg_id = msg.get('id', '')
                timestamp = msg.get('timestamp', '')
                sender = msg.get('sender', 'unknown')
                content = msg.get('content', '')
                
                # Insert into treeview with message ID as item ID
                self.chat_display.insert('', 'end', iid=str(msg_id),
                                      values=(timestamp, sender, content))

    def handle_error_response(self, message: dict):
        """Handle error response."""
        error_msg = message['data'].get('message', 'Unknown error occurred')
        logger.error(f"Received error: {error_msg}")
        
        # Ignore "not logged in" errors during logout
        if self._logging_out and "not logged in" in error_msg.lower():
            return
            
        # If we're in chat mode (chat_display exists), append to chat
        if hasattr(self, 'chat_display') and not self._logging_out:
            self.append_chat(f"Error: {error_msg}")
        else:
            # Otherwise show error dialog
            messagebox.showerror('Error', error_msg)

    def handle_mark_as_read_response(self, message: dict):
        """Handle mark as read response."""
        if message['status'] != StatusCode.SUCCESS.value:
            error_msg = message['data'].get('message', 'Unknown error')
            logger.error(f"Failed to mark messages as read: {error_msg}")
            # Optionally refresh messages to ensure correct state
            self.get_messages()

    def on_message_click(self, event):
        """Handle message click event."""
        item = self.chat_display.identify_row(event.y)
        if item and self.chat_display.item(item, 'tags') == ('unread',):
            # Mark message as read locally
            self.chat_display.item(item, tags=())  # Remove 'unread' tag
            
            # Send read confirmation to server
            message = protocol.create_message(
                MessageType.MARK_AS_READ,
                {
                    "username": self.username,
                    "message_ids": [int(item)]
                }
            )
            protocol.send_custom(self.sock, message)

    def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        while not self.stop_event.is_set():
            try:
                message = protocol.recv_custom(self.sock)
                if not message:
                    logger.warning("Received empty message from server")
                    continue
                    
                if isinstance(message, str):  # Error occurred
                    logger.error(f"Error receiving message: {message}")
                    continue
                    
                logger.debug(f"Received message: {message}")
                
                # If we're logging out, only process logout responses
                if self._logging_out and message['type'] != MessageType.LOGOUT.value:
                    logger.debug(f"Ignoring message during logout: {message['type']}")
                    continue
                
                # Route message to appropriate handler
                msg_type = message['type']
                handler = self.message_handlers.get(msg_type)
                
                if handler:
                    self.master.after(0, handler, message)
                else:
                    logger.warning(f"No handler for message type: {msg_type}")
                    
            except Exception as e:
                if not self._logging_out:  # Only log error if not intentionally logging out
                    logger.error(f"Error in message listener: {e}")
                break

    def stop_listener(self):
        """Stop the listener thread."""
        self.stop_event.set()

    def logout(self):
        """
        Sends a logout request to the server for the current user.
        The server's response is handled in handle_logout_response.
        """
        if not self.username:
            messagebox.showinfo("No user logged in", "You are not currently logged in.")
            return

        # Set logging out state
        self._logging_out = True
        logger.debug("Starting logout process")
        
        # Stop auto-refresh immediately to prevent race conditions
        self.stop_auto_refresh()
        
        # Build and send the logout request
        logout_msg = protocol.create_message(
            MessageType.LOGOUT,
            {"username": self.username}
        )
        protocol.send_custom(self.sock, logout_msg)
        
        # Give a small delay for the server to process logout
        self.master.after(100, self._complete_logout)

    def _complete_logout(self):
        """Complete the logout process by cleaning up resources."""
        logger.debug("Completing logout process")
        
        # Stop listener thread first
        self.stop_listener()
        
        # Close socket
        try:
            self.sock.close()
            logger.info("Socket closed successfully")
        except Exception as e:
            logger.error(f"Error closing socket: {e}")
        
        # Clear UI and state last
        self.username = None
        self.clear_window()
        self.create_login_widgets()

if __name__ == '__main__':
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
