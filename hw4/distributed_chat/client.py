"""
Client implementation for distributed chat system.
This client is fault-tolerant and will automatically reconnect to another server
if the current server fails or isn't the leader.
"""
import os
import sys
import time
import json
import logging
import hashlib
import threading
import grpc
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Import the generated protobuf modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from distributed_chat import distributed_chat_pb2 as pb2
from distributed_chat import distributed_chat_pb2_grpc as pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("chat_client")

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class FaultTolerantClient:
    """
    A client that handles server failures and leader changes transparently.
    """
    
    def __init__(self, server_list):
        """
        Initialize with a list of server addresses.
        
        Args:
            server_list: List of server addresses [host:port, host:port, ...]
        """
        self.server_list = server_list
        self.current_server = server_list[0] if server_list else None
        self.channel = None
        self.stub = None
        self.leader_info = {}  # Metadata about leader if redirected
        self.lock = threading.RLock()
        self.last_connect_attempt = {}  # Track failed connection attempts
        self.reconnect_backoff = 1.0  # Initial backoff time in seconds
        self.max_backoff = 10.0  # Maximum backoff time
        
        # Connect to initial server
        self.connect()

    def connect(self, server=None):
        """
        Connect to a server, either specified or the current one.
        
        Args:
            server: Optional server address to connect to
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        with self.lock:
            if server:
                self.current_server = server
                
            if not self.current_server:
                logger.error("No server address provided")
                return False
                
            try:
                # Close existing channel if any
                if self.channel:
                    try:
                        self.channel.close()
                    except Exception:
                        pass
                
                logger.info(f"Connecting to server at {self.current_server}")
                
                # Create new connection with timeout
                options = [
                    ('grpc.max_send_message_length', 10 * 1024 * 1024),
                    ('grpc.max_receive_message_length', 10 * 1024 * 1024),
                    ('grpc.keepalive_time_ms', 10000),  # Send keepalive ping every 10 seconds
                    ('grpc.keepalive_timeout_ms', 5000),  # Keepalive ping timeout after 5 seconds
                    ('grpc.keepalive_permit_without_calls', True),  # Allow keepalive pings when no calls are in-flight
                    ('grpc.http2.max_pings_without_data', 0),  # Allow unlimited pings without data
                    ('grpc.enable_retries', 1),  # Enable retries
                ]
                self.channel = grpc.insecure_channel(self.current_server, options=options)
                
                # Set a deadline for the connection attempt
                grpc.channel_ready_future(self.channel).result(timeout=5)
                
                # Create stub for client-server communication
                self.stub = pb2_grpc.ChatServiceStub(self.channel)
                
                # Reset backoff on successful connection
                self.reconnect_backoff = 1.0
                self.last_connect_attempt[self.current_server] = time.time()
                
                logger.info(f"Successfully connected to {self.current_server}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to {self.current_server}: {e}")
                
                # Mark this server as recently failed
                self.last_connect_attempt[self.current_server] = time.time()
                
                # Try to find another server
                if not self._try_next_server():
                    # If all servers failed, increase backoff time
                    self.reconnect_backoff = min(self.reconnect_backoff * 1.5, self.max_backoff)
                    logger.warning(f"All servers unavailable. Will retry in {self.reconnect_backoff} seconds")
                
                return False
                
    def _try_next_server(self):
        """
        Try to connect to another server in the list that hasn't failed recently.
        
        Returns:
            bool: True if successfully connected to another server, False otherwise
        """
        now = time.time()
        
        # Try each server in the list
        for server in self.server_list:
            # Skip current server and recently failed servers
            if server == self.current_server:
                continue
                
            # Skip servers that failed within the backoff period
            last_attempt = self.last_connect_attempt.get(server, 0)
            if now - last_attempt < self.reconnect_backoff:
                continue
                
            logger.info(f"Trying alternative server at {server}")
            if self.connect(server):
                return True
                
        return False
    
    def _handle_server_failure(self, operation_name):
        """
        Handle server failure by trying to reconnect.
        
        Args:
            operation_name: Name of the operation that failed
            
        Returns:
            bool: True if reconnected successfully, False otherwise
        """
        logger.warning(f"Server failure during {operation_name}. Attempting to reconnect.")
        
        # Try to connect to another server
        if self._try_next_server():
            logger.info(f"Reconnected to {self.current_server}. Retrying {operation_name}.")
            return True
            
        # If all servers are down, wait and try again
        time.sleep(self.reconnect_backoff)
        return self.connect()

    def _handle_not_leader(self, response):
        """
        Handle the case where the current server is not the leader.
        
        Args:
            response: Server response containing leader information
            
        Returns:
            bool: True if successfully redirected to leader, False otherwise
        """
        if not hasattr(response, 'message'):
            return False
            
        # Parse leader information from the response message
        message = response.message
        if "try leader at" in message:
            try:
                # Extract leader address from message
                leader_address = message.split("try leader at ")[1].strip()
                
                logger.info(f"Redirecting to leader at {leader_address}")
                
                # Connect to the leader
                if self.connect(leader_address):
                    return True
            except Exception as e:
                logger.error(f"Failed to parse leader address: {e}")
                
        return False
        
    def register(self, username, password):
        """
        Register a new user with the chat service.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            RegisterResponse with success status and message
        """
        with self.lock:
            # Hash password
            password_hash = hash_password(password)
            
            # Create request
            request = pb2.UserCredentials(
                username=username,
                password=password_hash
            )
            
            # Retry loop with backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.stub.Register(request)
                    
                    # If not leader, try redirecting
                    if not response.success and self._handle_not_leader(response):
                        # Retry with new leader
                        response = self.stub.Register(request)
                    
                    return response
                    
                except grpc.RpcError as e:
                    logger.error(f"RPC Error in register: {e}")
                    
                    # Handle server failure
                    if not self._handle_server_failure("register"):
                        # If reconnection failed, return error response
                        return pb2.RegisterResponse(
                            success=False,
                            message=f"Failed to connect to any server after {max_retries} attempts"
                        )
                        
                    # If reconnected, continue retry loop
                    
            # If all retries failed
            return pb2.RegisterResponse(
                success=False,
                message=f"Failed after {max_retries} attempts"
            )

    def call_with_retry(self, method_name, request, retry_count=3):
        """
        Call a gRPC method with automatic retries and server switching.
        
        Args:
            method_name: Name of method to call on stub
            request: Request protobuf message
            retry_count: Number of retries allowed
            
        Returns:
            Response from the method or None if all retries failed
        """
        with self.lock:
            for attempt in range(retry_count):
                try:
                    method = getattr(self.stub, method_name)
                    response = method(request)
                    
                    # If response indicates not leader, try to find leader
                    if not response.success and "Not leader" in response.message:
                        if self._handle_not_leader(response):
                            continue
                    
                    return response
                
                except grpc.RpcError as e:
                    logger.warning(f"RPC error during {method_name}: {e}")
                    if self._handle_server_failure(method_name):
                        continue
                    else:
                        break
                
                except Exception as e:
                    logger.error(f"Error during {method_name}: {e}")
                    break
            
            return None
    
    def start_stream(self, method_name, request, callback):
        """
        Start a streaming RPC call with automatic reconnection.
        
        Args:
            method_name: Name of streaming method to call on stub
            request: Request protobuf message
            callback: Function to call with each stream response
            
        Returns:
            Thread object for the streaming operation
        """
        thread = threading.Thread(
            target=self._stream_worker,
            args=(method_name, request, callback)
        )
        thread.daemon = True
        thread.start()
        return thread
    
    def _stream_worker(self, method_name, request, callback):
        """
        Worker thread for handling streaming RPCs.
        
        Args:
            method_name: Name of streaming method to call on stub
            request: Request protobuf message
            callback: Function to call with each stream response
        """
        retry_delay = 1.0
        max_retry_delay = 30.0
        
        while True:
            try:
                method = getattr(self.stub, method_name)
                stream = method(request)
                
                # Reset retry delay on successful connection
                retry_delay = 1.0
                
                for response in stream:
                    callback(response)
                
            except grpc.RpcError as e:
                logger.warning(f"Stream error in {method_name}: {e}")
                self._handle_server_failure(method_name)
            
            except Exception as e:
                logger.error(f"Error in stream {method_name}: {e}")
            
            # Wait before reconnecting
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)


class ChatClient:
    """
    Chat client UI implementation using tkinter.
    """
    
    def __init__(self, master, server_list):
        """
        Initialize chat client UI.
        
        Args:
            master: tkinter root window
            server_list: List of server addresses [host:port, host:port, ...]
        """
        self.master = master
        self.master.title("Distributed Chat Client - Login")
        self.master.geometry("600x800")
        self.username = None
        
        # Create fault-tolerant client
        self.client = FaultTolerantClient(server_list)
        
        self.stop_event = threading.Event()
        self.listener_thread = None
        
        # Status bar to show connection info
        self.status_var = tk.StringVar()
        self.status_var.set(f"Connected to {self.client.current_server}")
        
        # Build login UI
        self.create_login_widgets()
    
    def clear_window(self):
        """Clear all widgets from the window."""
        for widget in self.master.winfo_children():
            widget.destroy()
    
    def create_login_widgets(self):
        """Create the login screen widgets."""
        self.clear_window()
        
        self.login_frame = ttk.Frame(self.master, padding="10")
        self.login_frame.pack(expand=True)
        
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, sticky="e", pady=5)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, sticky="e", pady=5)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5)
        
        button_frame = ttk.Frame(self.login_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.register_button = ttk.Button(button_frame, text="Register", command=self.register)
        self.register_button.pack(side=tk.LEFT, padx=5)
        
        self.login_button = ttk.Button(button_frame, text="Login", command=self.login)
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        status_frame = ttk.Frame(self.master)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
    
    def create_chat_widgets(self):
        """Create the main chat screen widgets."""
        self.clear_window()
        self.master.title(f"Distributed Chat Client - {self.username}")
        
        self.chat_frame = ttk.Frame(self.master, padding="10")
        self.chat_frame.pack(fill="both", expand=True)
        
        # Top frame: online users and logout button
        top_frame = ttk.Frame(self.chat_frame)
        top_frame.pack(fill="x", pady=(0,10))
        
        user_frame = ttk.LabelFrame(top_frame, text="Online Users", padding="5")
        user_frame.pack(side=tk.LEFT, fill="both", expand=True)
        
        self.user_search = ttk.Entry(user_frame)
        self.user_search.pack(fill="x", pady=(0,5))
        
        self.user_listbox = tk.Listbox(user_frame, height=5)
        self.user_listbox.pack(fill="both", expand=True)
        
        refresh_users_btn = ttk.Button(user_frame, text="Refresh Users", command=self.list_accounts)
        refresh_users_btn.pack(fill="x", pady=(5,0))
        
        self.logout_button = ttk.Button(top_frame, text="Logout", command=self.logout)
        self.logout_button.pack(side=tk.RIGHT, padx=5)
        
        # Chat display area using Treeview
        chat_display_frame = ttk.LabelFrame(self.chat_frame, text="Messages", padding="5")
        chat_display_frame.pack(fill="both", expand=True, pady=(0,10))
        
        self.chat_display = ttk.Treeview(
            chat_display_frame, 
            columns=("timestamp", "sender", "content"), 
            show="headings", 
            selectmode="extended"
        )
        self.chat_display.heading("timestamp", text="Time")
        self.chat_display.heading("sender", text="From")
        self.chat_display.heading("content", text="Message")
        self.chat_display.column("timestamp", width=100)
        self.chat_display.column("sender", width=100)
        self.chat_display.column("content", width=300)
        
        # Configure 'unread' tag to have a blue background
        self.chat_display.tag_configure("unread", background="lightblue")
        self.chat_display.bind("<ButtonRelease-1>", self.on_message_click)
        self.chat_display.pack(fill="both", expand=True)
        
        # Message input area
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill="x")
        
        ttk.Label(input_frame, text="To:").pack(side=tk.LEFT)
        self.recipient_entry = ttk.Entry(input_frame, width=20)
        self.recipient_entry.pack(side=tk.LEFT, padx=5)
        
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        
        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side=tk.LEFT)
        
        # Bottom controls
        button_frame = ttk.Frame(self.chat_frame)
        button_frame.pack(fill="x", pady=(10,0))
        
        ttk.Label(button_frame, text="Messages to show:").pack(side=tk.LEFT, padx=5)
        self.message_limit = ttk.Combobox(button_frame, values=["10", "25", "50", "100"], width=5, state="readonly")
        self.message_limit.set("10")
        self.message_limit.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(
            button_frame, 
            text="Refresh Messages",
            command=lambda: self.get_messages(int(self.message_limit.get()))
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected_messages)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        delete_account_btn = ttk.Button(button_frame, text="Delete Account", command=self.delete_account)
        delete_account_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        status_frame = ttk.Frame(self.master)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Start message streaming
        self.start_message_stream()
    
    def start_message_stream(self):
        """Start streaming messages from the server."""
        self.listener_thread = self.client.start_stream(
            'StreamMessages',
            pb2.Username(username=self.username),
            self.handle_streamed_message
        )
    
    def handle_streamed_message(self, message):
        """
        Handle a message received from the message stream.
        
        Args:
            message: Message protobuf message
        """
        # Check if message already exists in the display
        if any(self.chat_display.item(item, "values")[0] == message.timestamp and
               self.chat_display.item(item, "values")[1] == message.sender for item in self.chat_display.get_children()):
            return
        
        # Insert new message with unread tag
        item_id = self.chat_display.insert(
            "", 0,
            values=(message.timestamp, message.sender, message.content),
            tags=("unread",)
        )
        
        # Store message ID in the item
        self.chat_display.item(item_id, tags=("unread", str(message.id)))
    
    def register(self):
        """Register a new user account."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Input Error", "Username and password required.")
            return
        
        logger.debug(f"Registering user: {username}")
        
        response = self.client.register(username, password)
        
        if response and response.success:
            messagebox.showinfo("Success", "Account created successfully!")
        else:
            messagebox.showerror("Error", response.message if response else "Registration failed.")
        
        # Update status bar
        self.status_var.set(f"Connected to {self.client.current_server}")
    
    def login(self):
        """Log in an existing user."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Input Error", "Username and password required.")
            return
        
        logger.debug(f"Logging in user: {username}")
        
        response = self.client.call_with_retry(
            'Login',
            pb2.UserCredentials(
                username=username,
                password=hash_password(password)
            )
        )
        
        if response and response.success:
            self.username = username
            messagebox.showinfo(
                "Success", 
                f"Login successful! You have {response.unread_count} unread messages."
            )
            self.create_chat_widgets()
        else:
            messagebox.showerror(
                "Login Error", 
                response.message if response else "Login failed."
            )
        
        # Update status bar
        self.status_var.set(f"Connected to {self.client.current_server}")
    
    def logout(self):
        """Log out the current user."""
        if not self.username:
            return
        
        logger.debug(f"Logging out user: {self.username}")
        
        response = self.client.call_with_retry(
            'Logout',
            pb2.Username(username=self.username)
        )
        
        # Stop message streaming
        self.stop_event.set()
        if self.listener_thread:
            self.listener_thread.join(1.0)
        
        self.username = None
        self.create_login_widgets()
        
        # Update status bar
        self.status_var.set(f"Connected to {self.client.current_server}")
    
    def list_accounts(self, pattern="%"):
        """
        List user accounts matching the pattern.
        
        Args:
            pattern: Pattern to match against usernames
        """
        logger.debug(f"Requesting account list with pattern: {pattern}")
        
        response = self.client.call_with_retry(
            'ListAccounts',
            pb2.AccountListRequest(
                pattern=pattern, page=1, per_page=50
            )
        )
        
        if response:
            try:
                self.user_listbox.delete(0, tk.END)
                for account in response.accounts:
                    # Add an indicator for online users
                    display_name = f"{account.username} [ONLINE]" if hasattr(account, 'online') and account.online else account.username
                    self.user_listbox.insert(tk.END, display_name)
                
                # Update status to show successful retrieval
                self.status_var.set(f"Retrieved {len(response.accounts)} accounts. Connected to {self.client.current_server}")
            except Exception as e:
                logger.error(f"Error processing account list: {e}")
                messagebox.showerror("Error", f"Failed to process account list: {e}")
        else:
            messagebox.showerror("Error", "Failed to retrieve account list.")
        
        # Update status bar
        self.status_var.set(f"Connected to {self.client.current_server}")
    
    def send_message(self):
        """Send a message to another user."""
        if not self.username:
            return
        
        recipient = self.recipient_entry.get().strip()
        content = self.message_entry.get().strip()
        
        if not recipient or not content:
            messagebox.showwarning("Input Error", "Recipient and message required.")
            return
        
        logger.debug(f"Sending message from {self.username} to {recipient}")
        
        response = self.client.call_with_retry(
            'SendMessage',
            pb2.Message(
                sender=self.username, 
                recipient=recipient, 
                content=content
            )
        )
        
        if response and response.success:
            self.message_entry.delete(0, tk.END)
        else:
            messagebox.showerror(
                "Error", 
                response.message if response else "Failed to send message."
            )
        
        # Update status bar
        self.status_var.set(f"Connected to {self.client.current_server}")
    
    def get_messages(self, count=10):
        """
        Retrieve messages for the current user.
        
        Args:
            count: Maximum number of messages to retrieve
        """
        if not self.username:
            return
        
        logger.debug(f"Getting messages for {self.username} (limit {count})")
        
        response = self.client.call_with_retry(
            'GetMessages',
            pb2.MessageRequest(
                username=self.username, 
                count=count
            )
        )
        
        if response:
            # Clear existing messages
            self.chat_display.delete(*self.chat_display.get_children())
            
            # Add messages to display
            for message in response.messages:
                item_id = self.chat_display.insert(
                    "", "end",
                    values=(message.timestamp, message.sender, message.content),
                    tags=("unread" if not message.read else (), str(message.id))
                )
        else:
            messagebox.showerror("Error", "Failed to retrieve messages.")
        
        # Update status bar
        self.status_var.set(f"Connected to {self.client.current_server}")
    
    def on_message_click(self, event):
        """
        Handle message click event to mark messages as read.
        
        Args:
            event: Click event
        """
        selected_items = self.chat_display.selection()
        if not selected_items:
            return
        
        # Check if any selected messages are unread
        unread_ids = []
        for item_id in selected_items:
            tags = self.chat_display.item(item_id, "tags")
            if "unread" in tags:
                # Extract message ID from tags
                message_id = next((int(tag) for tag in tags if tag != "unread" and tag.isdigit()), None)
                if message_id is not None:
                    unread_ids.append(message_id)
                    # Remove unread tag locally
                    self.chat_display.item(item_id, tags=(str(message_id),))
        
        # Mark messages as read on server
        if unread_ids:
            self.mark_as_read(unread_ids)
    
    def mark_as_read(self, message_ids):
        """
        Mark messages as read.
        
        Args:
            message_ids: List of message IDs to mark as read
        """
        if not self.username or not message_ids:
            return
        
        logger.debug(f"Marking messages as read: {message_ids}")
        
        response = self.client.call_with_retry(
            'MarkAsRead',
            pb2.MarkAsReadRequest(
                username=self.username, 
                message_ids=message_ids
            )
        )
        
        if not response or not response.success:
            messagebox.showerror(
                "Error", 
                response.message if response else "Failed to mark messages as read."
            )
    
    def delete_selected_messages(self):
        """Delete the currently selected messages."""
        if not self.username:
            return
        
        selected_items = self.chat_display.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No messages selected.")
            return
        
        # Extract message IDs
        message_ids = []
        for item_id in selected_items:
            tags = self.chat_display.item(item_id, "tags")
            message_id = next((int(tag) for tag in tags if tag.isdigit()), None)
            if message_id is not None:
                message_ids.append(message_id)
        
        if not message_ids:
            messagebox.showinfo("Info", "No valid message IDs found.")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm", "Delete selected messages?"):
            return
        
        logger.debug(f"Deleting messages: {message_ids}")
        
        response = self.client.call_with_retry(
            'DeleteMessages',
            pb2.DeleteMessageRequest(
                username=self.username, 
                message_ids=message_ids
            )
        )
        
        if response and response.success:
            # Remove from display
            for item_id in selected_items:
                self.chat_display.delete(item_id)
        else:
            messagebox.showerror(
                "Error", 
                response.message if response else "Failed to delete messages."
            )
        
        # Update status bar
        self.status_var.set(f"Connected to {self.client.current_server}")
    
    def delete_account(self):
        """Delete the current user's account."""
        if not self.username:
            return
        
        # Confirm deletion
        if not messagebox.askyesno(
            "Confirm", 
            "Are you sure you want to delete your account? This cannot be undone."
        ):
            return
        
        logger.debug(f"Deleting account: {self.username}")
        
        response = self.client.call_with_retry(
            'DeleteAccount',
            pb2.Username(username=self.username)
        )
        
        if response and response.success:
            messagebox.showinfo("Success", response.message)
            self.username = None
            self.create_login_widgets()
        else:
            messagebox.showerror(
                "Error", 
                response.message if response else "Failed to delete account."
            )
        
        # Update status bar
        self.status_var.set(f"Connected to {self.client.current_server}")


def main():
    """Main function to parse arguments and start the client."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start a chat client')
    parser.add_argument('--servers', type=str, nargs='+', help='List of server addresses (host:port)')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    args = parser.parse_args()
    
    # Load server list
    server_list = []
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
                server_list = config.get('servers', [])
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            server_list = ["localhost:50051", "localhost:50052", "localhost:50053"]
    elif args.servers:
        server_list = args.servers
    else:
        # Default server list
        server_list = ["localhost:50051", "localhost:50052", "localhost:50053"]
    
    # Start GUI
    root = tk.Tk()
    client = ChatClient(root, server_list)
    root.mainloop()

if __name__ == "__main__":
    main()
