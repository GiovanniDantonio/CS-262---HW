import grpc
import chat_pb2
import chat_pb2_grpc
from concurrent import futures
import sqlite3
import hashlib
from datetime import datetime
import time

DB_PATH = "chat.db"

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = {}  # Dictionary to store active clients and their streams
        self.init_db()

    def init_db(self):
        """Initialize the database."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read INTEGER DEFAULT 0
            )''')
        conn.commit()
        conn.close()

    def hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def Register(self, request, context):
        """Handle user registration."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", 
                      (request.username, self.hash_password(request.password)))
            conn.commit()
            return chat_pb2.Response(success=True, message="Account created successfully.")
        except sqlite3.IntegrityError:
            return chat_pb2.Response(success=False, message="Username already exists.")
        finally:
            conn.close()

    def Login(self, request, context):
        """Handle user login."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password FROM accounts WHERE username = ?", (request.username,))
        record = c.fetchone()
        if not record or record[0] != self.hash_password(request.password):
            return chat_pb2.LoginResponse(success=False, message="Invalid username or password.", unread_count=0)

        # Count unread messages
        c.execute("SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0", (request.username,))
        unread_count = c.fetchone()[0]

        return chat_pb2.LoginResponse(success=True, message="Login successful.", unread_count=unread_count)

    def SendMessage(self, request, context):
        """Send a message."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, recipient, content, read) VALUES (?, ?, ?, 0)",
                  (request.sender, request.recipient, request.content))
        conn.commit()
        conn.close()
        
        return chat_pb2.Response(success=True, message="Message sent successfully.")

    def GetMessages(self, request, context):
        """Fetch messages."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, sender, recipient, content, timestamp, read FROM messages WHERE recipient = ? ORDER BY timestamp DESC LIMIT ?", 
                  (request.username, request.count))
        messages = [chat_pb2.Message(id=row[0], sender=row[1], recipient=row[2], content=row[3], timestamp=row[4], read=bool(row[5])) for row in c.fetchall()]
        conn.close()
        return chat_pb2.MessageList(messages=messages)

    def StreamMessages(self, request, context):
        """Stream messages in real-time."""
        self.clients[request.username] = context
        try:
            while True:
                time.sleep(5)  # Simulate real-time updates
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT id, sender, recipient, content, timestamp, read FROM messages WHERE recipient = ? ORDER BY timestamp DESC LIMIT 10",
                          (request.username,))
                messages = [chat_pb2.Message(id=row[0], sender=row[1], recipient=row[2], content=row[3], timestamp=row[4], read=bool(row[5])) for row in c.fetchall()]
                conn.close()
                for msg in messages:
                    yield msg
        except grpc.RpcError:
            del self.clients[request.username]

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
