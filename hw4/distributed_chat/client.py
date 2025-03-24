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
        
        # Connect to initial server
        self._connect_to_server(self.current_server)
    
    def _connect_to_server(self, server_addr):
        """
        Connect to a specific server.
        
        Args:
            server_addr: Server address in format "host:port"
            
        Returns:
            bool: True if connection successful
        """
        with self.lock:
            try:
                if self.channel:
                    self.channel.close()
                
                logger.info(f"Connecting to server at {server_addr}")
                self.channel = grpc.insecure_channel(server_addr)
                self.stub = pb2_grpc.ChatServiceStub(self.channel)
                self.current_server = server_addr
                return True
            except Exception as e:
                logger.error(f"Failed to connect to {server_addr}: {e}")
                return False
    
    def _try_next_server(self):
        """
        Try to connect to the next server in the list.
        
        Returns:
            bool: True if connection successful
        """
        with self.lock:
            # If we have leader info, try that first
            if 'leader-addr' in self.leader_info:
                leader_addr = self.leader_info['leader-addr']
                if self._connect_to_server(leader_addr):
                    return True
            
            # Try other servers in order
            current_idx = self.server_list.index(self.current_server) if self.current_server in self.server_list else -1
            for i in range(1, len(self.server_list) + 1):
                idx = (current_idx + i) % len(self.server_list)
                if self._connect_to_server(self.server_list[idx]):
                    return True
            
            return False
    
    def _handle_error(self, e, retry_count=3):
        """
        Handle errors by possibly reconnecting to a different server.
        
        Args:
            e: Exception that occurred
            retry_count: Number of retries remaining
            
        Returns:
            bool: True if should retry the operation
        """
        if retry_count <= 0:
            return False
        
        # Check for metadata about leader
        if hasattr(e, 'trailing_metadata'):
            self.leader_info = {}
            for key, value in e.trailing_metadata():
                self.leader_info[key] = value
        
        # Try to reconnect
        if self._try_next_server():
            logger.info(f"Reconnected to server at {self.current_server}")
            return True
        
        return False
    
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
                        if self._handle_error(Exception("Not leader"), retry_count - attempt - 1):
                            continue
                    
                    return response
                
                except grpc.RpcError as e:
                    logger.warning(f"RPC error during {method_name}: {e}")
                    if self._handle_error(e, retry_count - attempt - 1):
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
                self._handle_error(e)
            
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
        
        response = self.client.call_with_retry(
            'Register',
            pb2.UserCredentials(
                username=username,
                password=hash_password(password)
            )
        )
        
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
