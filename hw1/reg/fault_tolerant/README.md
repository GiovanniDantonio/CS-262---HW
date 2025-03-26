# Fault-Tolerant Chat System

This is a fault-tolerant implementation of the chat system that can handle up to 2 node failures while maintaining data consistency and availability.

## Architecture

The system uses a leader-follower replication model based on the Raft consensus algorithm. Key features:

1. **Fault Tolerance**:
   - 3-node cluster that can tolerate 2 node failures
   - Automatic leader election when leader fails
   - Automatic client redirection to current leader
   - Persistent message storage across node restarts

2. **Consistency**:
   - Strong consistency through leader-based replication
   - All writes go through the leader
   - Majority consensus required for leader election
   - Log replication ensures all nodes have the same state

3. **High Availability**:
   - Automatic failover to new leader
   - Clients automatically reconnect to available nodes
   - No single point of failure

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the cluster:
   - Edit `cluster_config.json` to specify node addresses and ports
   - Default configuration runs 3 nodes on localhost with different ports

3. Start the nodes:
```bash
# Start node 1 (in terminal 1)
python -m reg.fault_tolerant.node.server 1

# Start node 2 (in terminal 2)
python -m reg.fault_tolerant.node.server 2

# Start node 3 (in terminal 3)
python -m reg.fault_tolerant.node.server 3
```

4. Start the client:
```bash
python -m reg.fault_tolerant.client.client
```

## Testing Fault Tolerance

1. **Node Failure Test**:
   - Start all 3 nodes
   - Create accounts and send messages
   - Kill the leader node (the client will tell you which node is leader)
   - Verify that a new leader is elected
   - Verify that clients can still send/receive messages
   - Verify that all messages sent before the failure are preserved

2. **Multiple Node Failure Test**:
   - Start all 3 nodes
   - Send some messages
   - Kill 2 non-leader nodes
   - Verify that the system continues to work
   - Verify that all messages are preserved
   - Start the failed nodes and verify they catch up

3. **Network Partition Test**:
   - Start all 3 nodes
   - Create a network partition that isolates one node
   - Verify that the majority partition continues to work
   - Heal the partition and verify the isolated node catches up

4. **Data Persistence Test**:
   - Start all 3 nodes
   - Send messages
   - Stop all nodes
   - Start nodes again
   - Verify all messages are preserved

## Implementation Details

1. **Node Server (`node/server.py`)**:
   - Implements the Raft consensus algorithm
   - Handles client connections and requests
   - Manages state replication
   - Provides automatic failover

2. **State Machine (`node/state_machine.py`)**:
   - Implements the replicated state machine
   - Manages Raft protocol
   - Handles log replication and persistence

3. **Client (`client/client.py`)**:
   - Provides fault-tolerant client interface
   - Automatically handles node failures and leader changes
   - Retries operations when nodes fail
   - Maintains session across reconnections

4. **Protocol (`common/protocol.py`)**:
   - Defines message types and formats
   - Handles message serialization
   - Provides reliable message transport

## Engineering Decisions

1. **Why Raft?**
   - Simpler to understand and implement than Paxos
   - Strong leader-based approach fits chat system well
   - Built-in membership changes
   - Clear failure handling semantics

2. **Why SQLite?**
   - Simple embedded database
   - ACID compliance
   - No external dependencies
   - Easy backup and recovery

3. **Failure Detection**
   - Heartbeat-based failure detection
   - Configurable timeouts
   - Quick leader election
   - Automatic client failover

4. **Data Consistency**
   - Strong consistency through leader
   - Majority writes for durability
   - Log-based replication for reliability
   - Atomic operations for message delivery

## Testing

Run the test suite:
```bash
python -m pytest reg/fault_tolerant/tests/
```

The tests cover:
1. Node failure and recovery
2. Leader election
3. Log replication
4. Client failover
5. Data persistence
6. Network partitions
7. Message ordering and delivery
