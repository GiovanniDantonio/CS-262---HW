#!/usr/bin/env python3
"""
Test suite for data persistence in the distributed chat system.
Tests data persistence across node restarts and system recovery.
"""
import unittest
import time
import logging
import os
import sys
import json
from concurrent import futures

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
distributed_chat_dir = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, distributed_chat_dir)

from distributed_chat.node import Node
from distributed_chat.client import Client

class TestDataPersistence(unittest.TestCase):
    """Test suite for data persistence scenarios."""

    def setUp(self):
        """Set up test environment before each test."""
        self.nodes = []
        # Start 3 nodes for testing
        for i in range(3):
            node = Node(node_id=i+1)
            node.start()
            self.nodes.append(node)
        time.sleep(2)  # Allow time for leader election

    def tearDown(self):
        """Clean up after each test."""
        for node in self.nodes:
            node.stop()
        time.sleep(1)  # Allow time for clean shutdown

    def test_data_persistence_across_restarts(self):
        """
        Test that data persists when nodes restart.
        Steps:
        1. Send test messages
        2. Stop all nodes
        3. Restart nodes
        4. Verify messages are still available
        """
        # Send test messages
        client = Client()
        client.connect()
        test_messages = [
            "Test message 1 for persistence",
            "Test message 2 for persistence",
            "Test message 3 for persistence"
        ]
        
        for msg in test_messages:
            response = client.send_message(msg)
            self.assertTrue(response.success, f"Failed to send message: {msg}")
        
        client.disconnect()
        
        # Stop all nodes
        for node in self.nodes:
            node.stop()
        time.sleep(2)
        
        # Restart nodes
        self.nodes = []
        for i in range(3):
            node = Node(node_id=i+1)
            node.start()
            self.nodes.append(node)
        time.sleep(2)  # Allow time for leader election and log replay
        
        # Verify messages persisted
        client = Client()
        client.connect()
        chat_history = client.get_chat_history()
        
        for msg in test_messages:
            self.assertIn(msg, [m.content for m in chat_history.messages],
                         f"Message not found after restart: {msg}")
        
        client.disconnect()

if __name__ == '__main__':
    unittest.main()
