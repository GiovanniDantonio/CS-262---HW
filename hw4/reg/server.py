import grpc
import chat_pb2
import chat_pb2_grpc
from concurrent import futures
import sqlite3
import hashlib
from datetime import datetime
import time
import logging
import threading
import os
import json

# ------------------ Configuration ------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "server_config.json")
default_config = {
    "host": "0.0.0.0",    # Not used directly for gRPC, but for reference.
    "port": 50051,        # gRPC port (changed from 12345 to 50051)
    "db_path": "chat.db"
}

if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        user_config = json.load(f)
    config = {**default_config, **user_config}
else:
    logging.warning(f"No config file found at {CONFIG_FILE}. Using defaults.")
    config = default_config

HOST = config["host"]
PORT = config["port"]
DB_PATH = config["db_path"]

# ------------------ Logging Setup ------------------

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("chat_server")

# ------------------ Database Initialization & Migration ------------------

def init_db():
    """Initialize the SQLite database with required tables."""
    logger.info("Initializing database...")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read INTEGER DEFAULT 0,
                FOREIGN KEY (sender) REFERENCES accounts(username),
                FOREIGN KEY (recipient) REFERENCES accounts(username)
            )
        ''')
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

# ------------------ gRPC Service Implementation ------------------

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        # For streaming clients: map username -> context; used for bookkeeping.
        self.active_streams = {}
        self.lock = threading.Lock()
        init_db()
        migrate_database()

    def Register(self, request, context):
        """Handle user registration."""
        logger.info(f"Register request for: {request.username}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO accounts (username, password) VALUES (?, ?)",
                      (request.username, hash_password(request.password)))
            conn.commit()
            return chat_pb2.Response(success=True, message="Account created successfully.")
        except sqlite3.IntegrityError:
            return chat_pb2.Response(success=False, message="Username already exists.")
        except Exception as e:
            logger.error(f"Error in Register: {e}")
            return chat_pb2.Response(success=False, message="Account creation failed.")
        finally:
            conn.close()

    def Login(self, request, context):
        """Handle user login."""
        logger.info(f"Login attempt for: {request.username}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password FROM accounts WHERE username = ?", (request.username,))
        record = c.fetchone()
        if not record or record[0] != hash_password(request.password):
            conn.close()
            return chat_pb2.LoginResponse(success=False, message="Invalid username or password.", unread_count=0)
        # Update last_login
        c.execute("UPDATE accounts SET last_login = ? WHERE username = ?",
                  (datetime.utcnow(), request.username))
        # Count unread messages
        c.execute("SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0", (request.username,))
        unread_count = c.fetchone()[0]
        conn.commit()
        conn.close()
        logger.info(f"Login successful for {request.username}. Unread: {unread_count}")
        return chat_pb2.LoginResponse(success=True, message="Login successful.", unread_count=unread_count)

    def Logout(self, request, context):
        """Handle user logout."""
        logger.info(f"Logout request for: {request.username}")
        with self.lock:
            if request.username in self.active_streams:
                del self.active_streams[request.username]
        return chat_pb2.Response(success=True, message="Logged out successfully.")

    def DeleteAccount(self, request, context):
        """Handle account deletion."""
        logger.info(f"DeleteAccount request for: {request.username}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Get unread message count
        c.execute("SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0", (request.username,))
        unread_count = c.fetchone()[0]
        try:
            c.execute("DELETE FROM messages WHERE sender = ? OR recipient = ?", (request.username, request.username))
            c.execute("DELETE FROM accounts WHERE username = ?", (request.username,))
            conn.commit()
            # Remove from active streams if present.
            with self.lock:
                if request.username in self.active_streams:
                    del self.active_streams[request.username]
            return chat_pb2.Response(success=True, message=f"Account deleted. Unread messages: {unread_count}")
        except Exception as e:
            logger.error(f"Failed to delete account {request.username}: {e}")
            return chat_pb2.Response(success=False, message="Failed to delete account.")
        finally:
            conn.close()

    def ListAccounts(self, request, context):
        """Handle listing accounts."""
        logger.info(f"ListAccounts request: pattern='{request.pattern}', page={request.page}, per_page={request.per_page}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        pattern = request.pattern if request.pattern else "%"
        page = request.page if request.page > 0 else 1
        per_page = request.per_page if request.per_page > 0 else 10
        offset = (page - 1) * per_page
        c.execute(
            "SELECT username, created_at, last_login FROM accounts WHERE username LIKE ? ORDER BY username LIMIT ? OFFSET ?",
            (pattern, per_page, offset)
        )
        rows = c.fetchall()
        accounts = []
        for row in rows:
            accounts.append(chat_pb2.Account(
                username=row[0],
                created_at=row[1] if row[1] is not None else "",
                last_login=row[2] if row[2] is not None else ""
            ))
        conn.close()
        return chat_pb2.AccountListResponse(accounts=accounts, page=page, per_page=per_page)

    def SendMessage(self, request, context):
        """Handle sending a message."""
        logger.info(f"SendMessage: from {request.sender} to {request.recipient}: {request.content}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO messages (sender, recipient, content, read) VALUES (?, ?, ?, 0)",
                      (request.sender, request.recipient, request.content))
            message_id = c.lastrowid
            conn.commit()
            # Optionally, you could trigger broadcast updates here.
            return chat_pb2.Response(success=True, message="Message sent successfully.")
        except Exception as e:
            logger.error(f"Error in SendMessage: {e}")
            return chat_pb2.Response(success=False, message="Failed to send message.")
        finally:
            conn.close()

    def GetMessages(self, request, context):
        """Handle fetching messages."""
        logger.info(f"GetMessages: for {request.username} (limit {request.count})")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("SELECT id, sender, recipient, content, timestamp, read FROM messages WHERE recipient = ? ORDER BY timestamp DESC LIMIT ?",
                      (request.username, request.count))
            messages = []
            for row in c.fetchall():
                messages.append(chat_pb2.Message(
                    id=row[0],
                    sender=row[1],
                    recipient=row[2],
                    content=row[3],
                    timestamp=row[4],
                    read=bool(row[5])
                ))
            return chat_pb2.MessageList(messages=messages)
        except Exception as e:
            logger.error(f"Error in GetMessages: {e}")
            return chat_pb2.MessageList(messages=[])
        finally:
            conn.close()

    def DeleteMessages(self, request, context):
        """Handle deletion of messages."""
        logger.info(f"DeleteMessages: for {request.username}, IDs: {request.message_ids}")
        if not request.message_ids:
            return chat_pb2.Response(success=False, message="No message IDs provided.")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            placeholders = ','.join('?' for _ in request.message_ids)
            params = list(request.message_ids) + [request.username, request.username]
            c.execute(f"DELETE FROM messages WHERE id IN ({placeholders}) AND (sender = ? OR recipient = ?)", params)
            deleted_count = c.rowcount
            conn.commit()
            return chat_pb2.Response(success=True, message=f"Deleted {deleted_count} messages.")
        except Exception as e:
            logger.error(f"Error in DeleteMessages: {e}")
            return chat_pb2.Response(success=False, message="Failed to delete messages.")
        finally:
            conn.close()

    def MarkAsRead(self, request, context):
        """Handle marking messages as read."""
        logger.info(f"MarkAsRead: for {request.username}, IDs: {request.message_ids}")
        if not request.message_ids:
            return chat_pb2.Response(success=False, message="No message IDs provided.")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            placeholders = ','.join('?' for _ in request.message_ids)
            params = list(request.message_ids) + [request.username]
            c.execute(f"UPDATE messages SET read = 1 WHERE id IN ({placeholders}) AND recipient = ?", params)
            marked_count = c.rowcount
            conn.commit()
            return chat_pb2.Response(success=True, message=f"Marked {marked_count} messages as read.")
        except Exception as e:
            logger.error(f"Error in MarkAsRead: {e}")
            return chat_pb2.Response(success=False, message="Failed to mark messages as read.")
        finally:
            conn.close()

    def StreamMessages(self, request, context):
        """
        Stream unread messages for the given user in real time.
        This implementation polls the database every 3 seconds for new messages.
        """
        logger.info(f"StreamMessages: starting for user {request.username}")
        with self.lock:
            self.active_streams[request.username] = context

        try:
            while True:
                time.sleep(3)
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                # Only return unread messages.
                c.execute("SELECT id, sender, recipient, content, timestamp, read FROM messages WHERE recipient = ? AND read = 0 ORDER BY timestamp DESC LIMIT 50",
                          (request.username,))
                rows = c.fetchall()
                conn.close()
                for row in rows:
                    yield chat_pb2.Message(
                        id=row[0],
                        sender=row[1],
                        recipient=row[2],
                        content=row[3],
                        timestamp=row[4],
                        read=bool(row[5])
                    )
        except grpc.RpcError as e:
            logger.warning(f"StreamMessages: client {request.username} disconnected: {e}")
        finally:
            with self.lock:
                if request.username in self.active_streams:
                    del self.active_streams[request.username]


# ------------------ Server Setup ------------------

def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server_address = f"[::]:{PORT}"
    server.add_insecure_port(server_address)
    logger.info(f"Starting gRPC server on {server_address}...")
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.stop(0)

if __name__ == "__main__":
    serve()
