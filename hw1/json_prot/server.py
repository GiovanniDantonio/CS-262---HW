import socket
import sqlite3
import threading
import hashlib
import json
import logging
from datetime import datetime
import protocol as protocol
from protocol import MessageType, StatusCode

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_server")

# Constants
PORT = 12345
HOST = '0.0.0.0'
DB_PATH = 'chat.db'

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
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivered INTEGER DEFAULT 0,
                    deleted INTEGER DEFAULT 0,
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

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

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
        "SELECT COUNT(*) FROM messages WHERE recipient = ? AND delivered = 0 AND deleted = 0",
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
    sender = data.get('sender')
    recipient = data.get('recipient')
    content = data.get('content')
    
    if not all([sender, recipient, content]):
        return protocol.create_error("Sender, recipient, and content required")
    
    # Verify both users exist
    c.execute("SELECT username FROM accounts WHERE username IN (?, ?)", (sender, recipient))
    users = c.fetchall()
    if len(users) != 2:
        return protocol.create_error("Invalid sender or recipient")
    
    try:
        c.execute(
            """INSERT INTO messages (sender, recipient, content, timestamp) 
               VALUES (?, ?, ?, ?)""",
            (sender, recipient, content, datetime.utcnow())
        )
        return protocol.create_message(
            MessageType.SEND_MESSAGE,
            {"message_id": c.lastrowid},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return protocol.create_error("Failed to send message")

def handle_get_messages(data: dict, c: sqlite3.Cursor) -> dict:
    """Handle message retrieval request."""
    logger.debug(f"Handling get messages request: {data}")
    username = data.get('username')
    count = data.get('count', 10)
    
    if not username:
        return protocol.create_error("Username required")
    
    c.execute(
        """SELECT id, sender, content, timestamp 
           FROM messages 
           WHERE recipient = ? AND deleted = 0 
           ORDER BY timestamp DESC 
           LIMIT ?""",
        (username, count)
    )
    
    messages = [{
        "id": row[0],
        "sender": row[1],
        "content": row[2],
        "timestamp": row[3]
    } for row in c.fetchall()]
    
    # Mark messages as delivered
    if messages:
        c.execute(
            "UPDATE messages SET delivered = 1 WHERE recipient = ? AND delivered = 0",
            (username,)
        )
    
    return protocol.create_message(
        MessageType.GET_MESSAGES,
        {"messages": messages},
        StatusCode.SUCCESS
    )

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
            f"""UPDATE messages 
                SET deleted = 1 
                WHERE id IN ({placeholders})
                AND (sender = ? OR recipient = ?)""",
            (*message_ids, username, username)
        )
        
        return protocol.create_message(
            MessageType.DELETE_MESSAGES,
            {"deleted_count": c.rowcount},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to delete messages: {e}")
        return protocol.create_error("Failed to delete messages")

def handle_client(client_socket: socket.socket, addr: tuple):
    """Handle client connection and route messages to appropriate handlers."""
    logger.info(f"New client connected: {addr}")
    try:
        while True:
            message = protocol.recv_json(client_socket)
            if not message:
                break
                
            if isinstance(message, str):  # Error occurred
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
                    MessageType.DELETE_MESSAGES: handle_delete_messages
                }
                
                handler = handler_map.get(msg_type)
                if handler:
                    response = handler(data, c)
                    conn.commit()
                else:
                    response = protocol.create_error(f"Unsupported message type: {msg_type}")
                
                protocol.send_json(client_socket, response)
                
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                protocol.send_json(client_socket, protocol.create_error(str(e)))
                conn.rollback()
            finally:
                conn.close()
                
    except Exception as e:
        logger.error(f"Client connection error: {e}")
    finally:
        client_socket.close()
        logger.info(f"Client disconnected: {addr}")

def start_server():
    """Start the chat server."""
    logger.info("Initializing server...")
    init_db()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        logger.info(f"Server listening on {HOST}:{PORT}")
        
        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, addr)
            )
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server_socket.close()

if __name__ == '__main__':
    start_server()
