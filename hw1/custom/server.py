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

# Load in Configuration File
CONFIG_FILE = "server_config.json"
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
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivered INTEGER DEFAULT 0,
                    read INTEGER DEFAULT NULL,
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
            c.execute("ALTER TABLE messages ADD COLUMN read INTEGER DEFAULT NULL")
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
    while True:
        try:
            time.sleep(5)  # Broadcast every 5 seconds
            
            # Create a new connection and cursor in this thread:
            conn_broadcast = sqlite3.connect(DB_PATH)
            cursor_broadcast = conn_broadcast.cursor()
            
            with threading.Lock():
                # Get all online users
                online_users = list(active_clients.keys())
                
                # Create broadcast message for each connected user
                for username, (conn, _) in active_clients.items():
                    try:
                        # 1) Send user list update
                        users_msg = protocol.create_message_custom(
                            MessageType.BROADCAST,
                            {"type": "users", "users": online_users},
                            StatusCode.SUCCESS
                        )
                        protocol.send_custom(conn, users_msg)
                        
                        # 2) Send messages update using the broadcast thread’s cursor:
                        cursor_broadcast.execute("""
                            SELECT m.id, m.sender, m.recipient, m.content, m.timestamp
                            FROM messages m
                            WHERE m.recipient = ?
                            ORDER BY m.timestamp DESC
                            LIMIT 50
                        """, (username,))
                        messages = cursor_broadcast.fetchall()
                        
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
                        
                        msg_msg = protocol.create_message_custom(
                            MessageType.BROADCAST,
                            {"type": "messages", "messages": messages_list},
                            StatusCode.SUCCESS
                        )
                        protocol.send_custom(conn, msg_msg)
                        
                    except Exception as e:
                        logger.error(f"Error broadcasting to {username}: {e}")
            # Close the broadcast connection after done:
            conn_broadcast.close()
            
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
        
        msg_msg = protocol.create_message_custom(
            MessageType.BROADCAST,
            {
                "type": "messages",
                "messages": messages_list
            },
            StatusCode.SUCCESS
        )
        protocol.send_custom(user_socket, msg_msg)
        
        # Send online users update
        users_msg = protocol.create_message_custom(
            MessageType.BROADCAST,
            {
                "type": "users",
                "users": list(active_clients.keys())
            },
            StatusCode.SUCCESS
        )
        protocol.send_custom(user_socket, users_msg)
        
    except Exception as e:
        logger.error(f"Error broadcasting to {username}: {e}")
        del active_clients[username]

def handle_create_account(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle account creation request, returning raw bytes."""
    logger.debug(f"Handling create account request: {data}")
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username and password required"},
            StatusCode.ERROR
        )
    
    c.execute("SELECT username FROM accounts WHERE username = ?", (username,))
    if c.fetchone():
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username already exists"},
            StatusCode.ERROR
        )
    
    hashed_pwd = hash_password(password)
    try:
        c.execute(
            "INSERT INTO accounts (username, password, created_at) VALUES (?, ?, ?)",
            (username, hashed_pwd, datetime.utcnow())
        )
        # If insertion is successful:
        return protocol.create_message_custom(
            MessageType.CREATE_ACCOUNT,
            {"username": username},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Account creation failed: {e}")
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Account creation failed"},
            StatusCode.ERROR
        )

def handle_login(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle login request, returning raw bytes."""
    logger.debug(f"Handling login request: {data}")
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username and password required"},
            StatusCode.ERROR
        )
    
    c.execute("SELECT password FROM accounts WHERE username = ?", (username,))
    record = c.fetchone()
    
    if not record:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username not found"},
            StatusCode.ERROR
        )
    
    if record[0] != hash_password(password):
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Incorrect password"},
            StatusCode.ERROR
        )
    
    # Update last login
    c.execute(
        "UPDATE accounts SET last_login = ? WHERE username = ?",
        (datetime.utcnow(), username)
    )

    # Count unread messages
    c.execute(
        "SELECT COUNT(*) FROM messages WHERE recipient = ? AND delivered = 0",
        (username,)
    )
    unread_count = c.fetchone()[0]
    
    # Return raw bytes
    return protocol.create_message_custom(
        MessageType.LOGIN,
        {
            "username": username,
            "unread_count": unread_count
        },
        StatusCode.SUCCESS
    )

def handle_logout(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle user logout request, returning raw bytes."""
    logger.debug(f"Handling logout request: {data}")
    username = data.get('username')

    if not username:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username is required to logout."},
            StatusCode.ERROR
        )

    # If the user is in active_clients, remove them
    if username in active_clients:
        del active_clients[username]
        logger.info(f"User '{username}' has been logged out successfully.")
        return protocol.create_message_custom(
            MessageType.LOGOUT,
            {},
            StatusCode.SUCCESS
        )
    else:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "User not currently logged in or not found in active list."},
            StatusCode.ERROR
        )

def handle_delete_account(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle account deletion request, returning raw bytes."""
    logger.debug(f"Handling delete account request: {data}")
    username = data.get('username')
    
    if not username:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username is required to delete an account."},
            StatusCode.ERROR
        )
    
    # Check if user exists
    c.execute("SELECT username FROM accounts WHERE username = ?", (username,))
    record = c.fetchone()
    if not record:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "User not found."},
            StatusCode.ERROR
        )

    # Get unread message count
    c.execute(
        "SELECT COUNT(*) FROM messages WHERE recipient = ? AND delivered = 0",
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
        
        return protocol.create_message_custom(
            MessageType.DELETE_ACCOUNT,
            {
                "username": username,
                "unread_count": unread_count
            },
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to delete account for {username}: {e}")
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Failed to delete account."},
            StatusCode.ERROR
        )

def handle_list_accounts(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle account listing request, returning raw bytes."""
    logger.debug(f"Handling list accounts request: {data}")
    pattern = data.get('pattern', '%')
    page = data.get('page', 1)
    page = int(page)
    per_page = data.get('per_page', 10)
    per_page = int(per_page)
    
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
    
    return protocol.create_message_custom(
        MessageType.LIST_ACCOUNTS,
        {
            "accounts": accounts,
            "page": page,
            "per_page": per_page
        },
        StatusCode.SUCCESS
    )

def handle_send_message(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle message sending request, returning raw bytes."""
    logger.debug(f"Handling send message request: {data}")
    username = data.get('username')
    recipient = data.get('recipient')
    content = data.get('content')
    
    if not all([username, recipient, content]):
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username, recipient, and content are required"},
            StatusCode.ERROR
        )

    # Check if recipient exists
    c.execute("SELECT username FROM accounts WHERE username = ?", (recipient,))
    if not c.fetchone():
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Recipient not found"},
            StatusCode.ERROR
        )
    
    try:
        # Insert the message
        c.execute(
            """INSERT INTO messages (sender, recipient, content, delivered) 
               VALUES (?, ?, ?, ?)""",
            (username, recipient, content, 0)
        )
        message_id = c.lastrowid
        
        # Retrieve timestamp, read status
        c.execute("SELECT timestamp, read FROM messages WHERE id = ?", (message_id,))
        result = c.fetchone()
        if not result:
            raise Exception("Message insertion failed.")
        
        timestamp, read_status = result
        
        # (Possibly broadcast updates or mark delivered.)

        # Return raw bytes
        return protocol.create_message_custom(
            MessageType.SEND_MESSAGE,
            {
                "id": message_id,
                "timestamp": str(timestamp),
                "read": read_status
            },
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to send message. Error: {str(e)}")
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": f"Failed to send message: {str(e)}"},
            StatusCode.ERROR
        )

def handle_get_messages(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle message retrieval request, returning raw bytes."""
    logger.debug(f"Handling get messages request: {data}")
    username = data.get('username')
    count = data.get('count', 10)  # Default to 10 messages
    
    if not username:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username required"},
            StatusCode.ERROR
        )
    
    try:
        # Get messages where user is recipient
        c.execute(
            """SELECT id, sender, content, timestamp,
                      CASE 
                          WHEN read IS NULL THEN 0
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
                'read': row[4]  # 0 for NULL (unread), 1 for read
            })
        
        return protocol.create_message_custom(
            MessageType.GET_MESSAGES,
            {"messages": messages},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to get messages. Error: {str(e)}")
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": f"Failed to get messages: {str(e)}"},
            StatusCode.ERROR
        )

def handle_delete_messages(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle message deletion request, returning raw bytes."""
    logger.debug(f"Handling delete messages request: {data}")
    username = data.get('username')
    message_ids = data.get('message_ids', [])
    
    if not username or not message_ids:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username and message IDs required"},
            StatusCode.ERROR
        )
    
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
        
        return protocol.create_message_custom(
            MessageType.DELETE_MESSAGES,
            {"deleted_count": deleted_count},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to delete messages: {e}")
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Failed to delete messages"},
            StatusCode.ERROR
        )

def handle_mark_as_read(data: dict, c: sqlite3.Cursor) -> bytes:
    """Handle marking messages as read, returning raw bytes."""
    logger.debug(f"Handling mark as read request: {data}")
    username = data.get('username')
    message_ids = data.get('message_ids', [])
    
    if not username or not message_ids:
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Username and message IDs required"},
            StatusCode.ERROR
        )
    
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
        
        return protocol.create_message_custom(
            MessageType.MARK_AS_READ,
            {"marked_count": c.rowcount},
            StatusCode.SUCCESS
        )
    except Exception as e:
        logger.error(f"Failed to mark messages as read: {e}")
        return protocol.create_message_custom(
            MessageType.ERROR,
            {"message": "Failed to mark messages as read"},
            StatusCode.ERROR
        )

def handle_client(client_socket: socket.socket, addr: tuple):
    """Main client loop: read incoming messages, call handlers, send back bytes."""
    logger.info(f"New client connected: {addr}")
    client_username = None
    try:
        while True:
            # Receive a message in our custom format
            message = protocol.recv_custom(client_socket)
            if not message:
                # Client disconnected or no data
                break

            if isinstance(message, str):
                # Some error from recv_custom
                logger.error(f"Error receiving message: {message}")
                continue

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            try:
                # Convert inbound message type string to an enum
                msg_type = MessageType(message['type'])
                data = message['data']

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
                
                # We'll store the raw bytes the handler returns here
                response_bytes = None

                if handler:
                    response_bytes = handler(data, c)
                    # Commit DB changes after the handler
                    conn.commit()
                else:
                    # If we have no handler for this type
                    response_bytes = protocol.create_message_custom(
                        MessageType.ERROR,
                        {"message": f"Unsupported message type: {msg_type.value}"},
                        StatusCode.ERROR
                    )

                # If we got something to send, send it
                if response_bytes:
                    protocol.send_custom(client_socket, response_bytes)

                # If login was successful, track the client
                # NOTE: This checks the INBOUND message's status (the client sent 'pending').
                # If you want to track the user only if the SERVER's handler says "success",
                # you'd need to parse the outbound response bytes or track it differently.
                if message['type'] == MessageType.LOGIN.value:
                  username = data['username']
                  client_username = username
                  active_clients[username] = (client_socket, time.time())

            except Exception as e:
                logger.error(f"Error handling message: {e}")
                # If the handler or code above raised an error,
                # send back an ERROR message
                error_bytes = protocol.create_message_custom(
                    MessageType.ERROR,
                    {"message": str(e)},
                    StatusCode.ERROR
                )
                protocol.send_custom(client_socket, error_bytes)
                conn.rollback()
            finally:
                conn.close()

    except Exception as e:
        logger.error(f"Client connection error: {e}")
    finally:
        # On exit, clean up
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
