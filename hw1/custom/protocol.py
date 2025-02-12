import json
import enum
from datetime import datetime
from typing import Optional, Dict, List, Any, Union
import logging
import struct
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_protocol")

# Define mappings from our string values to compact numeric codes.
MESSAGE_TYPE_CODES = {
    "create_account": 0,
    "login": 1,
    "list_accounts": 2,
    "delete_account": 3,
    "logout": 4,
    "send_message": 5,
    "get_messages": 6,
    "delete_messages": 7,
    "broadcast": 8,
    "mark_as_read": 9,
    "error": 10,
    "ack": 11
}

STATUS_CODE_VALUES = {
    "success": 0,
    "error": 1,
    "pending": 2
}

MESSAGE_TYPE_FROM_CODE = {v: k for k, v in MESSAGE_TYPE_CODES.items()}
STATUS_CODE_FROM_VALUE = {v: k for k, v in STATUS_CODE_VALUES.items()}


class MessageType(enum.Enum):
    # Authentication
    CREATE_ACCOUNT = "create_account"
    LOGIN = "login"
    
    # Account Management
    LIST_ACCOUNTS = "list_accounts"
    DELETE_ACCOUNT = "delete_account"
    LOGOUT = "logout"
    
    # Messaging
    SEND_MESSAGE = "send_message"
    GET_MESSAGES = "get_messages"
    DELETE_MESSAGES = "delete_messages"
    BROADCAST = "broadcast"
    MARK_AS_READ = "mark_as_read"
    
    # System
    ERROR = "error"
    ACK = "ack"


class StatusCode(enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

def encode_data(data: dict) -> bytes:
    """
    Encode the data dictionary into a compact string.
    Each key-value pair is encoded as key=value and pairs are separated by commas.
    For list values, join the items with a semicolon.
    (This is a simple encoding for demonstration purposes.)
    """
    parts = []
    for key, value in data.items():
        if isinstance(value, list):
            value_str = ";".join(str(item) for item in value)
        else:
            value_str = str(value)
        parts.append(f"{key}={value_str}")
    encoded_str = ",".join(parts)
    return encoded_str.encode('utf-8')

def decode_data(data_bytes: bytes) -> dict:
    """
    Decode the custom-encoded data.
    """
    decoded_str = data_bytes.decode('utf-8')
    data = {}
    if decoded_str:
        pairs = decoded_str.split(',')
        for pair in pairs:
            if '=' in pair:
                key, value_str = pair.split('=', 1)
                # If the value contains a semicolon, assume it was a list.
                if ';' in value_str:
                    value = value_str.split(';')
                else:
                    value = value_str
                data[key] = value
    return data

def create_message_custom(
    msg_type: enum.Enum, 
    data: dict, 
    status: enum.Enum = StatusCode.PENDING
) -> bytes:
    """
    Create a message in our custom binary format.
    The message layout is:
      [1 byte msg_type][1 byte status][8 byte timestamp][4 byte payload length][payload]
    """
    msg_type_code = MESSAGE_TYPE_CODES[msg_type.value]
    status_code = STATUS_CODE_VALUES[status.value]
    timestamp = time.time()  # seconds since epoch as float
    data_bytes = encode_data(data)
    data_length = len(data_bytes)
    # Pack header in network byte order: two unsigned chars, one double, one unsigned int.
    header = struct.pack("!BBdI", msg_type_code, status_code, timestamp, data_length)
    return header + data_bytes

def send_custom(sock, msg: bytes) -> None:
    """
    Send a custom binary message over the socket.
    """
    try:
        sock.sendall(msg)
        logger.debug("Custom message sent successfully")
    except Exception as e:
        logger.error(f"Error sending custom message: {e}")
        raise

def recv_custom(sock) -> dict:
    """
    Receive a custom binary message from the socket.
    First read the fixed header (14 bytes) then the payload.
    Returns a dictionary with these keys:
      {
        "type": <string>,
        "status": <string>,
        "timestamp": <float>,
        "data": <dict>
      }
    """
    try:
        # Read the 14-byte header.
        header = b""
        while len(header) < 14:
            chunk = sock.recv(14 - len(header))
            if not chunk:
                return None  # Connection closed.
            header += chunk
        
        msg_type_code, status_code, timestamp, data_length = struct.unpack("!BBdI", header)
        
        # Now read the payload.
        data_bytes = b""
        while len(data_bytes) < data_length:
            chunk = sock.recv(data_length - len(data_bytes))
            if not chunk:
                break
            data_bytes += chunk
        if len(data_bytes) != data_length:
            raise ValueError("Incomplete data payload")
        
        data = decode_data(data_bytes)
        message = {
            "type": MESSAGE_TYPE_FROM_CODE.get(msg_type_code, "unknown"),
            "status": STATUS_CODE_FROM_VALUE.get(status_code, "unknown"),
            "timestamp": timestamp,
            "data": data
        }
        return message
    except Exception as e:
        logger.error(f"Error receiving custom message: {e}")
        raise

def validate_message(message: Dict[str, Any]) -> bool:
    """
    Validate that a message has all required fields and correct format.
    Not always used, but can be helpful if you want to ensure structure.
    """
    logger.debug(f"Validating message: {message}")
    
    required_fields = {"type", "data", "timestamp", "status"}
    
    # Check all required fields exist
    if not all(field in message for field in required_fields):
        logger.error(f"Message missing required fields. Required: {required_fields}, Got: {message.keys()}")
        return False
    
    # Validate message type
    try:
        MessageType(message["type"])
    except ValueError:
        logger.error(f"Invalid message type: {message['type']}")
        return False
    
    # Validate status
    try:
        StatusCode(message["status"])
    except ValueError:
        logger.error(f"Invalid status code: {message['status']}")
        return False
    
    # Validate data is dict
    if not isinstance(message["data"], dict):
        logger.error(f"Data must be a dictionary, got: {type(message['data'])}")
        return False
    
    logger.debug("Message validation successful")
    return True

#
# Helper functions that now also return raw bytes
#
def create_error(msg: str) -> bytes:
    """
    Create an error message as raw bytes.
    """
    logger.debug(f"Creating error message: {msg}")
    return create_message_custom(
        MessageType.ERROR,
        {"message": msg},
        StatusCode.ERROR
    )

def create_ack(message_id: str) -> bytes:
    """
    Create an acknowledgment message as raw bytes.
    """
    logger.debug(f"Creating acknowledgment message for message_id: {message_id}")
    return create_message_custom(
        MessageType.ACK,
        {"message_id": message_id},
        StatusCode.SUCCESS
    )
