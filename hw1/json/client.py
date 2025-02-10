import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox, ttk
import protocol as protocol
from protocol import MessageType, StatusCode
import hashlib
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_client")

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title('Chat Client - Login')
        self.master.geometry('600x800')
        
        # Initialize socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            logger.info("Connected to server successfully")
        except Exception as e:
            logger.error(f"Could not connect to server: {e}")
            messagebox.showerror('Connection Error', f'Could not connect to server: {e}')
            self.master.destroy()
            return
            
        self.username = None
        self.create_login_widgets()
        
        # Message handlers for different message types
        self.message_handlers = {
            MessageType.CREATE_ACCOUNT.value: self.handle_create_account_response,
            MessageType.LOGIN.value: self.handle_login_response,
            MessageType.LIST_ACCOUNTS.value: self.handle_list_accounts_response,
            MessageType.SEND_MESSAGE.value: self.handle_send_message_response,
            MessageType.GET_MESSAGES.value: self.handle_get_messages_response,
            MessageType.DELETE_MESSAGES.value: self.handle_delete_messages_response,
            MessageType.DELETE_ACCOUNT.value: self.handle_delete_account_response,
            MessageType.BROADCAST.value: self.handle_broadcast_message,
            MessageType.ERROR.value: self.handle_error_response

        }
        
        # Start listener thread
        self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listener_thread.start()

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

        # Chat display
        chat_display_frame = ttk.LabelFrame(self.chat_frame, text="Messages", padding="5")
        chat_display_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_display_frame, 
            wrap=tk.WORD,
            width=50, 
            height=20
        )
        self.chat_display.pack(fill='both', expand=True)

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
        
        refresh_btn = ttk.Button(button_frame, text='Refresh Messages', command=self.get_messages)
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
            messagebox.showwarning("No User", "You are not logged in with any account.")
            return

        confirm = messagebox.askyesno(
            "Confirm Account Deletion",
            f"Are you sure you want to delete account '{self.username}'?\n"
            "All messages (read or unread) will be permanently removed!"
        )
        if not confirm:
            return

        logger.debug(f"Sending delete account request for user: {self.username}")
        message = protocol.create_message(
            MessageType.DELETE_ACCOUNT,
            {
                "username": self.username
            }
        )
        protocol.send_json(self.sock, message)

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
            
        logger.debug(f"Attempting to register user: {username}")
        message = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": username,
                "password": hash_password(password)
            }
        )
        protocol.send_json(self.sock, message)

    def login(self):
        """Handle user login."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning('Input Error', 'Username and password required.')
            return
            
        logger.debug(f"Attempting to login user: {username}")
        message = protocol.create_message(
            MessageType.LOGIN,
            {
                "username": username,
                "password": hash_password(password)
            }
        )
        protocol.send_json(self.sock, message)

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
        protocol.send_json(self.sock, message)

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
        protocol.send_json(self.sock, message)

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
        protocol.send_json(self.sock, message)

    def delete_selected_messages(self):
        """Delete selected messages."""
        # Implementation depends on how you track message IDs in the UI
        selected_ids = []  # Get these from your UI
        if not selected_ids:
            messagebox.showwarning('Selection Error', 'No messages selected.')
            return
            
        logger.debug(f"Deleting messages: {selected_ids}")
        message = protocol.create_message(
            MessageType.DELETE_MESSAGES,
            {
                "username": self.username,
                "message_ids": selected_ids
            }
        )
        protocol.send_json(self.sock, message)

    def append_chat(self, text: str):
        """Append text to chat display."""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {text}\n")
        self.chat_display.yview(tk.END)
        self.chat_display.config(state='disabled')

    def start_auto_refresh(self):
        """Start automatic refresh of messages and users as backup."""
        def refresh():
            if hasattr(self, 'chat_display'):  # Only refresh if in chat mode
                self.list_accounts()  # Refresh users
                self.get_messages()   # Refresh messages
                self.master.after(30000, refresh)  # Backup refresh every 30 seconds
        
        # Start the first refresh
        self.master.after(0, refresh)

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
            self.create_chat_widgets()
            # Initial data load happens in start_auto_refresh
        else:
            messagebox.showerror('Login Error', message['data'].get('message', 'Login failed'))

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
            if messages:
                for msg in messages:
                    self.append_chat(f"From {msg['sender']}: {msg['content']}")
            else:
                self.append_chat("No new messages.")

    def handle_delete_messages_response(self, message: dict):
        """Handle delete messages response."""
        if message['status'] == StatusCode.SUCCESS.value:
            count = message['data']['deleted_count']
            self.append_chat(f"Successfully deleted {count} messages.")
        else:
            self.append_chat(f"Error deleting messages: {message['data'].get('message')}")
    
    def handle_delete_account_response(self, message: dict):
        """Handle server response to account deletion."""
        if message['status'] == StatusCode.SUCCESS.value:
            deleted_user = message['data'].get('username', 'Unknown')
            messagebox.showinfo("Account Deleted", f"Account '{deleted_user}' has been deleted.")
            
            # Log the client out locally and close the window
            self.sock.close()
            self.master.destroy()
        else:
            # Show the error message from the server
            error_msg = message['data'].get('message', 'Unknown error occurred')
            messagebox.showerror('Delete Account Error', error_msg)


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
            self.chat_display.config(state='normal')
            self.chat_display.delete(1.0, tk.END)
            for msg in messages:
                sender = msg['sender']
                content = msg['content']
                timestamp = msg['timestamp']
                self.chat_display.insert(tk.END, f"{timestamp} - {sender}: {content}\n")
            self.chat_display.yview(tk.END)
            self.chat_display.config(state='disabled')

    def handle_error_response(self, message: dict):
        """Handle error response."""
        error_msg = message['data'].get('message', 'Unknown error occurred')
        logger.error(f"Received error: {error_msg}")
        
        # If we're in chat mode (chat_display exists), append to chat
        if hasattr(self, 'chat_display'):
            self.append_chat(f"Error: {error_msg}")
        else:
            # Otherwise show error dialog
            messagebox.showerror('Error', error_msg)

    def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        while True:
            try:
                message = protocol.recv_json(self.sock)
                if not message:
                    logger.warning("Received empty message from server")
                    continue
                    
                if isinstance(message, str):  # Error occurred
                    logger.error(f"Error receiving message: {message}")
                    continue
                    
                logger.debug(f"Received message: {message}")
                
                # Route message to appropriate handler
                msg_type = message['type']
                handler = self.message_handlers.get(msg_type)
                
                if handler:
                    self.master.after(0, handler, message)
                else:
                    logger.warning(f"No handler for message type: {msg_type}")
                    
            except Exception as e:
                logger.error(f"Error in message listener: {e}")
                break

if __name__ == '__main__':
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
