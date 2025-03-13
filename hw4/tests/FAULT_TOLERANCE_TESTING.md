# Fault Tolerance Testing Guide

This document provides instructions for testing the fault tolerance capabilities of our chat system across multiple machines. These tests will verify that the system meets the requirements of being persistent and 2-fault tolerant in the face of crash/failstop failures.

## Test Requirements

The fault tolerance tests will verify that:

1. **Persistence**: Messages are not lost when servers are restarted
2. **2-Fault Tolerance**: The system continues to operate correctly when up to 2 servers fail
3. **Leader Election**: A new leader is automatically elected when the current leader fails
4. **Data Consistency**: All servers maintain consistent data through the Raft consensus
5. **Client Failover**: Clients automatically reconnect to available servers

## Setup for Multi-Machine Testing

### Prerequisites

- At least 3 machines (ideally 5 for proper testing of 2-fault tolerance)
- Python 3.7+ installed on all machines
- Network connectivity between all machines
- Clone of the repository on each machine

### Machine Configuration

1. **Choose Machine Roles**:
   - **Machine A**: Primary node + Test coordinator
   - **Machine B**: Secondary node
   - **Machine C**: Tertiary node
   - Additional machines (if available): Additional nodes

2. **Network Configuration**:
   - Ensure all machines can reach each other on the network
   - Note down the IP addresses of all machines

## Running Tests

### Automatic Testing

We've provided an automated test script that simulates failures and verifies system behavior:

```bash
# On Machine A (coordinator)
python tests/fault_tolerance_test.py --servers 5 --base-port 8001
```

This will:
1. Start a cluster of 5 server instances
2. Register test users
3. Test basic functionality
4. Test leader failure recovery
5. Test multiple server failure recovery
6. Test persistence across restarts
7. Test behavior when quorum is lost

### Manual Cross-Machine Testing

For testing across multiple physical machines:

#### 1. Start the Server Cluster

**On Machine A** (Start the first server as the leader):
```bash
python server/run_server.py --id server1 --host <MACHINE_A_IP> --port 8001 --data-dir ./data/server1
```

**On Machine B** (Join the cluster):
```bash
python server/run_server.py --id server2 --host <MACHINE_B_IP> --port 8001 --data-dir ./data/server2 --join <MACHINE_A_IP>:8001
```

**On Machine C** (Join the cluster):
```bash
python server/run_server.py --id server3 --host <MACHINE_C_IP> --port 8001 --data-dir ./data/server3 --join <MACHINE_A_IP>:8001
```

Repeat for additional machines if available.

#### 2. Connect a Test Client

**On any machine**:
```bash
python client/cli_client.py --servers <MACHINE_A_IP>:8001,<MACHINE_B_IP>:8001,<MACHINE_C_IP>:8001
```

#### 3. Manual Testing Procedure

1. **Initial State Test**:
   - Register a few test users: `register user1 password1`
   - Login as a test user: `login user1 password1`
   - Send some test messages: `send user2 "Test message 1"`
   - Verify messages are received: `messages`

2. **Leader Failure Test**:
   - Check cluster status to identify the leader: `status`
   - Kill the leader process on its machine (Ctrl+C or `kill` command)
   - Verify a new leader is elected: `status` (after a few seconds)
   - Send new messages and verify they're processed

3. **Two-Node Failure Test**:
   - Kill two non-leader nodes
   - Verify the system continues to function
   - Send and receive messages

4. **Persistence Test**:
   - Send some uniquely identifiable messages
   - Restart all servers one by one
   - Verify the messages are still available after restart

5. **Network Partition Test**:
   - Create a network partition by blocking communication between sets of servers
   - Verify that only the majority partition makes progress
   - Restore network connectivity and verify the system recovers

6. **New Server Addition Test** (Extra Credit):
   - Start a new server and join it to the cluster
   - Verify it receives all data and participates in consensus

## Test Scenarios and Expected Results

### Scenario 1: Single Server Failure

**Test Steps**:
1. Start a 5-node cluster
2. Identify the leader node
3. Kill the leader node
4. Attempt operations from a client

**Expected Results**:
- A new leader should be elected within a few seconds
- Client operations should continue to work after a brief pause
- No data should be lost

### Scenario 2: Two Server Failures

**Test Steps**:
1. Start a 5-node cluster
2. Kill any two nodes (can include the leader)
3. Attempt operations from a client

**Expected Results**:
- If the leader was killed, a new one should be elected
- Client operations should continue to work
- No data should be lost
- The system should maintain consensus with 3 remaining nodes

### Scenario 3: Majority Failure (3/5 Nodes)

**Test Steps**:
1. Start a 5-node cluster
2. Kill any three nodes
3. Attempt operations from a client

**Expected Results**:
- The system should become unavailable for write operations
- Read operations that don't require consensus may still work
- When nodes are restored, the system should recover and continue operation

### Scenario 4: Persistence Test

**Test Steps**:
1. Start a 5-node cluster
2. Send several messages through clients
3. Stop all servers
4. Restart all servers
5. Check if messages are still available

**Expected Results**:
- All messages sent before the restart should be available after restart
- The cluster should re-establish itself with the same state
- A leader should be elected and the system should resume normal operation

## Common Issues and Troubleshooting

1. **Network Configuration**:
   - Ensure all machines can reach each other on the specified ports
   - Check firewall settings on all machines

2. **Data Directory Permissions**:
   - Ensure the data directories are writable by the server process

3. **Process Management**:
   - For long-running tests, consider using `nohup` or a terminal multiplexer like `tmux` or `screen` to keep processes running

4. **Log Files**:
   - Check server logs for any errors or warnings
   - Increase logging level for debugging: add `--log-level debug` to server commands

## Analyzing Test Results

After running the tests, analyze the results to verify that the system meets the requirements:

1. **Persistence**: Were all messages preserved across server restarts?
2. **Fault Tolerance**: Did the system continue to operate with up to 2 server failures?
3. **Consistency**: Were all clients able to see the same state of the system?
4. **Performance**: What was the impact on response time during failure scenarios?

Document any issues or edge cases discovered during testing for future improvements.
