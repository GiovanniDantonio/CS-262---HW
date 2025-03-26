"""
Tests for fault tolerance in the chat system.
"""
import os
import pytest
import shutil
import socket
import threading
import time
from typing import List, Tuple

from ..client.client import ChatClient
from ..node.server import NodeServer

# Test configuration
TEST_CONFIG = {
    "nodes": [
        {
            "id": 1,
            "host": "localhost",
            "port": 12345,
            "data_dir": "test_node1_data"
        },
        {
            "id": 2,
            "host": "localhost",
            "port": 12346,
            "data_dir": "test_node2_data"
        },
        {
            "id": 3,
            "host": "localhost",
            "port": 12347,
            "data_dir": "test_node3_data"
        }
    ],
    "election_timeout_ms": 150,
    "heartbeat_interval_ms": 50,
    "client_retry_interval_ms": 100,
    "max_batch_size": 100
}

@pytest.fixture(scope="function")
def cluster():
    """Create a test cluster."""
    # Create test config
    config_path = "test_cluster_config.json"
    with open(config_path, "w") as f:
        json.dump(TEST_CONFIG, f)
    
    # Create nodes
    nodes = []
    for node_config in TEST_CONFIG["nodes"]:
        # Clean data directory
        if os.path.exists(node_config["data_dir"]):
            shutil.rmtree(node_config["data_dir"])
        os.makedirs(node_config["data_dir"])
        
        # Create node
        node = NodeServer(node_config["id"], config_path)
        node.start()
        nodes.append(node)
    
    # Wait for leader election
    time.sleep(0.5)
    
    yield nodes
    
    # Cleanup
    for node in nodes:
        node.stop()
    
    os.remove(config_path)
    for node_config in TEST_CONFIG["nodes"]:
        if os.path.exists(node_config["data_dir"]):
            shutil.rmtree(node_config["data_dir"])

@pytest.fixture(scope="function")
def client(cluster):
    """Create a test client."""
    config_path = "test_cluster_config.json"
    client = ChatClient(config_path)
    assert client.connect()
    
    yield client
    
    client.disconnect()

def test_leader_failure(cluster, client):
    """Test that system continues working when leader fails."""
    # Create test accounts
    assert client.create_account("user1", "pass1")
    assert client.create_account("user2", "pass2")
    
    # Send some messages
    client.login("user1", "pass1")
    assert client.send_message("user2", "Hello before failure")
    
    # Find and stop leader
    leader = None
    for node in cluster:
        if node.state_machine.role == NodeRole.LEADER:
            leader = node
            break
    assert leader is not None
    
    # Stop leader
    leader.stop()
    
    # Wait for new leader election
    time.sleep(0.5)
    
    # System should continue working
    assert client.send_message("user2", "Hello after failure")
    
    # Check messages are preserved
    client.login("user2", "pass2")
    messages = client.get_messages()
    assert len(messages) == 2
    assert any(m["content"] == "Hello before failure" for m in messages)
    assert any(m["content"] == "Hello after failure" for m in messages)

def test_client_connect_to_available_node(cluster, client):
    """Test that client can connect to any available node."""
    # Create test account
    assert client.create_account("user1", "pass1")
    
    # Stop nodes one by one, client should stay connected
    for i in range(len(cluster) - 1):
        # Stop a non-leader node
        non_leader = None
        for node in cluster:
            if node.state_machine.role != NodeRole.LEADER:
                non_leader = node
                break
        assert non_leader is not None
        
        non_leader.stop()
        time.sleep(0.5)
        
        # Client should still work
        assert client.send_message("user1", f"Message after stop {i}")

def test_data_persistence_across_restarts(cluster, client):
    """Test that data persists across node restarts."""
    # Create test accounts and messages
    assert client.create_account("user1", "pass1")
    assert client.create_account("user2", "pass2")
    
    client.login("user1", "pass1")
    assert client.send_message("user2", "Hello before restart")
    
    # Stop all nodes
    for node in cluster:
        node.stop()
    
    # Start nodes again
    for i, node_config in enumerate(TEST_CONFIG["nodes"]):
        cluster[i] = NodeServer(node_config["id"], "test_cluster_config.json")
        cluster[i].start()
    
    # Wait for leader election
    time.sleep(0.5)
    
    # Reconnect client
    client.reconnect()
    
    # Check data persisted
    client.login("user2", "pass2")
    messages = client.get_messages()
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello before restart"

def test_concurrent_client_operations(cluster):
    """Test concurrent client operations during node failures."""
    def client_worker(client_id: int) -> List[str]:
        """Worker function for concurrent clients."""
        messages_sent = []
        
        client = ChatClient("test_cluster_config.json")
        assert client.connect()
        
        username = f"user{client_id}"
        password = f"pass{client_id}"
        
        try:
            # Create account and login
            assert client.create_account(username, password)
            assert client.login(username, password)
            
            # Send messages
            for i in range(5):
                msg = f"Message {i} from {username}"
                if client.send_message("user0", msg):
                    messages_sent.append(msg)
                time.sleep(0.1)
        
        finally:
            client.disconnect()
        
        return messages_sent
    
    # Create main user
    client = ChatClient("test_cluster_config.json")
    assert client.connect()
    assert client.create_account("user0", "pass0")
    client.disconnect()
    
    # Start concurrent clients
    threads = []
    results = []
    for i in range(1, 4):
        result = []
        results.append(result)
        thread = threading.Thread(target=lambda: result.extend(client_worker(i)))
        threads.append(thread)
        thread.start()
    
    # Simulate node failures
    time.sleep(0.5)
    for node in cluster[:-1]:  # Keep at least one node alive
        if node.state_machine.role != NodeRole.LEADER:
            node.stop()
            time.sleep(0.5)
    
    # Wait for clients to finish
    for thread in threads:
        thread.join()
    
    # Verify messages
    client = ChatClient("test_cluster_config.json")
    assert client.connect()
    assert client.login("user0", "pass0")
    
    messages = client.get_messages()
    sent_messages = [msg for result in results for msg in result]
    
    assert len(messages) == len(sent_messages)
    for sent in sent_messages:
        assert any(m["content"] == sent for m in messages)
