import socket
import threading
import struct
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

HEADER_SIZE = 4

def send_packet(sock, data):
    """Encodes and sends data with a 4-byte length header."""
    encoded_data = data.encode('utf-8')
    packet = struct.pack(f'!I{len(encoded_data)}s', len(encoded_data), encoded_data)
    sock.sendall(packet)

def recv_packet(sock):
    """Receives one packet according to our custom wire protocol."""
    try:
        header = sock.recv(HEADER_SIZE)
        if not header:
            return None
        data_length = struct.unpack('!I', header)[0]
        data = sock.recv(data_length).decode('utf-8')
        return data
    except:
        return None

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

    def clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning('Input Error', 'Username and password required.')
            return
        
        request = f'register|{username}|{password}'
        send_packet(self.sock, request)
        response = recv_packet(self.sock)
        
        if not response:
            messagebox.showerror('Error', 'No response from server.')
            return
        
        parts = response.split('|', 1)  # split only once
        if parts[0] == 'ok':
            # e.g. "ok|Account created successfully."
            msg = parts[1] if len(parts) > 1 else "Registration successful."
            messagebox.showinfo('Success', msg)
        else:
            # e.g. "error|Username already exists."
            msg = parts[1] if len(parts) > 1 else 'Unknown error'
            messagebox.showerror('Error', msg)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning('Input Error', 'Username and password required.')
            return
        
        request = f'login|{username}|{password}'
        send_packet(self.sock, request)
        response = recv_packet(self.sock)
        
        if not response:
            messagebox.showerror('Error', 'No response from server.')
            return
        
        parts = response.split('|')
        if parts and parts[0] == 'ok':
            self.username = username
            
            # If we have a second part, treat it as unread info
            if len(parts) > 1:
                unread_info = parts[1]
            else:
                unread_info = "No additional info."
            
            # You could also parse parts[2:] as individual messages if needed.

            self.create_chat_widgets(unread_info)
            
            # Start the background listener thread
            self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            self.listener_thread.start()
        else:
            error_msg = parts[1] if len(parts) > 1 else 'Unknown error'
            messagebox.showerror('Error', error_msg)

    def create_chat_widgets(self, unread_info=''):
        self.clear_window()
        self.master.title(f'Chat Client - {self.username}')
        
        self.chat_frame = tk.Frame(self.master)
        self.chat_frame.pack(padx=10, pady=10, fill='both', expand=True)

        self.info_label = tk.Label(self.chat_frame, text=unread_info)
        self.info_label.pack()

        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, state='disabled', width=50, height=15)
        self.chat_display.pack(pady=5)

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

        self.refresh_button = tk.Button(self.chat_frame, text='Refresh Messages', command=self.read_messages)
        self.refresh_button.pack(pady=5)

        self.send_frame.columnconfigure(1, weight=1)

    def send_message(self):
        recipient = self.recipient_entry.get().strip()
        message_text = self.message_entry.get().strip()
        if not recipient or not message_text:
            messagebox.showwarning('Input Error', 'Recipient and message required.')
            return
        
        # Build the "send" command
        request = f'send|{self.username}|{recipient}|{message_text}'
        send_packet(self.sock, request)
        response = recv_packet(self.sock)
        if response:
            parts = response.split('|', 1)  # e.g. "ok|Message sent."
            if parts[0] == 'ok':
                self.append_chat(f"Me to {recipient}: {message_text}")
            else:
                error_msg = parts[1] if len(parts) > 1 else 'Unknown error'
                messagebox.showerror('Error', error_msg)
        else:
            messagebox.showerror('Error', 'No response from server.')

    def read_messages(self):
        request = f'read|{self.username}'
        send_packet(self.sock, request)
        response = recv_packet(self.sock)
        if response:
            parts = response.split('|')
            if parts[0] == 'ok':
                # parts[1:] might be "No new messages." or multiple "sender:message"
                if len(parts) > 1:
                    for msg in parts[1:]:
                        self.append_chat(msg)
                else:
                    self.append_chat('No new messages.')
            else:
                error_msg = parts[1] if len(parts) > 1 else 'Unknown error'
                self.append_chat(f'Error reading messages: {error_msg}')
        else:
            self.append_chat('Error: No response from server while reading messages.')

    def listen_for_messages(self):
        """Continuously listen for any 'deliver' or 'server' commands (if implemented)."""
        while True:
            try:
                data = recv_packet(self.sock)
                if not data:
                    break
                parts = data.split('|')
                if parts[0] == 'deliver' and len(parts) >= 3:
                    sender = parts[1]
                    message = parts[2]
                    self.master.after(0, self.append_chat, f"Delivered message from {sender}: {message}")
                elif parts[0] == 'server' and len(parts) >= 2:
                    info = parts[1]
                    self.master.after(0, self.append_chat, f"Server: {info}")
                else:
                    # Ignore or handle other server commands
                    pass
            except Exception as e:
                print(f"Error in listen_for_messages: {e}")
                break

    def append_chat(self, text):
        if self.chat_display and self.chat_display.winfo_exists():
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, text + '\n')
            self.chat_display.yview(tk.END)
            self.chat_display.config(state='disabled')


if __name__ == '__main__':
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
