import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import protocol
import hashlib

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

# Utility function to hash password
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title('Chat Client - Login')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((SERVER_HOST, SERVER_PORT))
        except Exception as e:
            messagebox.showerror('Connection Error', f'Could not connect to server: {e}')
            self.master.destroy()
            return
        self.username = None
        self.create_login_widgets()
        
        # Start a thread to listen for incoming delivered messages
        self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listener_thread.start()

    def create_login_widgets(self):
        self.clear_window()
        self.login_frame = tk.Frame(self.master)
        self.login_frame.pack(padx=10, pady=10)
        
        tk.Label(self.login_frame, text='Username:').grid(row=0, column=0, sticky='e')
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1)
        
        tk.Label(self.login_frame, text='Password:').grid(row=1, column=0, sticky='e')
        self.password_entry = tk.Entry(self.login_frame, show='*')
        self.password_entry.grid(row=1, column=1)
        
        self.register_button = tk.Button(self.login_frame, text='Register', command=self.register)
        self.register_button.grid(row=2, column=0, pady=5)
        
        self.login_button = tk.Button(self.login_frame, text='Login', command=self.login)
        self.login_button.grid(row=2, column=1, pady=5)

    def create_chat_widgets(self, unread_info=''):
        self.clear_window()
        self.master.title(f'Chat Client - {self.username}')
        
        self.chat_frame = tk.Frame(self.master)
        self.chat_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Display unread message info
        self.info_label = tk.Label(self.chat_frame, text=unread_info)
        self.info_label.pack()

        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, state='disabled', width=50, height=15)
        self.chat_display.pack(pady=5)

        # Frame for sending messages
        self.send_frame = tk.Frame(self.chat_frame)
        self.send_frame.pack(fill='x', pady=5)

        tk.Label(self.send_frame, text='Recipient:').grid(row=0, column=0, sticky='e')
        self.recipient_entry = tk.Entry(self.send_frame)
        self.recipient_entry.grid(row=0, column=1, sticky='we')

        tk.Label(self.send_frame, text='Message:').grid(row=1, column=0, sticky='e')
        self.message_entry = tk.Entry(self.send_frame, width=40)
        self.message_entry.grid(row=1, column=1, sticky='we')

        self.send_button = tk.Button(self.send_frame, text='Send', command=self.send_message)
        self.send_button.grid(row=0, column=2, rowspan=2, padx=5)

        # Refresh button to read messages
        self.refresh_button = tk.Button(self.chat_frame, text='Refresh Messages', command=self.read_messages)
        self.refresh_button.pack(pady=5)

        self.send_frame.columnconfigure(1, weight=1)

    def clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning('Input Error', 'Username and password required.')
            return
        hashed = hash_password(password)
        request = {'command': 'register', 'username': username, 'password': hashed}
        protocol.send_json(self.sock, request)
        response = protocol.recv_json(self.sock)
        if response and response.get('status') == 'ok':
            messagebox.showinfo('Success', response.get('message'))
        else:
            messagebox.showerror('Error', response.get('message') if response else 'No response')

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning('Input Error', 'Username and password required.')
            return
        hashed = hash_password(password)
        request = {'command': 'login', 'username': username, 'password': hashed}
        protocol.send_json(self.sock, request)
        response = protocol.recv_json(self.sock)
        if response and response.get('status') == 'ok':
            self.username = username
            unread = response.get('message', '')
            self.create_chat_widgets(unread)
        else:
            messagebox.showerror('Error', response.get('message') if response else 'No response')

    def send_message(self):
        recipient = self.recipient_entry.get().strip()
        message_text = self.message_entry.get().strip()
        if not recipient or not message_text:
            messagebox.showwarning('Input Error', 'Recipient and message required.')
            return
        request = {
            'command': 'send',
            'sender': self.username,
            'recipient': recipient,
            'message': message_text
        }
        protocol.send_json(self.sock, request)
        response = protocol.recv_json(self.sock)
        if response and response.get('status') == 'ok':
            self.append_chat(f'Message sent to {recipient}')
            self.message_entry.delete(0, tk.END)
        else:
            self.append_chat(f'Error: {response.get("message") if response else "No response"}')

    def read_messages(self):
        request = {'command': 'read', 'username': self.username}
        protocol.send_json(self.sock, request)
        response = protocol.recv_json(self.sock)
        if response and response.get('status') == 'ok':
            messages = response.get('messages', [])
            if messages:
                for msg in messages:
                    self.append_chat(f"From {msg.get('from')}: {msg.get('message')}")
            else:
                self.append_chat('No new messages.')
        else:
            self.append_chat('Error reading messages.')

    def append_chat(self, text):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, text + '\n')
        self.chat_display.yview(tk.END)
        self.chat_display.config(state='disabled')

    def listen_for_messages(self):
        # Continuously listen for any delivered messages from the server
        while True:
            try:
                data = protocol.recv_json(self.sock)
                if data and data.get('command') == 'deliver':
                    sender = data.get('from')
                    message = data.get('message')
                    self.append_chat(f"Delivered message from {sender}: {message}")
            except Exception as e:
                break

if __name__ == '__main__':
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
