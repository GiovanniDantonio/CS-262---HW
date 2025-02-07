import socket
import threading
import struct
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

# Custom wire protocol
HEADER_SIZE = 4  # Fixed header size for message length
def send_packet(sock, data):
    encoded_data = data.encode('utf-8')
    packet = struct.pack(f'!I{len(encoded_data)}s', len(encoded_data), encoded_data)
    sock.sendall(packet)

def recv_packet(sock):
    header = sock.recv(HEADER_SIZE)
    if not header:
        return None
    data_length = struct.unpack('!I', header)[0]
    data = sock.recv(data_length).decode('utf-8')
    return data

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
        if response.startswith('ok'):
            messagebox.showinfo('Success', response.split('|')[1])
        else:
            messagebox.showerror('Error', response.split('|')[1])

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning('Input Error', 'Username and password required.')
            return
        request = f'login|{username}|{password}'
        send_packet(self.sock, request)
        response = recv_packet(self.sock)
        parts = response.split('|')
        if parts[0] == 'ok':
            self.username = username
            unread_info = parts[1]
            self.create_chat_widgets(unread_info)
        else:
            messagebox.showerror('Error', parts[1])

    def create_chat_widgets(self, unread_info=''):
      self.clear_window()
      self.master.title(f'Chat Client - {self.username}')

      self.chat_frame = tk.Frame(self.master)
      self.chat_frame.pack(padx=10, pady=10, fill='both', expand=True)

      self.info_label = tk.Label(self.chat_frame, text=unread_info)
      self.info_label.pack()

      # Ensure chat_display is initialized
      self.chat_display = scrolledtext.ScrolledText(self.chat_frame, state='disabled', width=50, height=15)
      self.chat_display.pack(pady=5)

      self.send_frame = tk.Frame(self.chat_frame)
      self.send_frame.pack(fill='x', pady=5)


    def send_message(self):
        recipient = self.recipient_entry.get().strip()
        message_text = self.message_entry.get().strip()
        if not recipient or not message_text:
            messagebox.showwarning('Input Error', 'Recipient and message required.')
            return
        request = f'send|{self.username}|{recipient}|{message_text}'
        send_packet(self.sock, request)
        response = recv_packet(self.sock)
        self.append_chat(response.split('|')[1])

    def append_chat(self, text):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, text + '\n')
        self.chat_display.yview(tk.END)
        self.chat_display.config(state='disabled')
    
    def listen_for_messages(self):
      """Continuously listen for incoming messages from the server."""
      while True:
          try:
              data = recv_packet(self.sock)  # Use the custom wire protocol
              if data:
                  if hasattr(self, 'chat_display'):  # Ensure chat_display exists
                      self.append_chat(f"Server: {data}")
                  else:
                      print(f"Received message but chat display is not initialized: {data}")
          except Exception as e:
              print(f"Error receiving message: {e}")
              break



if __name__ == '__main__':
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
