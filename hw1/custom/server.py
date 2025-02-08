import socket
import sqlite3
import threading
import struct

# Permanent Database Setup
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    message TEXT NOT NULL,
                    delivered INTEGER DEFAULT 0
                 )''')
    conn.commit()
    conn.close()

PORT = 12345
HOST = '0.0.0.0'  # Listen on all interfaces

# Custom wire protocol
HEADER_SIZE = 4  # Fixed header size for message length

def send_packet(sock, data):
    """Send a packet with a 4-byte big-endian length header plus data."""
    encoded_data = data.encode('utf-8')
    packet = struct.pack(f'!I{len(encoded_data)}s', len(encoded_data), encoded_data)
    sock.sendall(packet)

def recv_packet(sock):
    """Receive a single packet according to our wire protocol."""
    try:
        header = sock.recv(HEADER_SIZE)
        if not header:
            print("Client disconnected.")
            return None
        data_length = struct.unpack('!I', header)[0]
        data = sock.recv(data_length).decode('utf-8')
        return data
    except Exception as e:
        print(f"Error receiving packet: {e}")
        return None

def handle_client(client_socket, addr):
    print(f"[+] Client connected: {addr}")
    try:
        while True:
            data = recv_packet(client_socket)
            if not data:
                # Client disconnected or error
                break

            parts = data.split('|')
            command = parts[0] if parts else ''
            response = ""
            
            # Database connection
            conn = sqlite3.connect('chat.db')
            c = conn.cursor()
            
            try:
                if command == 'register':
                    # Expected format: register|username|password
                    if len(parts) < 3:
                        response = "error|Invalid register syntax."
                    else:
                        user, pwd = parts[1], parts[2]
                        c.execute("SELECT username FROM accounts WHERE username = ?", (user,))
                        if c.fetchone():
                            response = "error|Username already exists. Please log in."
                        else:
                            c.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", (user, pwd))
                            conn.commit()
                            # Return at least two parts
                            response = "ok|Account created successfully."

                elif command == 'login':
                    # Expected format: login|username|password
                    if len(parts) < 3:
                        response = "error|Invalid login syntax."
                    else:
                        user, pwd = parts[1], parts[2]
                        c.execute("SELECT password FROM accounts WHERE username = ?", (user,))
                        record = c.fetchone()
                        if not record:
                            response = "error|Username not found. Please register."
                        elif record[0] != pwd:
                            response = "error|Incorrect password."
                        else:
                            # User logged in
                            c.execute("SELECT sender, message FROM messages WHERE recipient = ? AND delivered = 0", (user,))
                            msgs = [f"{row[0]}:{row[1]}" for row in c.fetchall()]
                            unread_count = len(msgs)
                            # Return at least two parts:
                            #   parts[0] = "ok"
                            #   parts[1] = "You have X unread messages."
                            #   parts[2..n] = each "sender:message"
                            response = f"ok|You have {unread_count} unread messages.|" + "|".join(msgs)
                            # Mark them as delivered
                            c.execute("UPDATE messages SET delivered = 1 WHERE recipient = ?", (user,))
                            conn.commit()

                elif command == 'send':
                    # Expected format: send|sender|recipient|message
                    if len(parts) < 4:
                        response = "error|Invalid send syntax."
                    else:
                        sender = parts[1]
                        recipient = parts[2]
                        # Rejoin the rest as the message (allows '|' inside the message text)
                        message = "|".join(parts[3:])
                        c.execute("INSERT INTO messages (sender, recipient, message, delivered) VALUES (?, ?, ?, 0)",
                                  (sender, recipient, message))
                        conn.commit()
                        response = "ok|Message sent."

                elif command == 'read':
                    # Expected format: read|username
                    if len(parts) < 2:
                        response = "error|Invalid read syntax."
                    else:
                        user = parts[1]
                        c.execute("SELECT sender, message FROM messages WHERE recipient = ? AND delivered = 0", (user,))
                        rows = c.fetchall()
                        if rows:
                            msgs = [f"{row[0]}:{row[1]}" for row in rows]
                            response = f"ok|{'|'.join(msgs)}"
                        else:
                            # Return at least 2 parts so the client can parse
                            response = "ok|No new messages."
                        # Mark delivered
                        c.execute("UPDATE messages SET delivered = 1 WHERE recipient = ?", (user,))
                        conn.commit()

                else:
                    response = "error|Unknown command."

            except Exception as e:
                response = f"error|Server error: {e}"

            finally:
                conn.close()
                # Always send a response back to client
                send_packet(client_socket, response)

    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        client_socket.close()
        print(f"[-] Client disconnected: {addr}")

def start_server():
    init_db()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[*] Server listening on {HOST}:{PORT}")
    
    try:
        while True:
            client_socket, addr = server_socket.accept()
            t = threading.Thread(target=handle_client, args=(client_socket, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()

if __name__ == '__main__':
    start_server()
