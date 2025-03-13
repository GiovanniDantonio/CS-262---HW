"""
Unit tests for the chat client.
Tests connection management, failover, and command handling.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.client import ChatClient
from proto import chat_pb2

class TestChatClient(unittest.TestCase):
    """Test cases for the chat client implementation."""
    
    def setUp(self):
        """Set up test environment with mocked gRPC channels and stubs."""
        # Create patches
        self.channel_patcher = patch('grpc.insecure_channel')
        self.mock_channel = self.channel_patcher.start()
        
        # Mock channel and stubs
        self.mock_channel_instance = MagicMock()
        self.mock_channel.return_value = self.mock_channel_instance
        
        self.mock_chat_stub = MagicMock()
        self.mock_raft_stub = MagicMock()
        
        # Setup mocks for stubs
        with patch('proto.chat_pb2_grpc.ChatServiceStub') as mock_chat_stub_class:
            mock_chat_stub_class.return_value = self.mock_chat_stub
            with patch('proto.chat_pb2_grpc.RaftServiceStub') as mock_raft_stub_class:
                mock_raft_stub_class.return_value = self.mock_raft_stub
                
                # Setup cluster status response
                mock_status = MagicMock()
                mock_status.leader_id = "server1"
                mock_status.current_term = 1
                
                # Create mock members
                member1 = MagicMock()
                member1.id = "server1"
                member1.address = "localhost:8001"
                member1.state = "leader"
                
                member2 = MagicMock()
                member2.id = "server2"
                member2.address = "localhost:8002"
                member2.state = "follower"
                
                mock_status.members = [member1, member2]
                
                self.mock_raft_stub.GetClusterStatus.return_value = mock_status
                
                # Create client
                self.server_addresses = ["localhost:8001", "localhost:8002", "localhost:8003"]
                self.client = ChatClient(self.server_addresses)
    
    def tearDown(self):
        """Clean up test environment."""
        self.channel_patcher.stop()
    
    def test_initial_connection(self):
        """Test that client successfully connects to one of the servers."""
        # Client should have connected to a server
        self.assertIsNotNone(self.client.current_server)
        self.assertIn(self.client.current_server, self.server_addresses)
        
        # Should have created a channel
        self.mock_channel.assert_called()
        
        # Should have queried cluster status
        self.mock_raft_stub.GetClusterStatus.assert_called()
    
    def test_register_success(self):
        """Test successful user registration."""
        # Mock successful registration
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = "User registered successfully"
        self.mock_chat_stub.Register.return_value = mock_response
        
        # Call register
        result = self.client.register("testuser", "password123")
        
        # Verify success
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "User registered successfully")
        
        # Verify stub was called with correct request
        register_request = self.mock_chat_stub.Register.call_args[0][0]
        self.assertEqual(register_request.username, "testuser")
        self.assertEqual(register_request.password, "password123")
    
    def test_register_not_leader(self):
        """Test registration when connected to non-leader node."""
        # Setup responses for first attempt (not leader) and redirect
        not_leader_response = MagicMock()
        not_leader_response.success = False
        not_leader_response.message = "Not the leader, try leader node: server1"
        
        success_response = MagicMock()
        success_response.success = True
        success_response.message = "User registered successfully"
        
        # Configure mock to return different responses on consecutive calls
        self.mock_chat_stub.Register.side_effect = [not_leader_response, success_response]
        
        # Call register
        result = self.client.register("testuser", "password123")
        
        # Verify success
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "User registered successfully")
        
        # Verify we tried to connect to the leader
        self.mock_channel.assert_has_calls([
            call(self.server_addresses[0]),  # Initial connection
            call("localhost:8001")           # Leader connection
        ], any_order=True)
    
    def test_login_success(self):
        """Test successful login."""
        # Mock successful login
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = "Login successful"
        mock_response.unread_count = 5
        mock_response.server_id = "server1"
        self.mock_chat_stub.Login.return_value = mock_response
        
        # Call login
        result = self.client.login("testuser", "password123")
        
        # Verify success
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Login successful")
        self.assertEqual(result["unread_count"], 5)
        self.assertEqual(result["server_id"], "server1")
        
        # Username should be set after login
        self.assertEqual(self.client.current_username, "testuser")
        
        # Verify stub was called with correct request
        login_request = self.mock_chat_stub.Login.call_args[0][0]
        self.assertEqual(login_request.username, "testuser")
        self.assertEqual(login_request.password, "password123")
    
    def test_send_message_success(self):
        """Test successful message sending."""
        # Set user as logged in
        self.client.current_username = "sender"
        
        # Mock successful send
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = "Message sent"
        self.mock_chat_stub.SendMessage.return_value = mock_response
        
        # Call send_message
        result = self.client.send_message("recipient", "Hello there!")
        
        # Verify success
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Message sent")
        
        # Verify stub was called with correct request
        send_request = self.mock_chat_stub.SendMessage.call_args[0][0]
        self.assertEqual(send_request.sender, "sender")
        self.assertEqual(send_request.recipient, "recipient")
        self.assertEqual(send_request.content, "Hello there!")
    
    def test_get_messages(self):
        """Test fetching messages."""
        # Set user as logged in
        self.client.current_username = "testuser"
        
        # Create mock message
        mock_message1 = MagicMock()
        mock_message1.id = 1
        mock_message1.sender = "user1"
        mock_message1.recipient = "testuser"
        mock_message1.content = "Hello!"
        mock_message1.timestamp = "2023-04-01T12:00:00Z"
        mock_message1.read = False
        mock_message1.sequence_number = 1
        
        # Create another mock message
        mock_message2 = MagicMock()
        mock_message2.id = 2
        mock_message2.sender = "user2"
        mock_message2.recipient = "testuser"
        mock_message2.content = "Hi there"
        mock_message2.timestamp = "2023-04-01T12:05:00Z"
        mock_message2.read = True
        mock_message2.sequence_number = 2
        
        # Mock response
        mock_response = MagicMock()
        mock_response.messages = [mock_message1, mock_message2]
        self.mock_chat_stub.GetMessages.return_value = mock_response
        
        # Call get_messages
        result = self.client.get_messages(10)
        
        # Verify messages are returned correctly
        self.assertTrue(result["success"])
        self.assertEqual(len(result["messages"]), 2)
        
        # Check details of first message
        msg1 = result["messages"][0]
        self.assertEqual(msg1["id"], 1)
        self.assertEqual(msg1["sender"], "user1")
        self.assertEqual(msg1["recipient"], "testuser")
        self.assertEqual(msg1["content"], "Hello!")
        self.assertFalse(msg1["read"])
        
        # Check details of second message
        msg2 = result["messages"][1]
        self.assertEqual(msg2["id"], 2)
        self.assertEqual(msg2["sender"], "user2")
        self.assertEqual(msg2["content"], "Hi there")
        self.assertTrue(msg2["read"])
        
        # Verify stub was called with correct request
        get_request = self.mock_chat_stub.GetMessages.call_args[0][0]
        self.assertEqual(get_request.username, "testuser")
        self.assertEqual(get_request.count, 10)
    
    def test_reconnect_on_failure(self):
        """Test reconnection when a server fails."""
        # Set up client
        self.client.current_username = "testuser"
        
        # Mock RPC error for first call
        self.mock_chat_stub.GetMessages.side_effect = [
            Exception("Connection failed"),  # First server fails
            MagicMock(messages=[])           # Second server succeeds
        ]
        
        # Call get_messages
        result = self.client.get_messages(10)
        
        # Should have successfully reconnected
        self.assertTrue(result["success"])
        
        # Should have tried to connect to multiple servers
        self.assertTrue(self.mock_channel.call_count >= 2)
    
    def test_logout(self):
        """Test user logout."""
        # Set user as logged in
        self.client.current_username = "testuser"
        
        # Mock successful logout
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = "Logged out successfully"
        self.mock_chat_stub.Logout.return_value = mock_response
        
        # Call logout
        result = self.client.logout()
        
        # Verify success
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Logged out successfully")
        
        # Username should be cleared
        self.assertIsNone(self.client.current_username)

if __name__ == '__main__':
    unittest.main()
