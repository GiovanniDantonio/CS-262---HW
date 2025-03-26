"""
Protocol definitions for fault-tolerant chat system.
"""
import enum
import json
import socket
import struct
from typing import Dict, Optional

class MessageType(enum.Enum):
    """Message types for client-server and node-node communication."""
    # Client-server messages
    CREATE_ACCOUNT = 1
    LOGIN = 2
    LOGOUT = 3
    DELETE_ACCOUNT = 4
    LIST_ACCOUNTS = 5
    SEND_MESSAGE = 6
    GET_MESSAGES = 7
    DELETE_MESSAGES = 8
    MARK_AS_READ = 9
    RESPONSE = 10
    ACK = 11
    # BROADCAST = 12
    
    # Node-node messages (Raft protocol)
    REQUEST_VOTE = 20
    REQUEST_VOTE_RESPONSE = 21
    APPEND_ENTRIES = 22
    APPEND_ENTRIES_RESPONSE = 23

class NodeRole(enum.Enum):
    """Node roles in Raft protocol."""
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3

class StatusCode(enum.Enum):
    """Status codes for responses."""
    SUCCESS = 1
    ERROR = 2
    REDIRECT = 3

def create_message(msg_type: MessageType, data: Dict) -> Dict:
    """Create a message dictionary."""
    return {
        "type": msg_type.name,
        "data": data
    }

def send_json(sock: socket.socket, data: Dict) -> None:
    """Send JSON data over a socket."""
    try:
        # Convert data to JSON string
        json_str = json.dumps(data)
        json_bytes = json_str.encode()
        
        # Send length as 4-byte integer
        length = len(json_bytes)
        sock.sendall(struct.pack('!I', length))
        
        # Send JSON data
        sock.sendall(json_bytes)
        
    except Exception as e:
        raise ConnectionError(f"Error sending JSON: {e}")

def receive_json(sock: socket.socket) -> Optional[Dict]:
    """Receive JSON data from a socket."""
    try:
        # Read length (4 bytes)
        length_bytes = sock.recv(4)
        if not length_bytes or len(length_bytes) != 4:
            return None
        
        length = struct.unpack('!I', length_bytes)[0]
        
        # Read JSON data
        data = bytearray()
        while len(data) < length:
            chunk = sock.recv(min(4096, length - len(data)))
            if not chunk:
                return None
            data.extend(chunk)
        
        # Parse JSON
        return json.loads(data.decode())
        
    except Exception as e:
        raise ConnectionError(f"Error receiving JSON: {e}")
