import unittest
import sys
import os
import tempfile
import sqlite3
import time

# Adjust path so that we can import the server module.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from server import ChatService, DB_PATH  # DB_PATH will be overridden

# Dummy classes to simulate gRPC request and context objects.
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
        """Create a temporary database and override DB_PATH before instantiating ChatService."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()  # Close so SQLite can open it
        # Override the server's DB_PATH to point to our temporary database.
        import server
        server.DB_PATH = self.db_path
        # Instantiate ChatService; its __init__ will run init_db() and migrate_database() on our temporary DB.
        self.server = ChatService()
        self.context = DummyContext()

    def tearDown(self):
        """Clean up the temporary database file."""
        os.unlink(self.db_path)

    def test_register_and_login(self):
        """Test that a user can register and then log in."""
        # Register a new account.
        req_register = DummyRequest(username="user1", password="password1")
        response_reg = self.server.Register(req_register, self.context)
        self.assertTrue(response_reg.success, msg="Registration should succeed for a new user.")
        
        # Attempt duplicate registration.
        response_dup = self.server.Register(req_register, self.context)
        self.assertFalse(response_dup.success, msg="Duplicate registration should fail.")
        
        # Test login with correct credentials.
        req_login = DummyRequest(username="user1", password="password1")
        login_response = self.server.Login(req_login, self.context)
        self.assertTrue(login_response.success, msg="Login should succeed with correct credentials.")
        
        # Test login with wrong password.
        req_login_fail = DummyRequest(username="user1", password="wrongpassword")
        login_response_fail = self.server.Login(req_login_fail, self.context)
        self.assertFalse(login_response_fail.success, msg="Login should fail with incorrect password.")

    def test_send_and_get_message(self):
        """Test sending a message from one user to another and retrieving it."""
        # Register sender and recipient.
        req_sender = DummyRequest(username="sender", password="pass")
        req_recipient = DummyRequest(username="recipient", password="pass")
        self.server.Register(req_sender, self.context)
        self.server.Register(req_recipient, self.context)
        
        # Send a message.
        send_req = DummyRequest(sender="sender", recipient="recipient", content="Hello!")
        send_response = self.server.SendMessage(send_req, self.context)
        self.assertTrue(send_response.success, msg="Sending a message should succeed.")
        
        # Retrieve messages for the recipient.
        get_req = DummyRequest(username="recipient", count=10)
        msg_list = self.server.GetMessages(get_req, self.context)
        self.assertTrue(len(msg_list.messages) >= 1, msg="At least one message should be returned.")
        
        # Verify the content of the retrieved message.
        message = msg_list.messages[0]
        self.assertEqual(message.content, "Hello!")
        self.assertEqual(message.sender, "sender")
        self.assertEqual(message.recipient, "recipient")

    def test_delete_account(self):
        """Test account deletion along with associated messages."""
        # Register a user and a sender.
        req_user = DummyRequest(username="deleteme", password="pass")
        req_sender = DummyRequest(username="sender", password="pass")
        self.server.Register(req_user, self.context)
        self.server.Register(req_sender, self.context)
        
        # Send a message to the user.
        send_req = DummyRequest(sender="sender", recipient="deleteme", content="Hi!")
        self.server.SendMessage(send_req, self.context)
        
        # Delete the account.
        del_req = DummyRequest(username="deleteme")
        del_response = self.server.DeleteAccount(del_req, self.context)
        self.assertTrue(del_response.success, msg="Account deletion should succeed.")
        
        # Try to log in with the deleted account.
        login_req = DummyRequest(username="deleteme", password="pass")
        login_response = self.server.Login(login_req, self.context)
        self.assertFalse(login_response.success, msg="Login should fail for a deleted account.")

    def test_list_accounts(self):
        """Test listing accounts using a search pattern."""
        # Register several users.
        users = [f"user{i}" for i in range(5)]
        for user in users:
            req = DummyRequest(username=user, password="pass")
            self.server.Register(req, self.context)
        
        # List accounts with a pattern.
        list_req = DummyRequest(pattern="user%", page=1, per_page=10)
        account_list_response = self.server.ListAccounts(list_req, self.context)
        returned_users = [acc.username for acc in account_list_response.accounts]
        for user in users:
            self.assertIn(user, returned_users, msg=f"{user} should be listed.")

    def test_mark_as_read(self):
        """Test that marking messages as read works correctly."""
        # Register sender and recipient.
        req_sender = DummyRequest(username="sender", password="pass")
        req_recipient = DummyRequest(username="recipient", password="pass")
        self.server.Register(req_sender, self.context)
        self.server.Register(req_recipient, self.context)
        
        # Send a message.
        send_req = DummyRequest(sender="sender", recipient="recipient", content="Test Message")
        self.server.SendMessage(send_req, self.context)
        
        # Retrieve messages.
        get_req = DummyRequest(username="recipient", count=10)
        msg_list = self.server.GetMessages(get_req, self.context)
        self.assertTrue(len(msg_list.messages) >= 1, msg="There should be at least one message.")
        message_id = msg_list.messages[0].id
        
        # Mark the message as read.
        mark_req = DummyRequest(username="recipient", message_ids=[message_id])
        mark_response = self.server.MarkAsRead(mark_req, self.context)
        self.assertTrue(mark_response.success, msg="Marking as read should succeed.")
        
        # Retrieve messages again to confirm the read status.
        msg_list_after = self.server.GetMessages(get_req, self.context)
        for msg in msg_list_after.messages:
            if msg.id == message_id:
                self.assertTrue(msg.read, msg="Message should be marked as read.")

if __name__ == '__main__':
    unittest.main()
