import unittest
import sys
import os
import tempfile
import sqlite3
import json
import logging
from datetime import datetime, UTC

# Disable logging during tests
logging.getLogger('chat_server').setLevel(logging.ERROR)

# Adjust path so that we can import the server module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import ChatService, init_db, migrate_database

# Dummy classes to simulate gRPC request and context objects
class DummyRequest:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class DummyContext:
    def is_active(self):
        return True
    def cancel(self):
        pass

class TestServer(unittest.TestCase):
    def setUp(self):
        """Create a temporary database and config for testing."""
        # Create temp database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Create temp config directory and file
        self.temp_config_dir = tempfile.mkdtemp()
        self.temp_config_file = os.path.join(self.temp_config_dir, 'replicated_config.json')
        config = {
            "replicas": {
                "0": {
                    "db_path": self.db_path,
                    "host": "localhost",
                    "port": "50051"
                }
            }
        }
        with open(self.temp_config_file, 'w') as f:
            json.dump(config, f)

        # Initialize database
        init_db(self.db_path)
        migrate_database(self.db_path)

        # Initialize server with test config
        import server
        server.CONFIG_FILE = self.temp_config_file
        self.server = ChatService(replica_id=0)
        self.context = DummyContext()

    def tearDown(self):
        """Clean up temporary files."""
        os.unlink(self.db_path)
        os.unlink(self.temp_config_file)
        os.rmdir(self.temp_config_dir)

    def test_register_and_login(self):
        """Test user registration and login functionality."""
        # Register a new user
        register_req = DummyRequest(username="testuser", password="testpass")
        response = self.server.Register(register_req, self.context)
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Account created successfully")

        # Try registering same user again
        response = self.server.Register(register_req, self.context)
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Username already exists")

        # Test login with correct credentials
        login_req = DummyRequest(username="testuser", password="testpass")
        response = self.server.Login(login_req, self.context)
        self.assertTrue(response.success)

        # Test login with wrong password
        wrong_pass_req = DummyRequest(username="testuser", password="wrongpass")
        response = self.server.Login(wrong_pass_req, self.context)
        self.assertFalse(response.success)

    def test_send_and_get_messages(self):
        """Test sending and retrieving messages."""
        # Register two users
        self.server.Register(DummyRequest(username="sender", password="pass"), self.context)
        self.server.Register(DummyRequest(username="receiver", password="pass"), self.context)

        # Send a message
        msg_req = DummyRequest(
            sender="sender",
            recipient="receiver",
            content="Hello, receiver!"
        )
        response = self.server.SendMessage(msg_req, self.context)
        self.assertTrue(response.success)

        # Get messages for receiver
        get_req = DummyRequest(username="receiver", count=10)
        response = self.server.GetMessages(get_req, self.context)
        self.assertEqual(len(response.messages), 1)
        msg = response.messages[0]
        self.assertEqual(msg.sender, "sender")
        self.assertEqual(msg.recipient, "receiver")
        self.assertEqual(msg.content, "Hello, receiver!")
        self.assertFalse(msg.read)

    def test_mark_messages_as_read(self):
        """Test marking messages as read."""
        # Setup users and send a message
        self.server.Register(DummyRequest(username="sender", password="pass"), self.context)
        self.server.Register(DummyRequest(username="receiver", password="pass"), self.context)
        self.server.SendMessage(
            DummyRequest(sender="sender", recipient="receiver", content="Test message"),
            self.context
        )

        # Get message ID
        get_req = DummyRequest(username="receiver", count=10)
        response = self.server.GetMessages(get_req, self.context)
        msg_id = response.messages[0].id

        # Mark message as read
        mark_req = DummyRequest(username="receiver", message_ids=[msg_id])
        response = self.server.MarkAsRead(mark_req, self.context)
        self.assertTrue(response.success)

        # Verify message is marked as read
        response = self.server.GetMessages(get_req, self.context)
        self.assertTrue(response.messages[0].read)

    def test_delete_account(self):
        """Test account deletion."""
        # Register a user
        self.server.Register(DummyRequest(username="testuser", password="pass"), self.context)

        # Delete the account
        del_req = DummyRequest(username="testuser")
        response = self.server.DeleteAccount(del_req, self.context)
        self.assertTrue(response.success)

        # Try to login with deleted account
        login_req = DummyRequest(username="testuser", password="pass")
        response = self.server.Login(login_req, self.context)
        self.assertFalse(response.success)

    def test_list_accounts(self):
        """Test listing accounts with pattern matching."""
        # Register multiple users
        usernames = ["user1", "user2", "test1", "test2"]
        for username in usernames:
            self.server.Register(DummyRequest(username=username, password="pass"), self.context)

        # List accounts with 'user' pattern
        list_req = DummyRequest(pattern="user%", page=1, per_page=10)
        response = self.server.ListAccounts(list_req, self.context)
        user_accounts = [acc.username for acc in response.accounts]
        self.assertEqual(len(user_accounts), 2)
        self.assertIn("user1", user_accounts)
        self.assertIn("user2", user_accounts)

if __name__ == '__main__':
    unittest.main()