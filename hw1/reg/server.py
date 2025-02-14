import socket
import sqlite3
import threading
import hashlib
import json
import logging
from datetime import datetime
import protocol as protocol
from protocol import MessageType, StatusCode
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load Configuration File from the same directory as server.py
CONFIG_FILE = os.path.join(BASE_DIR, "server_config.json")

# Load in Configuration File
# CONFIG_FILE = "server_config.json"
default_config = {
    "host": "0.0.0.0",
    "port": 12345,
    "db_path": "chat.db"
}
if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        user_config = json.load(f)
    # Merge user_config with default_config
    config = {**default_config, **user_config}
else:
    logger.warning(f"No config file found at {CONFIG_FILE}. Using defaults.")
    config = default_config

HOST = config["host"]
PORT = config["port"]
DB_PATH = config["db_path"]

# Global variables
server_socket = None
db_conn = None
cursor = None
# Dictionary to store active client connections: {username: (conn, last_broadcast_time)}
active_clients = {}

def init_db():
    """Initialize the SQLite database with required tables."""
    logger.info("Initializing database...")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                 )''')
        # unread is 0, read is 1
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read INTEGER DEFAULT 0,
                    FOREIGN KEY (sender) REFERENCES accounts(username),
                    FOREIGN KEY (recipient) REFERENCES accounts(username)
                 )''')
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()

def migrate_database():
    """Migrate database to latest schema."""
    logger.info("Checking database schema...")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if read column exists in messages table
        c.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'read' not in columns:
            logger.info("Adding 'read' column to messages table...")
            c.execute("ALTER TABLE messages ADD COLUMN read INTEGER DEFAULT 0")
            conn.commit()
            logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise
    finally:
        conn.close()

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def broadcast_updates():
    """Broadcast updates to all connected clients."""
    while True:
        try:
            time.sleep(5)  # Broadcast every 5 seconds
            with threading.Lock():
                # Get all online users
                online_users = list(active_clients.keys())
                
                # Create broadcast message
                for username, (conn, _) in active_clients.items():
                    try:
                        # Send user list update
                        users_msg = protocol.create_message(
                            MessageType.BROADCAST,
                            {
                                "type": "users",
                                "users": online_users
                            }
                        )
                        protocol.send_json(conn, users_msg)
                        
                        # Send messages update
                        cursor.execute("""
                            SELECT m.id, m.sender, m.recipient, m.content, m.timestamp
                            FROM messages m
                            WHERE m.recipient = ?
                            ORDER BY m.timestamp DESC
                            LIMIT 50
                        """, (username,))
                        messages = cursor.fetchall()
                        
                        messages_list = [
                            {
                                "id": msg[0],
                                "sender": msg[1],
                                "recipient": msg[2],
                                "content": msg[3],
                                "timestamp": msg[4]
                            }
                            for msg in messages
                        ]
                        
                        msg_msg = protocol.create_message(
                            MessageType.BROADCAST,
                            {
                                "type": "messages",
                                "messages": messages_list
                            }
                        )
                        protocol.send_json(conn, msg_msg)
                        
                    except Exception as e:
                        logger.error(f"Error broadcasting to {username}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in broadcast thread: {e}")

def broadcast_to_user(username: str):
    """Send updates to a specific user."""
    if username not in active_clients:
        return
        
    user_socket = active_clients[username][0]
    try:
        # Send messages update
        cursor.execute("""
            SELECT m.id, m.sender, m.recipient, m.content, m.timestamp
            FROM messages m
            WHERE m.recipient = ?
            ORDER BY m.timestamp DESC
            LIMIT 50
        """, (username,))
        messages = cursor.fetchall()
        
        messages_list = [
            {
                "id": msg[0],
                "sender": msg[1],
                "recipient": msg[2],
                "content": msg[3],
                "timestamp": msg[4]
            }
            for msg in messages
        ]
        
        msg_msg = protocol.create_message(
            MessageType.BROADCAST,
            {
                "type": "messages",
                "messages": messages_list
            }
        )
        protocol.send_json(user_socket, msg_msg)
        
        # Send online users update
        users_msg = protocol.create_message(
            MessageType.BROADCAST,
            {
                "type": "users",
                "users": list(active_clients.keys())
            }
        )
        protocol.send_json(user_socket, users_msg)
        
    except Exception as e:
        logger.error(f"Error broadcasting to {username}: {e}")
        del active_clients[username]

def handle_create_account(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle account creation request."""
    logger.debug(f"Handling create account request: {data}")
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return protocol.create_error("Username and password required")
    
    c.execute("SELECT username FROM accounts WHERE username = ?", (username,))
    if c.fetchone():
        return protocol.create_error("Username already exists")
    
    hashed_pwd = hash_password(password)
    try:
        c.execute(
            "INSERT INTO accounts (username, password, created_at) VALUES (?, ?, ?)",
            (username, hashed_pwd, datetime.utcnow())
        )
        return protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {"username": username},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Account creation failed: {e}")
        return protocol.create_error("Account creation failed")

def handle_login(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle login request."""
    logger.debug(f"Handling login request: {data}")
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return protocol.create_error("Username and password required")
    
    c.execute("SELECT password FROM accounts WHERE username = ?", (username,))
    record = c.fetchone()
    
    if not record:
        return protocol.create_error("Username not found")
    
    if record[0] != hash_password(password):
        return protocol.create_error("Incorrect password")
    
    # Update last login
    c.execute(
        "UPDATE accounts SET last_login = ? WHERE username = ?",
        (datetime.utcnow(), username)
    )
    
    # Get unread message count
    c.execute(
        "SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0",
        (username,)
    )
    unread_count = c.fetchone()[0]
    
    return protocol.create_message(
        MessageType.LOGIN,
        {
            "username": username,
            "unread_count": unread_count
        },
        StatusCode.SUCCESS
    )

def handle_logout(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle user logout request."""
    logger.debug(f"Handling logout request: {data}")
    username = data.get('username')

    if not username:
        return protocol.create_error("Username is required to logout.")

    # If the user is in active_clients, remove them
    if username in active_clients:
        del active_clients[username]
        logger.info(f"User '{username}' has been logged out successfully.")
        return protocol.create_message(
            MessageType.LOGOUT,
            {},
            StatusCode.SUCCESS
        )
    else:
        return protocol.create_error("User not currently logged in or not found in active list.")

def handle_delete_account(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle account deletion request."""
    logger.debug(f"Handling delete account request: {data}")
    username = data.get('username')
    
    if not username:
        return protocol.create_error("Username is required to delete an account.")
    
    # Check if user exists
    c.execute("SELECT username FROM accounts WHERE username = ?", (username,))
    record = c.fetchone()
    if not record:
        return protocol.create_error("User not found.")

    # Get unread message count
    c.execute(
        "SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0",
        (username,)
    )
    unread_count = c.fetchone()[0]

    try:
        c.execute(
            "DELETE FROM messages WHERE sender = ? OR recipient = ?",
            (username, username)
        )
        c.execute(
            "DELETE FROM accounts WHERE username = ?",
            (username,)
        )
        c.connection.commit()
        
        # If the user is currently active, remove them
        if username in active_clients:
            del active_clients[username]
        
        return protocol.create_message(
            MessageType.DELETE_ACCOUNT,
            {
                "username": username,
                "unread_count": unread_count
            },
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to delete account for {username}: {e}")
        return protocol.create_error("Failed to delete account.")

def handle_list_accounts(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle account listing request."""
    logger.debug(f"Handling list accounts request: {data}")
    pattern = data.get('pattern', '%')
    page = data.get('page', 1)
    per_page = data.get('per_page', 10)
    
    offset = (page - 1) * per_page
    
    c.execute(
        """SELECT username, created_at, last_login 
           FROM accounts 
           WHERE username LIKE ? 
           ORDER BY username 
           LIMIT ? OFFSET ?""",
        (pattern, per_page, offset)
    )
    
    accounts = [{
        "username": row[0],
        "created_at": row[1],
        "last_login": row[2]
    } for row in c.fetchall()]
    
    return protocol.create_message(
        MessageType.LIST_ACCOUNTS,
        {
            "accounts": accounts,
            "page": page,
            "per_page": per_page
        },
        StatusCode.SUCCESS
    )

def handle_send_message(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle message sending request."""
    logger.debug(f"Handling send message request: {data}")
    username = data.get('username')
    recipient = data.get('recipient')
    content = data.get('content')
    
    if not all([username, recipient, content]):
        return protocol.create_error("Username, recipient, and content are required")
    
    # Check if recipient exists
    c.execute("SELECT username FROM accounts WHERE username = ?", (recipient,))
    if not c.fetchone():
        return protocol.create_error("Recipient not found")
    
    try:
        # Insert message with read status as NULL (unread)
        c.execute(
            """INSERT INTO messages (sender, recipient, content, read) 
               VALUES (?, ?, ?, ?)""",
            (username, recipient, content, 0)
        )
        message_id = c.lastrowid
        
        # Verify message was inserted
        c.execute("SELECT timestamp, read FROM messages WHERE id = ?", (message_id,))
        result = c.fetchone()
        if not result:
            raise Exception("Message insertion failed - no message ID returned")
        
        timestamp, read_status = result
        
        # Commit the transaction
        c.connection.commit()
        
        # Broadcast updates to both sender and recipient
        try:
            broadcast_to_user(username)  # Sender sees their sent message
            broadcast_to_user(recipient)  # Recipient gets notification
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            # Don't return error since message was saved successfully
        
        return protocol.create_message(
            MessageType.SEND_MESSAGE,
            {
                "id": message_id,
                "timestamp": timestamp,
                "read": read_status
            },
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to send message. Error: {str(e)}")
        return protocol.create_error(f"Failed to send message: {str(e)}")

def handle_get_messages(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle message retrieval request."""
    logger.debug(f"Handling get messages request: {data}")
    username = data.get('username')
    count = data.get('count', 10)  # Default to 10 messages
    
    if not username:
        return protocol.create_error("Username required")
    
    try:
        # Get messages where user is recipient
        c.execute(
            """SELECT id, sender, content, timestamp,
                      CASE
                          WHEN read IS 0 THEN 0
                          ELSE read
                      END as read_status
               FROM messages 
               WHERE recipient = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (username, count)
        )
        
        messages = []
        for row in c.fetchall():
            messages.append({
                'id': row[0],
                'sender': row[1],
                'content': row[2],
                'timestamp': row[3],
                'read': row[4]  # This will be 0 for NULL (unread) or 1 for read
            })
        
        return protocol.create_message(
            MessageType.GET_MESSAGES,
            {"messages": messages},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to get messages. Error: {str(e)}")
        return protocol.create_error(f"Failed to get messages: {str(e)}")

def handle_delete_messages(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle message deletion request."""
    logger.debug(f"Handling delete messages request: {data}")
    username = data.get('username')
    message_ids = data.get('message_ids', [])
    
    if not username or not message_ids:
        return protocol.create_error("Username and message IDs required")
    
    try:
        # Only delete messages where the user is either sender or recipient
        placeholders = ','.join('?' * len(message_ids))
        c.execute(
            f"""DELETE FROM messages 
                WHERE id IN ({placeholders})
                AND (sender = ? OR recipient = ?)""",
            (*message_ids, username, username)
        )
        
        deleted_count = c.rowcount
        if deleted_count > 0:
            logger.info(f"Permanently deleted {deleted_count} messages")
        
        return protocol.create_message(
            MessageType.DELETE_MESSAGES,
            {"deleted_count": deleted_count},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to delete messages: {e}")
        return protocol.create_error("Failed to delete messages")

def handle_mark_as_read(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle marking messages as read."""
    logger.debug(f"Handling mark as read request: {data}")
    username = data.get('username')
    message_ids = data.get('message_ids', [])
    
    if not username or not message_ids:
        return protocol.create_error("Username and message IDs required")
    
    try:
        # Only mark messages as read if user is the recipient
        placeholders = ','.join('?' * len(message_ids))
        c.execute(
            f"""UPDATE messages 
                SET read = 1 
                WHERE id IN ({placeholders})
                AND recipient = ?""",
            (*message_ids, username)
        )
        
        # Commit the changes
        c.connection.commit()
        
        return protocol.create_message(
            MessageType.MARK_AS_READ,
            {"marked_count": c.rowcount},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to mark messages as read: {e}")
        return protocol.create_error("Failed to mark messages as read")

def handle_client(client_socket: socket.socket, addr: tuple):
    """Handle client connection and route messages to appropriate handlers."""
    logger.info(f"New client connected: {addr}")
    client_username = None
    try:
        while True:
            message = protocol.recv_json(client_socket)
            if not message:
                break
            # Error occurred
            if isinstance(message, str):
                logger.error(f"Error receiving message: {message}")
                continue
                
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            try:
                msg_type = MessageType(message['type'])
                data = message['data']
                
                # Route message to appropriate handler
                handler_map = {
                    MessageType.CREATE_ACCOUNT: handle_create_account,
                    MessageType.LOGIN: handle_login,
                    MessageType.LIST_ACCOUNTS: handle_list_accounts,
                    MessageType.SEND_MESSAGE: handle_send_message,
                    MessageType.GET_MESSAGES: handle_get_messages,
                    MessageType.DELETE_MESSAGES: handle_delete_messages,
                    MessageType.DELETE_ACCOUNT: handle_delete_account,
                    MessageType.LOGOUT: handle_logout,
                    MessageType.MARK_AS_READ: handle_mark_as_read
                }
                
                handler = handler_map.get(msg_type)
                if handler:
                    response = handler(data, c)
                    conn.commit()
                else:
                    response = protocol.create_error(f"Unsupported message type: {msg_type}")
                
                protocol.send_json(client_socket, response)
                
                # Track username after successful login
                if message['type'] == MessageType.LOGIN.value and message['status'] == StatusCode.SUCCESS.value:
                    username = data['username']
                    client_username = username
                    
                    # Store the actual TCP socket plus timestamp
                    active_clients[username] = (client_socket, time.time())
                    
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                protocol.send_json(client_socket, protocol.create_error(str(e)))
                conn.rollback()
            finally:
                conn.close()
                
    except Exception as e:
        logger.error(f"Client connection error: {e}")
    finally:
        if client_username and client_username in active_clients:
            del active_clients[client_username]
        client_socket.close()
        logger.info(f"Client disconnected: {addr}")

def start_server():
    """Start the chat server."""
    global server_socket, db_conn, cursor
    
    # Initialize database
    db_conn = sqlite3.connect(DB_PATH)
    cursor = db_conn.cursor()
    init_db()
    migrate_database()
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    
    logger.info(f"Server started on {HOST}:{PORT}")
    
    # Start broadcast thread
    broadcast_thread = threading.Thread(target=broadcast_updates, daemon=True)
    broadcast_thread.start()
    
    try:
        while True:
            conn, addr = server_socket.accept()
            logger.info(f"New connection from {addr}")
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        if server_socket:
            server_socket.close()
        if db_conn:
            db_conn.close()

if __name__ == '__main__':
    start_server()
