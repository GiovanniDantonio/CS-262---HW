"""
Unit tests for the Raft consensus module.
Tests leader election, log replication, and persistence capabilities.
"""
import os
import sys
import unittest
import tempfile
import shutil
import time
import threading
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.raft import RaftNode, LogEntry
from common.persistence import PersistentState

class TestRaftConsensus(unittest.TestCase):
    """Test cases for the Raft consensus algorithm implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for persistent storage
        self.temp_dirs = [tempfile.mkdtemp() for _ in range(3)]
        
        # Create mock RPCs
        self.mock_rpcs = {}
        
        # Create nodes
        self.nodes = []
        for i, temp_dir in enumerate(self.temp_dirs):
            node_id = f"node{i+1}"
            peers = {f"node{j+1}": f"localhost:{8000+j+1}" 
                     for j in range(3) if j != i}
            
            node = RaftNode(
                server_id=node_id,
                peers=peers,
                persistent_state=PersistentState(temp_dir),
                apply_command_callback=self._mock_apply_command
            )
            
            # Patch RPCs
            self._patch_node_rpcs(node)
            
            self.nodes.append(node)
    
    def tearDown(self):
        """Clean up test environment."""
        # Stop nodes
        for node in self.nodes:
            node.stop()
        
        # Remove temporary directories
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir)
    
    def _mock_apply_command(self, command):
        """Mock callback for applying commands."""
        return True
    
    def _patch_node_rpcs(self, node):
        """Patch RPC methods to simulate network communications."""
        # Store original methods
        self.mock_rpcs[node.server_id] = {
            "request_vote": node._send_request_vote_rpc,
            "append_entries": node._send_append_entries_rpc
        }
        
        # Patch methods to route calls to other nodes
        def mock_request_vote(target_id, request):
            target_node = next((n for n in self.nodes if n.server_id == target_id), None)
            if not target_node:
                return {"term": node.current_term, "vote_granted": False}
            return target_node.on_request_vote_received(request)
        
        def mock_append_entries(target_id, request):
            target_node = next((n for n in self.nodes if n.server_id == target_id), None)
            if not target_node:
                return {"term": node.current_term, "success": False}
            return target_node.on_append_entries_received(request)
        
        # Apply patches
        node._send_request_vote_rpc = mock_request_vote
        node._send_append_entries_rpc = mock_append_entries
    
    def test_initial_state(self):
        """Test that nodes initialize with correct state."""
        for node in self.nodes:
            # All nodes should start as followers
            self.assertEqual(node.state, "follower")
            
            # Initial term should be 0
            self.assertEqual(node.current_term, 0)
            
            # No votes granted initially
            self.assertIsNone(node.voted_for)
            
            # Empty log initially
            self.assertEqual(len(node.log), 0)
    
    def test_single_leader_election(self):
        """Test that a single leader is elected."""
        # Start nodes
        for node in self.nodes:
            node.start()
        
        # Wait for leader election
        time.sleep(3)
        
        # Count leaders
        leaders = [node for node in self.nodes if node.state == "leader"]
        
        # There should be exactly one leader
        self.assertEqual(len(leaders), 1)
        
        # All nodes should be in the same term
        leader_term = leaders[0].current_term
        for node in self.nodes:
            self.assertEqual(node.current_term, leader_term)
    
    def test_log_replication(self):
        """Test that log entries are replicated to followers."""
        # Start nodes
        for node in self.nodes:
            node.start()
        
        # Wait for leader election
        time.sleep(3)
        
        # Find leader
        leader = next((node for node in self.nodes if node.state == "leader"), None)
        self.assertIsNotNone(leader)
        
        # Submit commands to the leader
        commands = [{"op": "set", "key": f"key{i}", "value": f"value{i}"} for i in range(5)]
        for command in commands:
            result = leader.submit_command(command)
            self.assertTrue(result["success"])
        
        # Wait for replication
        time.sleep(3)
        
        # Get followers
        followers = [node for node in self.nodes if node.state == "follower"]
        
        # Verify all nodes have the same log entries
        for i, entry in enumerate(leader.log):
            for follower in followers:
                if i < len(follower.log):
                    self.assertEqual(follower.log[i].command, entry.command)
                    self.assertEqual(follower.log[i].term, entry.term)
    
    def test_persistence(self):
        """Test that node state is persisted and recoverable."""
        # Start nodes
        for node in self.nodes:
            node.start()
        
        # Wait for leader election
        time.sleep(3)
        
        # Find leader
        leader = next((node for node in self.nodes if node.state == "leader"), None)
        self.assertIsNotNone(leader)
        
        # Submit commands to the leader
        commands = [{"op": "set", "key": f"key{i}", "value": f"value{i}"} for i in range(5)]
        for command in commands:
            leader.submit_command(command)
        
        # Wait for replication
        time.sleep(3)
        
        # Get a follower node
        follower = next((node for node in self.nodes if node.state == "follower"), None)
        self.assertIsNotNone(follower)
        
        # Record follower state
        original_term = follower.current_term
        original_log = follower.log.copy()
        
        # Stop the follower
        follower.stop()
        
        # Create a new node with the same ID and storage
        node_idx = self.nodes.index(follower)
        temp_dir = self.temp_dirs[node_idx]
        
        # Replace the node
        new_node = RaftNode(
            server_id=follower.server_id,
            peers=follower.peers,
            persistent_state=PersistentState(temp_dir),
            apply_command_callback=self._mock_apply_command
        )
        
        # Patch RPCs
        self._patch_node_rpcs(new_node)
        
        # Replace in the list
        self.nodes[node_idx] = new_node
        
        # Verify state was recovered
        self.assertEqual(new_node.current_term, original_term)
        self.assertEqual(len(new_node.log), len(original_log))
        
        for i, entry in enumerate(original_log):
            self.assertEqual(new_node.log[i].command, entry.command)
            self.assertEqual(new_node.log[i].term, entry.term)
    
    def test_leader_failure(self):
        """Test that a new leader is elected when the current leader fails."""
        # Start nodes
        for node in self.nodes:
            node.start()
        
        # Wait for leader election
        time.sleep(3)
        
        # Find leader
        old_leader = next((node for node in self.nodes if node.state == "leader"), None)
        self.assertIsNotNone(old_leader)
        
        # Record current term
        original_term = old_leader.current_term
        
        # Stop the leader
        old_leader.stop()
        
        # Wait for new leader election
        time.sleep(3)
        
        # Find new leader among remaining nodes
        active_nodes = [node for node in self.nodes if node != old_leader]
        new_leader = next((node for node in active_nodes if node.state == "leader"), None)
        
        # There should be a new leader
        self.assertIsNotNone(new_leader)
        
        # Term should have increased
        self.assertGreater(new_leader.current_term, original_term)

if __name__ == '__main__':
    unittest.main()
