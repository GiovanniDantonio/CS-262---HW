# Distributed Chat Application

A fault-tolerant, distributed chat application built with gRPC and Python. The system supports multiple chat servers with automatic failover and message persistence.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- tkinter (usually comes with Python installation)

## Setup Instructions

1. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install grpcio grpcio-tools
   ```

## Running the Application

### 1. Start the Server Replicas

Start three server replicas in separate terminal windows:

```bash
# Terminal 1 - Start Replica 0 (Primary)
python3 server.py --replica-id 0

# Terminal 2 - Start Replica 1
python3 server.py --replica-id 1

# Terminal 3 - Start Replica 2
python3 server.py --replica-id 2
```

The servers will start on the following ports:
- Replica 0: localhost:50051
- Replica 1: localhost:50052
- Replica 2: localhost:50053

### 2. Start the Chat Client

In a new terminal window:
```bash
python3 client.py
```

This will open the chat application GUI.

## Using the Chat Application

1. **Register a New Account**:
   - Enter a username and password
   - Click "Register"

2. **Login**:
   - Enter your credentials
   - Click "Login"

3. **Send Messages**:
   - Enter recipient's username in the "To:" field
   - Type your message
   - Click "Send"

4. **View Messages**:
   - Messages appear in the main chat display
   - Unread messages are highlighted
   - Click a message to mark it as read

5. **Other Features**:
   - Refresh user list to see online users
   - Delete selected messages
   - Logout when done
   - Delete account if needed

## Fault Tolerance Features

The system is designed to be 2-fault tolerant:
- Can continue operating with up to 2 server failures
- Messages are persisted across server restarts
- Automatic failover to available replicas
- Automatic leader election when primary fails

## Testing Fault Tolerance

1. Start all three replicas and the client
2. Try killing any two replicas (Ctrl+C in their terminal windows)
3. The system will continue to work with the remaining replica
4. Restart the killed replicas to see them rejoin the cluster

## Troubleshooting

1. If you see "Address already in use":
   ```bash
   # Check for existing Python processes
   ps aux | grep python
   # Kill the specific process
   kill <process_id>
   ```

2. If client can't connect:
   - Ensure at least one server replica is running
   - Check that you're using the correct port (50051, 50052, or 50053)
   - Make sure you're in the virtual environment
