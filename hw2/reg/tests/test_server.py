import unittest
import sys
import os
import socket
import threading
import json
import sqlite3
from unittest.mock import MagicMock, patch
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from protocol import MessageType, StatusCode, create_message

class TestServer(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        server.DB_PATH = self.db_path  # Set the server's DB path
        
        # Initialize the database
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create necessary tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered INTEGER DEFAULT 0,
                read INTEGER DEFAULT NULL,
                FOREIGN KEY (sender) REFERENCES accounts(username),
                FOREIGN KEY (recipient) REFERENCES accounts(username)
            )
        ''')
        
        self.conn.commit()

    def tearDown(self):
        """Clean up after each test"""
        self.conn.close()
        os.unlink(self.db_path)  # Delete the temporary database

    def test_create_account(self):
        """Test account creation"""
        # Test data
        data = {
            "username": "testuser",
            "password": "testpass"
        }
        
        # Create account
        result = server.handle_create_account(data, self.cursor)
        self.conn.commit()
        
        # Verify success response
        self.assertEqual(result["status"], StatusCode.SUCCESS.value)
        
        # Verify account exists in database
        self.cursor.execute("SELECT username FROM accounts WHERE username=?", (data["username"],))
        account = self.cursor.fetchone()
        self.assertIsNotNone(account)
        self.assertEqual(account[0], data["username"])

    def test_create_duplicate_account(self):
        """Test creating account with existing username"""
        # Create first account
        data = {
            "username": "testuser",
            "password": "testpass"
        }
        server.handle_create_account(data, self.cursor)
        self.conn.commit()
        
        # Try to create duplicate account
        result = server.handle_create_account(data, self.cursor)
        self.conn.commit()
        
        # Verify error response
        self.assertEqual(result["status"], StatusCode.ERROR.value)

    def test_login(self):
        """Test login with valid credentials"""
        # Create account first
        data = {
            "username": "testuser",
            "password": "testpass"
        }
        server.handle_create_account(data, self.cursor)
        self.conn.commit()
        
        # Try to login
        result = server.handle_login(data, self.cursor)
        self.conn.commit()
        
        # Verify success response
        self.assertEqual(result["status"], StatusCode.SUCCESS.value)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Create account
        data = {
            "username": "testuser",
            "password": "testpass"
        }
        server.handle_create_account(data, self.cursor)
        self.conn.commit()
        
        # Try to login with wrong password
        wrong_data = {
            "username": "testuser",
            "password": "wrongpass"
        }
        result = server.handle_login(wrong_data, self.cursor)
        
        # Verify error response
        self.assertEqual(result["status"], StatusCode.ERROR.value)

    def test_handle_send_message(self):
        """Test message sending"""
        # Create sender and recipient accounts
        server.handle_create_account({
            "username": "sender", 
            "password": server.hash_password("pass")
        }, self.cursor)
        server.handle_create_account({
            "username": "recipient", 
            "password": server.hash_password("pass")
        }, self.cursor)
        self.conn.commit()  # Commit the transaction
        
        # Send a message
        message_data = {
            "username": "sender",
            "recipient": "recipient",
            "content": "Hello, world!"
        }
        
        result = server.handle_send_message(message_data, self.cursor)
        self.conn.commit()  # Commit the transaction
        
        self.assertEqual(result["status"], StatusCode.SUCCESS.value)
        
        # Verify message was stored
        self.cursor.execute("""
            SELECT sender, recipient, content 
            FROM messages 
            WHERE sender = ? AND recipient = ?
        """, (message_data["username"], message_data["recipient"]))
        
        msg = self.cursor.fetchone()
        self.assertIsNotNone(msg)
        self.assertEqual(msg[0], message_data["username"])
        self.assertEqual(msg[1], message_data["recipient"])
        self.assertEqual(msg[2], message_data["content"])

if __name__ == '__main__':
    unittest.main()
