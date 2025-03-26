# Distributed Fault-Tolerant Chat System

This is a redesigned chat application that provides both persistence and 2-fault tolerance in the face of crash/failstop failures. The system uses a consensus algorithm based on Raft to replicate the chat state across multiple server nodes.

## Features

- **Persistence**: All chat data is stored in SQLite databases and persists across server restarts
- **2-Fault Tolerance**: The system continues to operate correctly even if 2 out of 3 nodes fail
- **Leader Election**: Automatic leader election ensures there's always a single source of truth
- **Transparent Failover**: Clients automatically reconnect to available servers when failures occur
- **Cross-Machine Replication**: Support for running nodes on different physical machines
- **Dynamic Server Addition**: Support for adding new servers to the cluster while it's running

## Architecture

The system follows a leader-follower architecture:

1. **Server Nodes**: Each node has its own local SQLite database and can operate in one of three states:
   - Leader: Accepts write operations and replicates them to followers
   - Follower: Accepts read operations and forwards write operations to the leader
   - Candidate: Temporary state during leader election

2. **Consensus Protocol**: Implements a simplified Raft consensus algorithm:
   - Log replication ensures all nodes maintain the same state
   - Leader election ensures there's always a single leader
   - Majority voting guarantees consistency

3. **Client Design**: The client is fault-tolerant and automatically:
   - Handles server failures by reconnecting to other available servers
   - Discovers the current leader for write operations
   - Streams messages in real-time

## Setup and Running

### Prerequisites

- Python 3.6+
- Required packages listed in `requirements.txt`

### Running the Server Nodes

Start at least 3 nodes to achieve 2-fault tolerance:

```bash
# Start node 1 (in terminal 1)
python server.py --id 1 --config config.yaml

# Start node 2 (in terminal 2)
python server.py --id 2 --config config.yaml

# Start node 3 (in terminal 3)
python server.py --id 3 --config config.yaml
```

### Running the Client

```bash
# Connect to any of the server nodes
python client.py
```

The client will automatically discover other nodes and connect to the leader when needed.

## Testing Fault Tolerance

To test fault tolerance, you can:

1. Start 3 server nodes
2. Connect a client and register/login
3. Send some messages
4. Stop 1 or 2 server nodes (including the leader)
5. Continue using the client - it should reconnect automatically
6. Verify that messages sent before the failure are still available
7. Verify that you can send new messages (as long as a majority of nodes are still available)

## Multi-Machine Setup

To run the system across multiple machines:

1. Update the `config.yaml` file with the actual hostnames or IP addresses of each machine
2. Ensure all machines can reach each other over the network
3. Start the nodes on their respective machines using the same configuration

Example configuration for multiple machines:

```yaml
nodes:
  - id: "1"
    host: "192.168.1.101"  # First machine's IP
    port: 50051
    db_path: "node_1.db"
  
  - id: "2"
    host: "192.168.1.102"  # Second machine's IP
    port: 50051
    db_path: "node_1.db"
  
  - id: "3"
    host: "192.168.1.103"  # Third machine's IP
    port: 50051
    db_path: "node_1.db"
```

## Implementation Details

### Server Components

- `node.py`: Core node implementation with Raft consensus logic
- `chat_service.py`: Handles client-server communication
- `replication_service.py`: Handles server-server communication
- `server.py`: Entry point for starting a server node

### Client Components

- `client.py`: Fault-tolerant client implementation with GUI

### Communication

- gRPC for all communication (client-server and server-server)
- Protocol Buffers for message serialization

## Dynamic Server Addition

The system supports adding new servers to the cluster while it's running. This is done through a two-phase process:

1. **Non-Voting Member Phase**: The new server is first added as a non-voting member
   - Receives log entries and updates but doesn't participate in leader election
   - Catches up with the current state of the cluster

2. **Promotion Phase**: Once caught up, the server is promoted to a full voting member
   - Participates in leader election and consensus
   - Counts towards the quorum for write operations

### Adding a New Server

```bash
# Add a new server to the cluster
python add_server.py <leader_address> <new_server_id> <new_server_address>

# Example:
python add_server.py localhost:50051 4 localhost:50054
```

The script will:
1. Contact the leader to add the new server
2. Wait for the new server to catch up with the log
3. Promote the server to a voting member

## Limitations and Future Improvements

- Currently implements a simplified version of the Raft consensus algorithm
- No automatic log compaction/snapshotting
- Simplified security (no encryption, authentication beyond username/password)
- No support for removing servers from the cluster

## Acknowledgements

This implementation is based on the principles described in the Raft consensus algorithm paper:
"In Search of an Understandable Consensus Algorithm" by Diego Ongaro and John Ousterhout.
