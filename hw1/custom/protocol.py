import enum
import logging
import struct
import time
from typing import Any, Dict

# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_protocol")

# -----------------------------------------------------------------------------
# Message type and status code mappings
# -----------------------------------------------------------------------------
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
    CREATE_ACCOUNT = "create_account"
    LOGIN = "login"
    LIST_ACCOUNTS = "list_accounts"
    DELETE_ACCOUNT = "delete_account"
    LOGOUT = "logout"
    SEND_MESSAGE = "send_message"
    GET_MESSAGES = "get_messages"
    DELETE_MESSAGES = "delete_messages"
    BROADCAST = "broadcast"
    MARK_AS_READ = "mark_as_read"
    ERROR = "error"
    ACK = "ack"

class StatusCode(enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

# -----------------------------------------------------------------------------
# Custom encoding/decoding with distinct delimiters
# -----------------------------------------------------------------------------
# We use:
#   - "D|" to mark dictionaries. Dictionary pairs are separated by '^'.
#     Each pair is: key=encoded_value.
#   - "L|" to mark lists. List items are separated by '~'.
#   - "S|" to mark scalars.
DICT_PAIR_DELIM = "^"
LIST_ITEM_DELIM = "~"

def encode_obj(obj: Any) -> str:
    """
    Recursively encode a Python object (dict, list, or scalar) as a string with type markers.
    
    Examples:
      - A dictionary: {"username": "anais", "roles": ["admin", "user"]}
        becomes: 
          "D|username=S|anais^roles=L|S|admin~S|user"
      - A list: ["hello", {"foo": "bar"}]
        becomes:
          "L|S|hello~D|foo=S|bar"
      - A scalar: "example" becomes "S|example"
    """
    if isinstance(obj, dict):
        parts = []
        for key, val in obj.items():
            encoded_val = encode_obj(val)
            parts.append(f"{key}={encoded_val}")
        return "D|" + DICT_PAIR_DELIM.join(parts)
    elif isinstance(obj, list):
        encoded_items = [encode_obj(item) for item in obj]
        return "L|" + LIST_ITEM_DELIM.join(encoded_items)
    else:
        # For scalars, simply prefix with "S|"
        return f"S|{obj}"

def decode_obj(encoded: str) -> Any:
    """
    Recursively decode a string with type markers into the original Python object.
    """
    if encoded.startswith("D|"):
        content = encoded[2:]  # Remove "D|"
        if not content:
            return {}
        pairs = content.split(DICT_PAIR_DELIM)
        result = {}
        for pair in pairs:
            if "=" in pair:
                key, enc_val = pair.split("=", 1)
                result[key] = decode_obj(enc_val)
        return result
    elif encoded.startswith("L|"):
        content = encoded[2:]  # Remove "L|"
        if not content:
            return []
        items = content.split(LIST_ITEM_DELIM)
        return [decode_obj(item) for item in items]
    elif encoded.startswith("S|"):
        return encoded[2:]  # Return scalar value (as string)
    else:
        # Fallback: if no marker, return the string as is
        return encoded

def encode_data(data: Dict) -> bytes:
    """
    Encode the top-level dictionary into a string using our custom encoding and return UTF-8 bytes.
    
    The format is simply the encoded object.
    """
    encoded_str = encode_obj(data)
    return encoded_str.encode('utf-8')

def decode_data(data_bytes: bytes) -> Dict:
    """
    Decode the given bytes (UTF-8) back into a Python dictionary.
    
    If the top-level object is not a dict, it is wrapped into one with the key "data".
    """
    decoded_str = data_bytes.decode('utf-8')
    obj = decode_obj(decoded_str)
    if isinstance(obj, dict):
        return obj
    else:
        logger.warning("Decoded top-level object is not a dict; wrapping it.")
        return {"data": obj}

# -----------------------------------------------------------------------------
# Message framing: packing and unpacking a binary header and payload
# -----------------------------------------------------------------------------
def create_message_custom(
    msg_type: enum.Enum,
    data: Dict,
    status: enum.Enum = StatusCode.PENDING
) -> bytes:
    """
    Create a custom binary message with the following layout:
      [1 byte msg_type][1 byte status][8 byte timestamp][4 byte payload length][payload bytes]
    
    - msg_type and status are encoded as 1-byte numbers.
    - timestamp is a double (8 bytes) using time.time().
    - payload is the encoded data (using encode_data).
    """
    msg_type_code = MESSAGE_TYPE_CODES[msg_type.value]
    status_code = STATUS_CODE_VALUES[status.value]
    timestamp = time.time()
    data_bytes = encode_data(data)
    data_length = len(data_bytes)
    
    # Pack header in network byte order: B, B, d, I = 1-byte, 1-byte, 8-byte double, 4-byte unsigned int.
    header = struct.pack("!BBdI", msg_type_code, status_code, timestamp, data_length)
    return header + data_bytes

def send_custom(sock, msg: bytes) -> None:
    """
    Send the custom binary message over the given socket.
    """
    try:
        sock.sendall(msg)
        logger.debug("Custom message sent successfully")
    except Exception as e:
        logger.error(f"Error sending custom message: {e}")
        raise

def recv_custom(sock) -> Dict:
    """
    Receive a custom binary message from the socket.
    
    It reads:
      - A fixed 14-byte header ([msg_type:1][status:1][timestamp:8][payload_length:4])
      - Then reads the specified payload length.
    
    Returns a dictionary with keys:
      "type": string message type,
      "status": string status,
      "timestamp": float timestamp,
      "data": decoded dictionary payload.
    
    Returns None if the connection is closed.
    """
    try:
        header = b""
        while len(header) < 14:
            chunk = sock.recv(14 - len(header))
            if not chunk:
                return None  # Connection closed
            header += chunk
        
        msg_type_code, status_code, timestamp, data_length = struct.unpack("!BBdI", header)
        
        data_bytes = b""
        while len(data_bytes) < data_length:
            chunk = sock.recv(data_length - len(data_bytes))
            if not chunk:
                break
            data_bytes += chunk
        
        if len(data_bytes) != data_length:
            raise ValueError(f"Incomplete data payload: expected {data_length}, got {len(data_bytes)}")
        
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

# -----------------------------------------------------------------------------
# Optional: Message validation and helper functions
# -----------------------------------------------------------------------------
def validate_message(message: Dict) -> bool:
    """
    Validate that the message has all required fields: "type", "status", "timestamp", and "data".
    Also, ensure that the type and status are recognized.
    """
    logger.debug(f"Validating message: {message}")
    required_fields = {"type", "status", "timestamp", "data"}
    if not all(field in message for field in required_fields):
        logger.error(f"Message missing required fields. Required: {required_fields}, got: {message.keys()}")
        return False

    if message["type"] not in MESSAGE_TYPE_CODES:
        logger.error(f"Invalid message type: {message['type']}")
        return False

    if message["status"] not in STATUS_CODE_VALUES:
        logger.error(f"Invalid status code: {message['status']}")
        return False

    if not isinstance(message["data"], dict):
        logger.error(f"Data must be a dictionary, got: {type(message['data'])}")
        return False

    logger.debug("Message validation successful")
    return True

def create_error(msg: str) -> bytes:
    """
    Create an error message (of type ERROR) as raw bytes.
    """
    logger.debug(f"Creating error message: {msg}")
    return create_message_custom(
        MessageType.ERROR,
        {"message": msg},
        StatusCode.ERROR
    )

def create_ack(message_id: str) -> bytes:
    """
    Create an acknowledgment message (of type ACK) as raw bytes.
    """
    logger.debug(f"Creating ACK message for message_id: {message_id}")
    return create_message_custom(
        MessageType.ACK,
        {"message_id": message_id},
        StatusCode.SUCCESS
    )
