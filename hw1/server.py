import socket
import threading
import hashlib
import json

import protocol

# Global in-memory storage for accounts and messages
accounts = {}  # username -> hashed_password
pending_messages = {}  # username -> list of messages
logged_in_clients = {}  # username -> client socket

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
            
            if command == 'register':
                user = data.get('username')
                pwd = data.get('password')
                if user in accounts:
                    response = {'status': 'error', 'message': 'Username already exists. Please log in.'}
                else:
                    accounts[user] = pwd
                    pending_messages.setdefault(user, [])
                    response = {'status': 'ok', 'message': 'Account created successfully.'}

            elif command == 'login':
                user = data.get('username')
                pwd = data.get('password')
                if user not in accounts:
                    response = {'status': 'error', 'message': 'Username not found. Please register.'}
                elif accounts[user] != pwd:
                    response = {'status': 'error', 'message': 'Incorrect password.'}
                else:
                    username = user
                    logged_in_clients[user] = client_socket
                    msgs = pending_messages.get(user, [])
                    response = {'status': 'ok', 'message': f'Logged in. You have {len(msgs)} unread messages.'}

            elif command == 'send':
                sender = data.get('sender')
                recipient = data.get('recipient')
                message = data.get('message')
                msg_obj = {'from': sender, 'message': message}
                # Deliver immediately if recipient is logged in
                if recipient in logged_in_clients:
                    try:
                        protocol.send_json(logged_in_clients[recipient], {'command': 'deliver', 'from': sender, 'message': message})
                    except Exception as e:
                        # If delivery fails, store the message
                        pending_messages.setdefault(recipient, []).append(msg_obj)
                else:
                    pending_messages.setdefault(recipient, []).append(msg_obj)
                response = {'status': 'ok', 'message': 'Message sent.'}

            elif command == 'read':
                user = data.get('username')
                msgs = pending_messages.get(user, [])
                response = {'status': 'ok', 'messages': msgs}
                # Clear messages after reading
                pending_messages[user] = []

            else:
                response = {'status': 'error', 'message': 'Unknown command.'}
            
            protocol.send_json(client_socket, response)
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        if username and username in logged_in_clients:
            del logged_in_clients[username]
        client_socket.close()
        print(f"Client disconnected: {addr}")


def start_server():
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
