#!/usr/bin/env python3
"""
Test suite for node failure scenarios in the distributed chat system.
Tests leader failure recovery and node rejoin mechanisms.
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

class TestNodeFailures(unittest.TestCase):
    """Test suite for node failure scenarios."""

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

    def test_leader_failure(self):
        """
        Test that the system can recover from a leader failure.
        Steps:
        1. Identify current leader
        2. Stop the leader node
        3. Verify new leader is elected
        4. Verify system continues to function
        """
        # Find current leader
        leader = None
        for node in self.nodes:
            if node.is_leader():
                leader = node
                break
        
        self.assertIsNotNone(leader, "No leader found")
        leader_id = leader.node_id

        # Stop the leader
        leader.stop()
        time.sleep(3)  # Allow time for new leader election

        # Verify new leader is elected
        new_leader = None
        for node in self.nodes:
            if node.node_id != leader_id and node.is_leader():
                new_leader = node
                break

        self.assertIsNotNone(new_leader, "No new leader elected after failure")
        self.assertNotEqual(new_leader.node_id, leader_id, "Old leader still marked as leader")

        # Test system functionality
        client = Client()
        client.connect()
        response = client.send_message("Test message after leader failure")
        self.assertTrue(response.success, "Failed to send message after leader failure")
        client.disconnect()

if __name__ == '__main__':
    unittest.main()
