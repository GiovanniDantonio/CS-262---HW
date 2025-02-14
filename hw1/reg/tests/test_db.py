import unittest
import sys
import os
import sqlite3
import tempfile
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Create a temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Enable foreign key constraints
        self.cursor.execute("PRAGMA foreign_keys = ON")
        
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
        """Clean up the temporary database"""
        self.conn.close()
        os.unlink(self.db_path)

    def test_account_creation(self):
        """Test creating a new account"""
        username = "testuser"
        password = "testpass"
        
        # Create account
        self.cursor.execute(
            "INSERT INTO accounts (username, password) VALUES (?, ?)",
            (username, password)
        )
        self.conn.commit()
        
        # Verify account exists
        self.cursor.execute("SELECT username, password FROM accounts WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], username)
        self.assertEqual(result[1], password)

    def test_message_creation(self):
        """Test creating a new message between users"""
        # Create sender and recipient accounts
        self.cursor.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", ("sender", "pass1"))
        self.cursor.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", ("recipient", "pass2"))
        self.conn.commit()
        
        # Send message
        self.cursor.execute("""
            INSERT INTO messages (sender, recipient, content, delivered)
            VALUES (?, ?, ?, ?)
        """, ("sender", "recipient", "Hello!", 0))
        self.conn.commit()
        
        # Verify message exists
        self.cursor.execute("""
            SELECT sender, recipient, content, delivered, read
            FROM messages
            WHERE sender = ? AND recipient = ?
        """, ("sender", "recipient"))
        
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "sender")
        self.assertEqual(result[1], "recipient")
        self.assertEqual(result[2], "Hello!")
        self.assertEqual(result[3], 0)  # delivered
        self.assertIsNone(result[4])    # read status

    def test_foreign_key_constraint(self):
        """Test that messages can't be created with non-existent users"""
        # Try to create message with non-existent users
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("""
                INSERT INTO messages (sender, recipient, content)
                VALUES (?, ?, ?)
            """, ("nonexistent", "alsononexistent", "Hello!"))
            self.conn.commit()

if __name__ == '__main__':
    unittest.main()
