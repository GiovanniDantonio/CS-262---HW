#!/usr/bin/env python3
"""
Test suite for client resilience in the distributed chat system.
Tests client's ability to maintain service during node failures.
"""
import unittest
import time
import logging
import os
import sys
from concurrent import futures

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
distributed_chat_dir = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, distributed_chat_dir)

from distributed_chat.node import Node
from distributed_chat.client import Client

class TestClientResilience(unittest.TestCase):
    """Test suite for client resilience scenarios."""

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

    def test_client_connect_to_available_node(self):
        """
        Test that client can connect to available nodes when some are down.
        Steps:
        1. Stop one node
        2. Verify client can still connect and send messages
        3. Stop another node (maintaining quorum)
        4. Verify client still functions
        """
        # Initial connection test
        client = Client()
        self.assertTrue(client.connect(), "Failed to connect initially")
        
        # Stop first node
        self.nodes[0].stop()
        time.sleep(2)
        
        # Test client can still connect and send messages
        response = client.send_message("Test message after first node failure")
        self.assertTrue(response.success, "Failed to send message after first node failure")
        
        # Stop second node (still maintaining quorum with 1 node)
        self.nodes[1].stop()
        time.sleep(2)
        
        # Test client can still function with only one node
        response = client.send_message("Test message with minimum quorum")
        self.assertTrue(response.success, "Failed to send message with minimum quorum")
        
        client.disconnect()

if __name__ == '__main__':
    unittest.main()
