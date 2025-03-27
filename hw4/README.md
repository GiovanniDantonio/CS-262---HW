# Fault-Tolerant Chat System

A distributed, fault-tolerant chat system that implements reliability and consistency across multiple nodes.

## Features

- **2-Fault Tolerance**: Continues operating even when two or more servers fail.
- **Consistency**: Ensures all servers have the same data.
- **Persistence**: Stores messages and state to disk for durability.
- **Automatic Failover**: Clients automatically reconnect to available servers.
- **Server Replication**: Supports multiple server instances in a cluster.
- **User Authentication**: Supports user registration, login, and account management.

## Architecture

The system is built using the following components:

1. **Consensus Module**: Implements leader election, log replication, and cluster membership.
2. **Persistence Layer**: Handles durable storage of logs, state, and snapshots.
3. **gRPC Services**: Provides client-server and server-server communication. This was implemented using the `grpc` library. Also, we used the `grpc_tools.protoc` to generate the gRPC code from the `chat.proto` file. Furthermore, we took our code from the previous homework.
4. **Client Library**: Manages connections, retries, and automatic failover.
5. **Command-Line Interface**: Provides a user interface for interacting with the system.

## Directory Structure

```
hw4/
├── distributed_chat/     # Main distributed chat implementation
│   ├── server.py        # Server implementation with Raft consensus
│   ├── node.py          # Node implementation for distributed system
│   ├── client.py        # Client implementation
│   └── distributed_chat.proto  # Protocol buffer definitions
├── reg/                 # Registration and authentication service
│   ├── server.py        # Authentication server
│   ├── client.py        # Client for auth service
│   ├── chat.proto       # Auth service protocol definitions
│   └── tests/           # Test suite
│       ├── test_client.py    # Client tests
│       ├── test_db.py        # Database tests
│       ├── test_protocol.py  # Protocol tests
│       └── test_server.py    # Server tests
└── requirements.txt     # Project dependencies
```

### Prerequisites

- Python 3.7+
- gRPC and Protocol Buffers

### Installation

1. Clone the repository
2. Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure you are already cded in the hw4 folder and then generate gRPC code from protocol buffers:

```bash
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/chat.proto
```

### Running a Server Cluster

1. Start the first server:

```bash
python3 server.py --replica-id 1
```

2. Start additional servers (joining the leader):

```bash
source venv/bin/activate && cd reg && python3 server.py --replica-id 2
source venv/bin/activate && cd reg && python3 client.py
source ../venv/bin/activate && python3 server.py --replica-id 0
```

Alternatively, you can use a configuration file:

```bash
python server/run_server.py --id server1 --port 8001 --data-dir ./data/server1 --config-file cluster_config.json
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

We implement a consensus module that follows this format:

1. **Leader Election**:
   - Highest id wins.

2. **Log Replication**:
   - Append-only log structure.
   - Leader-driven replication.
   - Commit index tracking.

3. **Cluster Membership**:
   - Single-server changes for safety. This means that we only allow a single server to change the state of the cluster.
   - Joint consensus for configuration changes. Thus, the joint consensus works by having a majority of the servers agree on the new configuration.

## Fault Tolerance Capabilities

The system can handle:

1. **Server Failures**:
   - Automatic leader election when leader fails.
   - Clients automatically reconnect to available servers.
   - Log replication ensures no data loss. Since logs are replicated to all servers, we can recover from a server failure by having the other servers replicate the log to the new server.

2. **Network Partitions**:
   - Only the majority partition can make progress.

3. **Process Crashes**:
   - Persistent storage enables recovery after crashes.
   - Log replay brings servers back to consistent state.

## Running Tests

To run the test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python -m pytest reg/tests/

# Run specific test files
python -m pytest reg/tests/test_client.py
python -m pytest reg/tests/test_server.py
python -m pytest reg/tests/test_protocol.py
python -m pytest reg/tests/test_db.py

# Run tests with verbose output
python -m pytest -v reg/tests/

# Run tests and show coverage
python -m pytest --cov=reg reg/tests/
```

The test suite includes:
- Client functionality tests (authentication, message sending)
- Server functionality tests (request handling, state management)
- Database tests (persistence, data integrity)
- Protocol tests (message serialization, protocol compliance)

## Implementation Notes

- We used gRPC for efficient bi-directional streaming.
- We used Protocol Buffers for serialization. This is like JSON, but smaller and faster.
- All modifications to the chat state go through the log to ensure consistency.
- Message delivery uses at-least-once semantics with client-side deduplication.
