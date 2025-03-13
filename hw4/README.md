# Fault-Tolerant Chat System

A distributed, fault-tolerant chat system that implements the Raft consensus algorithm for reliability and consistency across multiple nodes.

## Features

- **Fault Tolerance**: Continues operating even when some servers fail
- **Consistency**: Ensures all servers have the same data using Raft consensus
- **Persistence**: Stores messages and state to disk for durability
- **Automatic Failover**: Clients automatically reconnect to available servers
- **Server Replication**: Supports multiple server instances in a cluster
- **User Authentication**: Supports user registration, login, and account management

## Architecture

The system is built using the following components:

1. **Raft Consensus Module**: Implements leader election, log replication, and cluster membership
2. **Persistence Layer**: Handles durable storage of logs, state, and snapshots
3. **gRPC Services**: Provides client-server and server-server communication
4. **Client Library**: Manages connections, retries, and automatic failover
5. **Command-Line Interface**: Provides a user interface for interacting with the system

## Directory Structure

```
fault_tolerant_chat/
├── client/           # Client implementation
│   ├── client.py     # Client library for application integration
│   └── cli_client.py # Command-line interface
├── common/           # Shared modules
│   ├── persistence.py # Persistence and storage
│   └── raft.py       # Raft consensus implementation
├── proto/            # Protocol buffer definitions
│   └── chat.proto    # Service and message definitions
├── server/           # Server implementation
│   ├── server.py     # Main server class
│   ├── server_handlers.py # Request handlers
│   └── run_server.py # Server launcher script
└── tests/            # Unit and integration tests
    ├── test_raft.py  # Tests for Raft consensus
    └── test_client.py # Tests for client functionality
```

## Getting Started

### Prerequisites

- Python 3.7+
- gRPC and Protocol Buffers

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install grpcio grpcio-tools protobuf
```

3. Generate gRPC code from protocol buffers:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. fault_tolerant_chat/proto/chat.proto
```

### Running a Server Cluster

1. Start the first server (as the leader):

```bash
python fault_tolerant_chat/server/run_server.py --id server1 --port 8001 --data-dir ./data/server1
```

2. Start additional servers (joining the leader):

```bash
python fault_tolerant_chat/server/run_server.py --id server2 --port 8002 --data-dir ./data/server2 --join localhost:8001
python fault_tolerant_chat/server/run_server.py --id server3 --port 8003 --data-dir ./data/server3 --join localhost:8001
```

Alternatively, you can use a configuration file:

```bash
python fault_tolerant_chat/server/run_server.py --id server1 --port 8001 --data-dir ./data/server1 --config-file cluster_config.json
```

Where `cluster_config.json` contains:

```json
{
  "servers": {
    "server1": "localhost:8001",
    "server2": "localhost:8002",
    "server3": "localhost:8003"
  }
}
```

### Using the CLI Client

Connect to the server cluster:

```bash
python fault_tolerant_chat/client/cli_client.py --servers localhost:8001,localhost:8002,localhost:8003
```

The CLI supports commands like:
- `register <username> <password>` - Register a new user
- `login <username> <password>` - Log in to the chat system
- `send <recipient> <message>` - Send a message
- `messages [count]` - List received messages
- `status` - Show cluster status
- `help` - Show available commands

## Raft Consensus Details

The implementation follows the Raft paper with:

1. **Leader Election**:
   - Timeout-based leader election
   - Randomized election timeouts to avoid split votes
   - Term-based voting to ensure safety

2. **Log Replication**:
   - Append-only log structure
   - Leader-driven replication
   - Commit index tracking

3. **Cluster Membership**:
   - Single-server changes for safety
   - Joint consensus for configuration changes

## Fault Tolerance Capabilities

The system can handle:

1. **Server Failures**:
   - Automatic leader election when leader fails
   - Clients automatically reconnect to available servers
   - Log replication ensures no data loss

2. **Network Partitions**:
   - Raft guarantees safety under network partitions
   - Only the majority partition can make progress

3. **Process Crashes**:
   - Persistent storage enables recovery after crashes
   - Log replay brings servers back to consistent state

## Running Tests

Execute the unit tests:

```bash
python -m unittest discover fault_tolerant_chat/tests
```

## Implementation Notes

- Built on gRPC for efficient bi-directional streaming
- Uses Protocol Buffers for serialization
- All modifications to the chat state go through the Raft log for consistency
- Message delivery uses at-least-once semantics with client-side deduplication
