import unittest
import socket
import threading
import time
import os
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to path to import client and protocol
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import protocol
from protocol import MessageType, StatusCode

class TestChatClientCore(unittest.TestCase):
    """Test suite for the chat client core functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Create a mock server
        cls.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.server.bind(('127.0.0.1', 12345))
        cls.server.listen(1)
        
        # Start mock server thread
        cls.server_thread = threading.Thread(target=cls.run_mock_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def run_mock_server(cls):
        """Run a simple mock server that echoes messages."""
        while True:
            try:
                conn, addr = cls.server.accept()
                threading.Thread(target=cls.handle_client, args=(conn,)).start()
            except:
                break

    @classmethod
    def handle_client(cls, conn):
        """Handle mock client connection."""
        try:
            while True:
                message = protocol.recv_json(conn)
                if not message:
                    break
                    
                # Create appropriate response based on message type
                if message["type"] == MessageType.CREATE_ACCOUNT.value:
                    response = protocol.create_message(
                        MessageType.CREATE_ACCOUNT,
                        {"username": message["data"]["username"]},
                        StatusCode.SUCCESS
                    )
                elif message["type"] == MessageType.LOGIN.value:
                    response = protocol.create_message(
                        MessageType.LOGIN,
                        {
                            "username": message["data"]["username"],
                            "unread_count": 0
                        },
                        StatusCode.SUCCESS
                    )
                elif message["type"] == MessageType.GET_MESSAGES.value:
                    response = protocol.create_message(
                        MessageType.GET_MESSAGES,
                        {
                            "messages": [
                                {
                                    "sender": "test_sender",
                                    "content": "test message",
                                    "timestamp": "2024-02-07T00:00:00"
                                }
                            ]
                        },
                        StatusCode.SUCCESS
                    )
                else:
                    response = protocol.create_message(
                        MessageType(message["type"]),
                        {"status": "ok"},
                        StatusCode.SUCCESS
                    )
                    
                protocol.send_json(conn, response)
        except:
            pass
        finally:
            conn.close()

    def setUp(self):
        """Set up test fixtures before each test."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('127.0.0.1', 12345))

    def tearDown(self):
        """Clean up after each test."""
        try:
            self.client_socket.close()
        except:
            pass

    # Smoke Tests
    def test_basic_connection(self):
        """Smoke test: Can we establish a basic connection?"""
        self.assertTrue(self.client_socket.fileno() != -1)

    def test_create_account(self):
        """Test basic account creation."""
        message = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": "test_user",
                "password": "test_pass"
            }
        )
        protocol.send_json(self.client_socket, message)
        response = protocol.recv_json(self.client_socket)
        
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        self.assertEqual(response["data"]["username"], "test_user")

    # Boundary Tests
    def test_empty_message(self):
        """Test handling of empty message."""
        with self.assertRaises(Exception):
            protocol.send_json(self.client_socket, None)

    def test_malformed_message(self):
        """Test handling of malformed message."""
        with self.assertRaises(Exception):
            protocol.send_json(self.client_socket, {"invalid": "message"})

    # Thorough Tests
    def test_message_lifecycle(self):
        """Test complete message lifecycle."""
        # 1. Create account
        create_msg = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": "lifecycle_user",
                "password": "test_pass"
            }
        )
        protocol.send_json(self.client_socket, create_msg)
        response = protocol.recv_json(self.client_socket)
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        
        # 2. Login
        login_msg = protocol.create_message(
            MessageType.LOGIN,
            {
                "username": "lifecycle_user",
                "password": "test_pass"
            }
        )
        protocol.send_json(self.client_socket, login_msg)
        response = protocol.recv_json(self.client_socket)
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        
        # 3. Get messages
        get_msg = protocol.create_message(
            MessageType.GET_MESSAGES,
            {
                "username": "lifecycle_user",
                "count": 10
            }
        )
        protocol.send_json(self.client_socket, get_msg)
        response = protocol.recv_json(self.client_socket)
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        self.assertIn("messages", response["data"])

    def test_protocol_validation(self):
        """Test protocol message validation."""
        # Test valid message
        valid_msg = protocol.create_message(
            MessageType.LOGIN,
            {
                "username": "test_user",
                "password": "test_pass"
            }
        )
        self.assertTrue(protocol.validate_message(valid_msg))
        
        # Test invalid message type
        with self.assertRaises(ValueError):
            protocol.create_message(
                "invalid_type",
                {"data": "test"}
            )
        
        # Test missing required fields
        invalid_msg = {
            "type": MessageType.LOGIN.value,
            "data": {}  # Missing required fields
        }
        with self.assertRaises(Exception):
            protocol.validate_message(invalid_msg)

    # Performance Tests
    def test_message_throughput(self):
        """Test message sending/receiving throughput."""
        message_count = 100
        start_time = time.time()
        
        # Send many messages rapidly
        message = protocol.create_message(
            MessageType.SEND_MESSAGE,
            {
                "sender": "test_user",
                "recipient": "test_recipient",
                "content": "test message"
            }
        )
        
        for _ in range(message_count):
            protocol.send_json(self.client_socket, message)
            response = protocol.recv_json(self.client_socket)
            self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        
        duration = time.time() - start_time
        messages_per_second = message_count / duration
        
        print(f"\nMessage throughput: {messages_per_second:.2f} messages/second")
        self.assertTrue(messages_per_second > 0)

if __name__ == '__main__':
    unittest.main()
