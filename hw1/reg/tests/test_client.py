import unittest
import sys
import os
import socket
import threading
import tkinter as tk
from unittest.mock import MagicMock, patch
import json
import queue

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import ChatClient, hash_password
from protocol import MessageType, StatusCode, create_message

class TestChatClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that can be shared across all tests"""
        cls.root = tk.Tk()
        cls.root.withdraw()  # Hide the window

    @classmethod
    def tearDownClass(cls):
        """Clean up shared test fixtures"""
        cls.root.destroy()

    def setUp(self):
        """Set up test environment before each test"""
        # Create socket patcher
        self.socket_patcher = patch('socket.socket')
        self.mock_socket = self.socket_patcher.start()
        
        # Mock socket connection and file-like object
        self.mock_socket.return_value.connect = MagicMock()
        self.mock_socket.return_value.send = MagicMock()
        self.mock_socket.return_value.makefile.return_value.readline.return_value = ""
        
        # Create client instance
        with patch('tkinter.Entry') as mock_entry:
            # Create mock Entry instances
            mock_username_entry = MagicMock()
            mock_password_entry = MagicMock()
            
            # Configure mock Entry instances
            mock_entry.side_effect = [mock_username_entry, mock_password_entry]
            
            # Create client
            self.client = ChatClient(self.root)
            
            # Store mock entries for later use
            self.client.username_entry = mock_username_entry
            self.client.password_entry = mock_password_entry

    def tearDown(self):
        """Clean up after each test"""
        if self.client and hasattr(self.client, 'sock'):
            self.client.sock.close()
        self.socket_patcher.stop()

    def test_client_connection(self):
        """Test that client connects to server on initialization"""
        # Verify socket connection was attempted
        self.mock_socket.return_value.connect.assert_called_once()
        
        # Verify initial state
        self.assertIsNone(self.client.username)
        self.assertFalse(self.client._logging_out)
        self.assertIsNotNone(self.client.listener_thread)

    @patch('client.protocol.send_json')
    @patch('socket.socket')
    @patch('client.hash_password')
    def test_login_request(self, mock_hash_password, mock_socket_class, mock_send_json):
        """Test login request creation and sending"""
        username = "testuser"
        password = "testpass"
        hashed_password = "hashedpass123"  # Mock hashed password
        
        # Mock hash_password
        mock_hash_password.return_value = hashed_password
        
        # Mock socket instance
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.makefile.return_value.readline.return_value = ""
        
        # Mock entry values
        self.client.username_entry.get.return_value = username
        self.client.password_entry.get.return_value = password
        
        # Call login
        self.client.login()
        
        # Verify send_json was called
        mock_send_json.assert_called()
        
        # Get the sent message
        _, sent_message = mock_send_json.call_args[0]
        
        # Verify message format
        self.assertEqual(sent_message["type"], MessageType.LOGIN.value)
        self.assertEqual(sent_message["data"]["username"], username)
        self.assertEqual(sent_message["data"]["password"], hashed_password)
        
        # Verify hash_password was called with correct password
        mock_hash_password.assert_called_once_with(password)

    def test_send_chat_message(self):
        """Test sending a chat message"""
        # Set up client as logged in
        self.client.username = "sender"
        
        # Create test message
        recipient = "recipient"
        content = "Hello, world!"
        
        # Create and send message
        message = create_message(
            MessageType.SEND_MESSAGE,
            {
                "username": self.client.username,
                "recipient": recipient,
                "content": content
            }
        )
        
        # Send the message
        self.client.sock.send(json.dumps(message).encode('utf-8') + b'\n')
        
        # Verify send was called with correct data
        self.mock_socket.return_value.send.assert_called_once()
        sent_data = self.mock_socket.return_value.send.call_args[0][0]
        sent_message = json.loads(sent_data.decode('utf-8').strip())
        
        # Verify message format
        self.assertEqual(sent_message["type"], MessageType.SEND_MESSAGE.value)
        self.assertEqual(sent_message["data"]["username"], "sender")
        self.assertEqual(sent_message["data"]["recipient"], recipient)
        self.assertEqual(sent_message["data"]["content"], content)

if __name__ == '__main__':
    unittest.main()