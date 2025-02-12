import unittest
import socket
import threading
import time
import os
import sys
import sqlite3
from datetime import datetime

# Add parent directory to path to import server and protocol
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
import protocol
from protocol import MessageType, StatusCode

class TestServer(unittest.TestCase):
    """Test suite for the chat server."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Use an in-memory database for testing
        server.DB_PATH = ':memory:'
        
        # Initialize database
        cls.db = sqlite3.connect(server.DB_PATH)
        server.init_db()
        cls.db.close()
        
        # Start server in a separate thread
        cls.server_thread = threading.Thread(target=server.start_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Give server time to start
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        try:
            # Close server socket
            server.server_socket.close()
            cls.server_thread.join(timeout=1)
        except:
            pass

    def setUp(self):
        """Set up test fixtures before each test."""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((server.HOST, server.PORT))
        
        # Create a test database connection and clean it
        self.db = sqlite3.connect(server.DB_PATH)
        self.cursor = self.db.cursor()
        self.cursor.execute("DELETE FROM accounts")
        self.cursor.execute("DELETE FROM messages")
        self.db.commit()

    def tearDown(self):
        """Clean up after each test."""
        try:
            self.client.close()
        except:
            pass
            
        try:
            self.cursor.close()
            self.db.close()
        except:
            pass

    # Smoke Tests
    def test_server_startup(self):
        """Smoke test: Can we connect to the server?"""
        new_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_client.connect((server.HOST, server.PORT))
        new_client.close()

    def test_basic_account_creation(self):
        """Smoke test: Can we create a basic account?"""
        message = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": "test_user",
                "password": "test_pass"
            }
        )
        protocol.send_json(self.client, message)
        response = protocol.recv_json(self.client)
        
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        
        # Verify in database
        self.cursor.execute("SELECT username FROM accounts WHERE username = ?", ("test_user",))
        self.assertIsNotNone(self.cursor.fetchone())

    # Boundary Tests
    def test_empty_username_password(self):
        """Boundary test: Empty username/password."""
        message = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": "",
                "password": ""
            }
        )
        protocol.send_json(self.client, message)
        response = protocol.recv_json(self.client)
        
        self.assertEqual(response["status"], StatusCode.ERROR.value)

    def test_duplicate_account(self):
        """Boundary test: Create duplicate account."""
        # Create first account
        message = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": "duplicate_user",
                "password": "test_pass"
            }
        )
        protocol.send_json(self.client, message)
        protocol.recv_json(self.client)
        
        # Try to create duplicate
        protocol.send_json(self.client, message)
        response = protocol.recv_json(self.client)
        
        self.assertEqual(response["status"], StatusCode.ERROR.value)

    # Thorough Tests
    def test_account_lifecycle(self):
        """Test complete account lifecycle: create, login, send message, delete."""
        # 1. Create account
        create_msg = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": "lifecycle_user",
                "password": "test_pass"
            }
        )
        protocol.send_json(self.client, create_msg)
        response = protocol.recv_json(self.client)
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        
        # 2. Login
        login_msg = protocol.create_message(
            MessageType.LOGIN,
            {
                "username": "lifecycle_user",
                "password": "test_pass"
            }
        )
        protocol.send_json(self.client, login_msg)
        response = protocol.recv_json(self.client)
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        
        # 3. Send message to self
        send_msg = protocol.create_message(
            MessageType.SEND_MESSAGE,
            {
                "sender": "lifecycle_user",
                "recipient": "lifecycle_user",
                "content": "test message"
            }
        )
        protocol.send_json(self.client, send_msg)
        response = protocol.recv_json(self.client)
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        
        # 4. Get messages
        get_msg = protocol.create_message(
            MessageType.GET_MESSAGES,
            {
                "username": "lifecycle_user",
                "count": 10
            }
        )
        protocol.send_json(self.client, get_msg)
        response = protocol.recv_json(self.client)
        self.assertEqual(response["status"], StatusCode.SUCCESS.value)
        self.assertEqual(len(response["data"]["messages"]), 1)

    def test_concurrent_clients(self):
        """Test multiple clients interacting simultaneously."""
        client_count = 10
        messages_per_client = 5
        clients = []
        
        def client_routine(client_id):
            # Create socket and connect
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server.HOST, server.PORT))
            clients.append(client_socket)
            
            username = f"user_{client_id}"
            
            # Create account
            create_msg = protocol.create_message(
                MessageType.CREATE_ACCOUNT,
                {
                    "username": username,
                    "password": "test_pass"
                }
            )
            protocol.send_json(client_socket, create_msg)
            protocol.recv_json(client_socket)
            
            # Send messages
            for i in range(messages_per_client):
                msg = protocol.create_message(
                    MessageType.SEND_MESSAGE,
                    {
                        "sender": username,
                        "recipient": f"user_{(client_id + 1) % client_count}",
                        "content": f"Message {i} from {username}"
                    }
                )
                protocol.send_json(client_socket, msg)
                protocol.recv_json(client_socket)
        
        # Start all clients
        threads = []
        for i in range(client_count):
            t = threading.Thread(target=client_routine, args=(i,))
            t.start()
            threads.append(t)
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify message count in database
        self.cursor.execute("SELECT COUNT(*) FROM messages")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, client_count * messages_per_client)
        
        # Clean up clients
        for client_socket in clients:
            client_socket.close()

    # Performance Tests
    def test_message_handling_performance(self):
        """Test server performance under load."""
        message_count = 100
        start_time = time.time()
        
        # Create test account
        create_msg = protocol.create_message(
            MessageType.CREATE_ACCOUNT,
            {
                "username": "perf_test",
                "password": "test_pass"
            }
        )
        protocol.send_json(self.client, create_msg)
        protocol.recv_json(self.client)
        
        # Send messages rapidly
        for i in range(message_count):
            msg = protocol.create_message(
                MessageType.SEND_MESSAGE,
                {
                    "sender": "perf_test",
                    "recipient": "perf_test",
                    "content": f"Message {i}"
                }
            )
            protocol.send_json(self.client, msg)
            protocol.recv_json(self.client)
        
        duration = time.time() - start_time
        messages_per_second = message_count / duration
        
        print(f"\nMessage handling throughput: {messages_per_second:.2f} messages/second")
        self.assertTrue(messages_per_second > 0)

    def test_connection_limit(self):
        """Test server behavior with many simultaneous connections."""
        max_connections = 100
        connections = []
        
        try:
            for i in range(max_connections):
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((server.HOST, server.PORT))
                connections.append(client)
        except Exception as e:
            print(f"\nServer reached connection limit at {len(connections)} connections")
        finally:
            for conn in connections:
                conn.close()
        
        self.assertTrue(len(connections) > 0)

if __name__ == '__main__':
    unittest.main()
