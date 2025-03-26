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
cd distributed_chat
python3 distributed_chat_pb2.py
```

### Running a Server Cluster

1. Start the first server (as the leader):

```bash
python server.py --id 1 --config config.yaml
```

2. Start additional servers (joining the leader):

```bash
python server.py --id 2 --config config.yaml
python server.py --id 3 --config config.yaml
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

Connect to the server cluster:

```bash
python client/cli_client.py --servers localhost:8001,localhost:8002,localhost:8003
```

The CLI supports commands like:
- `register <username> <password>` - Register a new user
- `login <username> <password>` - Log in to the chat system
- `send <recipient> <message>` - Send a message
- `messages [count]` - List received messages
- `status` - Show cluster status
- `help` - Show available commands

We implement a consensus module that follows this format:

1. **Leader Election**:
   - Timeout-based leader election. We use a random timeout to avoid split votes.
   - As indicated above, we use randomized election timeouts to avoid split votes.
   - Term-based voting to ensure safety.

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

Execute the unit tests:

```bash
python -m unittest discover tests
```

## Implementation Notes

- We used gRPC for efficient bi-directional streaming.
- We used Protocol Buffers for serialization. This is like JSON, but smaller and faster.
- All modifications to the chat state go through the log to ensure consistency.
- Message delivery uses at-least-once semantics with client-side deduplication.