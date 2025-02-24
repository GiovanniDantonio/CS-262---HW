import unittest
import sys
import os
import tkinter as tk
from unittest.mock import MagicMock, patch
import json

# Adjust the path so we can import the client module.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from client import ChatClient, hash_password
from protocol import MessageType

class TestChatClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up a Tk root window (hidden) for the tests."""
        cls.root = tk.Tk()
        cls.root.withdraw()  # Hide the main window

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        """
        Create a ChatClient instance and override its gRPC stub with a MagicMock.
        Also, patch the UI elements so that we can simulate user input.
        """
        self.client = ChatClient(self.root)
        # Override the gRPC stub with a MagicMock to simulate responses.
        self.client.stub = MagicMock()
        
        # For login, the username and password entries are created in create_login_widgets().
        self.client.username_entry.get = MagicMock()
        self.client.password_entry.get = MagicMock()
        # For sending messages, ensure chat widget entries exist.
        self.client.recipient_entry = MagicMock()
        self.client.recipient_entry.get = MagicMock()
        self.client.message_entry = MagicMock()
        self.client.message_entry.get = MagicMock()
        # Also stub out the delete method for the message_entry.
        self.client.message_entry.delete = MagicMock()

    def tearDown(self):
        pass

    def test_client_connection(self):
        """
        Test that the ChatClient initializes correctly:
        - No user is logged in.
        - The gRPC channel and stub are set up.
        """
        self.assertIsNone(self.client.username)
        self.assertIsNotNone(self.client.channel)
        self.assertIsNotNone(self.client.stub)

    @patch('tkinter.messagebox.showinfo')
    @patch('tkinter.messagebox.showerror')
    def test_login_request(self, mock_showerror, mock_showinfo):
        """
        Test that the login method calls the stub.Login method with the correct
        credentials and, upon a successful response, sets the username and shows an info message.
        """
        username = "testuser"
        password = "testpass"
        self.client.username_entry.get.return_value = username
        self.client.password_entry.get.return_value = password

        # Create a fake login response from the stub.
        fake_response = MagicMock()
        fake_response.success = True
        fake_response.message = "Login successful."
        fake_response.unread_count = 3
        self.client.stub.Login.return_value = fake_response

        # Call login
        self.client.login()

        # Verify that stub.Login was called exactly once with a UserCredentials object
        self.client.stub.Login.assert_called_once()
        args, _ = self.client.stub.Login.call_args
        credentials = args[0]
        self.assertEqual(credentials.username, username)
        self.assertEqual(credentials.password, hash_password(password))

        # Upon successful login, the username should be set and a success message shown.
        self.assertEqual(self.client.username, username)
        mock_showinfo.assert_called_with("Success", f"Login successful! You have {fake_response.unread_count} unread messages.")
        # Ensure showerror was not called.
        mock_showerror.assert_not_called()

    def test_send_chat_message(self):
        """
        Test that the send_message method calls stub.SendMessage with the correct message,
        and, on a successful send, clears the message entry.
        """
        sender = "sender"
        recipient = "recipient"
        content = "Hello, world!"
        
        # Set the client as logged in.
        self.client.username = sender
        
        # Set up the chat message fields.
        self.client.recipient_entry.get.return_value = recipient
        self.client.message_entry.get.return_value = content

        # Create a fake successful response for SendMessage.
        fake_response = MagicMock()
        fake_response.success = True
        fake_response.message = "Message sent successfully."
        self.client.stub.SendMessage.return_value = fake_response

        # Call send_message.
        self.client.send_message()

        # Verify that stub.SendMessage was called once.
        self.client.stub.SendMessage.assert_called_once()
        args, _ = self.client.stub.SendMessage.call_args
        message = args[0]
        self.assertEqual(message.sender, sender)
        self.assertEqual(message.recipient, recipient)
        self.assertEqual(message.content, content)

        # After a successful send, the message entry should be cleared.
        self.client.message_entry.delete.assert_called_once_with(0, tk.END)

if __name__ == '__main__':
    unittest.main()
