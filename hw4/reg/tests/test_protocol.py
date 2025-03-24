import unittest
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol import MessageType, StatusCode, create_message, validate_message

class TestProtocol(unittest.TestCase):
    def test_create_message_basic(self):
        """Test basic message creation with minimal required fields."""
        data = {"username": "testuser"}
        message = create_message(MessageType.LOGIN, data)
        
        # Check required fields are present
        self.assertIn("type", message)
        self.assertIn("data", message)
        self.assertIn("timestamp", message)
        self.assertIn("status", message)
        
        # Check values are correctly set
        self.assertEqual(message["type"], MessageType.LOGIN.value)
        self.assertEqual(message["data"], data)
        self.assertEqual(message["status"], StatusCode.PENDING.value)
        # Also check that the timestamp is a valid ISO string.
        try:
            datetime.fromisoformat(message["timestamp"])
        except ValueError:
            self.fail("Timestamp is not in valid ISO format.")

    def test_validate_message_valid(self):
        """Test validation of a properly formatted message."""
        message = {
            "type": MessageType.LOGIN.value,
            "data": {"username": "testuser"},
            "timestamp": datetime.utcnow().isoformat(),
            "status": StatusCode.PENDING.value
        }
        self.assertTrue(validate_message(message))

    def test_validate_message_invalid_missing_field(self):
        """Test validation fails when a required field is missing."""
        message = {
            "type": MessageType.LOGIN.value,
            "data": {"username": "testuser"},
            # Missing timestamp field
            "status": StatusCode.PENDING.value
        }
        self.assertFalse(validate_message(message))

    def test_validate_message_invalid_type(self):
        """Test validation fails with an invalid message type."""
        message = {
            "type": "invalid_type",
            "data": {"username": "testuser"},
            "timestamp": datetime.utcnow().isoformat(),
            "status": StatusCode.PENDING.value
        }
        self.assertFalse(validate_message(message))

    def test_validate_message_invalid_status(self):
        """Test validation fails with an invalid status code."""
        message = {
            "type": MessageType.LOGIN.value,
            "data": {"username": "testuser"},
            "timestamp": datetime.utcnow().isoformat(),
            "status": "invalid_status"
        }
        self.assertFalse(validate_message(message))

if __name__ == '__main__':
    unittest.main()
