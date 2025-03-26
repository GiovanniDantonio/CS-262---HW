import grpc
import chat_pb2
import chat_pb2_grpc
import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import logging
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("chat_client")

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client - Login")
        self.master.geometry("600x800")
        self.username = None

        # gRPC channel and stub (using client_config.json host/port if desired)
        self.channel = grpc.insecure_channel("localhost:50051")
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)

        self.stop_event = threading.Event()
        self.listener_thread = None

        # Build login UI; do not start listener yet
        self.create_login_widgets()

    def clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    # --- UI Creation ---
    def create_login_widgets(self):
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

    def create_chat_widgets(self):
        self.clear_window()
        self.master.title(f"Chat Client - {self.username}")
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
        self.chat_display = ttk.Treeview(chat_display_frame, 
                                         columns=("timestamp", "sender", "content"), 
                                         show="headings", selectmode="extended")
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
        refresh_btn = ttk.Button(button_frame, text="Refresh Messages",
                                 command=lambda: self.get_messages(int(self.message_limit.get())))
        refresh_btn.pack(side=tk.LEFT, padx=5)
        delete_btn = ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected_messages)
        delete_btn.pack(side=tk.LEFT, padx=5)
        delete_account_btn = ttk.Button(button_frame, text="Delete Account", command=self.delete_account)
        delete_account_btn.pack(side=tk.LEFT, padx=5)

        self.start_auto_refresh()

    # --- gRPC Methods ---
    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Error", "Username and password required.")
            return
        logger.debug(f"Registering user: {username}")
        try:
            response = self.stub.Register(chat_pb2.UserCredentials(
                username=username,
                password=hash_password(password)
            ))
            if response.success:
                messagebox.showinfo("Success", "Account created successfully!")
            else:
                messagebox.showerror("Error", response.message)
        except grpc.RpcError as e:
            logger.error(f"gRPC error during registration: {e}")
            messagebox.showerror("Error", str(e))

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Error", "Username and password required.")
            return
        logger.debug(f"Logging in user: {username}")
        try:
            response = self.stub.Login(chat_pb2.UserCredentials(
                username=username,
                password=hash_password(password)
            ))
            if response.success:
                self.username = username
                messagebox.showinfo("Success", f"Login successful! You have {response.unread_count} unread messages.")
                self.create_chat_widgets()
                # Start the broadcast listener now that the user is logged in.
                self.start_listener()
            else:
                messagebox.showerror("Login Error", response.message)
        except grpc.RpcError as e:
            logger.error(f"gRPC error during login: {e}")
            messagebox.showerror("Error", str(e))

    def list_accounts(self, pattern="%"):
        logger.debug(f"Requesting account list with pattern: {pattern}")
        try:
            response = self.stub.ListAccounts(chat_pb2.AccountListRequest(
                pattern=pattern, page=1, per_page=50
            ))
            self.user_listbox.delete(0, tk.END)
            for account in response.accounts:
                self.user_listbox.insert(tk.END, account.username)
        except grpc.RpcError as e:
            logger.error(f"gRPC error during list_accounts: {e}")
            messagebox.showerror("Error", str(e))

    def send_message(self):
        recipient = self.recipient_entry.get().strip()
        content = self.message_entry.get().strip()
        if not recipient or not content:
            messagebox.showwarning("Input Error", "Recipient and message required.")
            return
        logger.debug(f"Sending message from {self.username} to {recipient}")
        try:
            response = self.stub.SendMessage(chat_pb2.Message(
                sender=self.username, recipient=recipient, content=content
            ))
            if response.success:
                self.message_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", response.message)
        except grpc.RpcError as e:
            logger.error(f"gRPC error during send_message: {e}")
            messagebox.showerror("Error", str(e))

    def get_messages(self, count=10):
        logger.debug(f"Requesting messages for {self.username}")
        try:
            response = self.stub.GetMessages(chat_pb2.MessageRequest(
                username=self.username, count=count
            ))
            # Clear existing messages in the Treeview
            for item in self.chat_display.get_children():
                self.chat_display.delete(item)
            for msg in response.messages:
                item_id = str(msg.id)
                self.chat_display.insert("", "end", iid=item_id,
                                          values=(msg.timestamp, msg.sender, msg.content))
                if not msg.read:
                    self.chat_display.item(item_id, tags=("unread",))
        except grpc.RpcError as e:
            logger.error(f"gRPC error during get_messages: {e}")
            messagebox.showerror("Error", str(e))

    def delete_selected_messages(self):
        selected_items = self.chat_display.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select messages to delete.")
            return
            
        try:
            # Convert selected item IDs to integers
            message_ids = [int(item) for item in selected_items]
            
            # Call DeleteMessages RPC
            response = self.stub.DeleteMessages(chat_pb2.DeleteMessagesRequest(
                username=self.username,
                message_ids=message_ids
            ))
            
            if response.success:
                # Remove deleted messages from display
                for item in selected_items:
                    self.chat_display.delete(item)
                messagebox.showinfo("Success", "Messages deleted successfully")
            else:
                messagebox.showerror("Error", response.message)
                
        except grpc.RpcError as e:
            logger.error(f"gRPC error during delete_messages: {e}")
            messagebox.showerror("Error", str(e))
        except ValueError as e:
            logger.error(f"Error converting message IDs: {e}")
            messagebox.showerror("Error", "Invalid message IDs")

    def delete_account(self):
        if not self.username:
            messagebox.showinfo("No user logged in", "You are not currently logged in.")
            return
        try:
            response = self.stub.GetMessages(chat_pb2.MessageRequest(
                username=self.username, count=1000
            ))
            unread_count = sum(1 for msg in response.messages if not msg.read)
            warning_msg = "Are you sure you want to delete your account?"
            if unread_count > 0:
                warning_msg += f"\n\nWARNING: You have {unread_count} unread message(s) that will be permanently deleted!"
            if messagebox.askyesno("Confirm Account Deletion", warning_msg):
                del_response = self.stub.DeleteAccount(chat_pb2.UserRequest(username=self.username))
                if del_response.success:
                    self.stop_auto_refresh()
                    self.username = None
                    self.clear_window()
                    self.create_login_widgets()
                    messagebox.showinfo("Success", "Account deleted successfully")
                else:
                    messagebox.showerror("Error", del_response.message)
        except grpc.RpcError as e:
            logger.error(f"gRPC error during delete_account: {e}")
            messagebox.showerror("Error", str(e))

    def logout(self):
        if not self.username:
            messagebox.showinfo("No user logged in", "You are not currently logged in.")
            return
        try:
            response = self.stub.Logout(chat_pb2.UserRequest(username=self.username))
            if response.success:
                messagebox.showinfo("Success", "Logged out successfully")
                self.stop_auto_refresh()
                self.username = None
                self.clear_window()
                self.create_login_widgets()
            else:
                messagebox.showerror("Logout Error", response.message)
        except grpc.RpcError as e:
            logger.error(f"gRPC error during logout: {e}")
            messagebox.showerror("Error", str(e))

    def start_auto_refresh(self):
        self._refresh_after_id = None
        def refresh():
            if self.username:
                self.get_messages(int(self.message_limit.get()))
                self.list_accounts()
                self._refresh_after_id = self.master.after(3000, refresh)
        refresh()

    def stop_auto_refresh(self):
        if hasattr(self, "_refresh_after_id") and self._refresh_after_id:
            self.master.after_cancel(self._refresh_after_id)
            self._refresh_after_id = None

    def append_chat(self, text: str):
        logger.info(text)

    def on_message_click(self, event):
        item = self.chat_display.identify_row(event.y)
        if item and "unread" in self.chat_display.item(item, "tags"):
            # Remove the 'unread' tag from the clicked message
            self.chat_display.item(item, tags=())
            # Call MarkAsRead RPC for this message
            try:
                response = self.stub.MarkAsRead(chat_pb2.MarkAsReadRequest(
                    username=self.username,
                    message_ids=[int(item)]
                ))
                if response.success:
                    logger.debug(f"Marked message {item} as read.")
                else:
                    logger.error(f"Failed to mark message {item} as read: {response.message}")
            except grpc.RpcError as e:
                logger.error(f"gRPC error during MarkAsRead: {e}")

    # --- Automatic Broadcast Listener (gRPC Streaming) ---
    def listen_for_messages(self):
        try:
            # Use the current username once logged in; if not logged in, use empty string.
            req_username = self.username if self.username else ""
            for broadcast in self.stub.StreamMessages(chat_pb2.UserRequest(username=req_username)):
                logger.debug(f"Broadcast message received: {broadcast}")
                self.master.after(0, self.process_broadcast_message, broadcast)
        except grpc.RpcError as e:
            logger.error(f"gRPC stream error: {e}")

    def process_broadcast_message(self, msg):
        if self.username and msg.recipient == self.username:
            item_id = str(msg.id)
            try:
                if self.chat_display.exists(item_id):
                    # Update the item if it already exists
                    self.chat_display.item(item_id,
                                          values=(msg.timestamp, msg.sender, msg.content),
                                          tags=("unread",))
                else:
                    self.chat_display.insert("", "end", iid=item_id,
                                              values=(msg.timestamp, msg.sender, msg.content),
                                              tags=("unread",))
                # Safely scroll to the bottom
                children = self.chat_display.get_children()
                if children:
                    self.chat_display.see(children[-1])
            except Exception as e:
                logger.error(f"Error processing broadcast message for item {item_id}: {e}")



    def start_listener(self):
        self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listener_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
