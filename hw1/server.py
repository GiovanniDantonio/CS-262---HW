import socket
import sqlite3
import threading
import hashlib
import json
import protocol

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
HOST = '0.0.0.0'

# Utility function to hash a password using sha256
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def handle_client(client_socket, addr):
    print(f"Client connected: {addr}")
    username = None
    try:
        while True:
            data = protocol.recv_json(client_socket)
            if not data:
                break
            command = data.get('command')
            response = {}
            conn = sqlite3.connect('chat.db')
            c = conn.cursor()
            
            if command == 'register':
                user = data.get('username')
                pwd = hash_password(data.get('password'))
                c.execute("SELECT username FROM accounts WHERE username = ?", (user,))
                if c.fetchone():
                    response = {'status': 'error', 'message': 'Username already exists. Please log in.'}
                else:
                    c.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", (user, pwd))
                    conn.commit()
                    response = {'status': 'ok', 'message': 'Account created successfully.'}

            elif command == 'login':
                user = data.get('username')
                pwd = hash_password(data.get('password'))
                c.execute("SELECT password FROM accounts WHERE username = ?", (user,))
                record = c.fetchone()
                if not record:
                    response = {'status': 'error', 'message': 'Username not found. Please register.'}
                elif record[0] != pwd:
                    response = {'status': 'error', 'message': 'Incorrect password.'}
                else:
                    username = user
                    c.execute("SELECT sender, message FROM messages WHERE recipient = ? AND delivered = 0", (user,))
                    msgs = [{'from': row[0], 'message': row[1]} for row in c.fetchall()]
                    response = {'status': 'ok', 'message': f'Logged in. You have {len(msgs)} unread messages.', 'messages': msgs}
                    c.execute("UPDATE messages SET delivered = 1 WHERE recipient = ?", (user,))
                    conn.commit()

            elif command == 'send':
                sender = data.get('sender')
                recipient = data.get('recipient')
                message = data.get('message')
                c.execute("INSERT INTO messages (sender, recipient, message, delivered) VALUES (?, ?, ?, 0)", (sender, recipient, message))
                conn.commit()
                response = {'status': 'ok', 'message': 'Message sent.'}

            elif command == 'read':
                user = data.get('username')
                c.execute("SELECT sender, message FROM messages WHERE recipient = ? AND delivered = 0", (user,))
                msgs = [{'from': row[0], 'message': row[1]} for row in c.fetchall()]
                response = {'status': 'ok', 'messages': msgs}
                c.execute("UPDATE messages SET delivered = 1 WHERE recipient = ?", (user,))
                conn.commit()

            else:
                response = {'status': 'error', 'message': 'Unknown command.'}
            conn.close()
            protocol.send_json(client_socket, response)
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        client_socket.close()
        print(f"Client disconnected: {addr}")


def start_server():
    init_db()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    
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
