import json
import enum
from datetime import datetime
from typing import Optional, Dict, List, Any, Union
import logging
import ast

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_protocol")

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


def create_message(msg_type: MessageType, data: Dict[str, Any], status: StatusCode = StatusCode.PENDING) -> Dict[str, Any]:
    """Create a properly formatted message with the given type and data."""
    logger.debug(f"Creating message of type {msg_type.value} with data: {data}")
    message = {
        "type": msg_type.value,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "status": status.value
    }
    logger.debug(f"Created message: {message}")
    return message


def validate_message(message: Dict[str, Any]) -> bool:
    """Validate that a message has all required fields and correct format."""
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


def send_custom(sock, obj: Dict[str, Any]) -> Optional[str]:
    try:
        logger.debug(f"Attempting to send message: {obj}")
        if not validate_message(obj):
            raise ValueError("Invalid message format")
        # Convert the object to its string representation
        msg = str(obj) + "\n"
        sock.sendall(msg.encode('utf-8'))
        logger.debug("Message sent successfully")
        return None
    except Exception as e:
        error_msg = f"Error sending message: {e}"
        logger.error(error_msg)
        return error_msg


def recv_custom(sock) -> Union[Dict[str, Any], str, None]:
    try:
        logger.debug("Attempting to receive message")
        f = sock.makefile('r')
        line = f.readline()
        if not line:
            logger.warning("Received empty line")
            return None
        logger.debug(f"Received raw message: {line}")
        # Convert the string representation back to a Python object
        message = ast.literal_eval(line)
        if not validate_message(message):
            raise ValueError("Received invalid message format")
        logger.debug(f"Successfully received and validated message: {message}")
        return message
    except Exception as e:
        error_msg = f"Error receiving message: {e}"
        logger.error(error_msg)
        return error_msg


# Helper functions for common message creation
def create_error(message: str) -> Dict[str, Any]:
    """Create an error message."""
    logger.debug(f"Creating error message: {message}")
    return create_message(
        MessageType.ERROR,
        {"message": message},
        StatusCode.ERROR
    )


def create_ack(message_id: str) -> Dict[str, Any]:
    """Create an acknowledgment message."""
    logger.debug(f"Creating acknowledgment message for message_id: {message_id}")
    return create_message(
        MessageType.ACK,
        {"message_id": message_id},
        StatusCode.SUCCESS
    )
