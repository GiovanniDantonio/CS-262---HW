import unittest
import socket
import json
import threading
import time
from datetime import datetime
import sys
import os

# Add parent directory to path to import protocol
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import protocol
from protocol import MessageType, StatusCode

class TestProtocol(unittest.TestCase):
    """Test suite for the protocol module."""
    
    def setUp(self):
        """Set up any necessary test fixtures."""
        # Create a pair of connected sockets for testing
        self.server_socket, self.client_socket = socket.socketpair()
    
    def tearDown(self):
        """Clean up after each test."""
        self.server_socket.close()
        self.client_socket.close()

    # Smoke Tests
    def test_create_basic_message(self):
        """Smoke test: Can we create a basic valid message?"""
        message = protocol.create_message(
            MessageType.LOGIN,
            {"username": "test", "password": "test"}
        )
        self.assertTrue(protocol.validate_message(message))
        self.assertEqual(message["type"], MessageType.LOGIN.value)
        self.assertEqual(message["status"], StatusCode.PENDING.value)

    def test_send_receive_basic_message(self):
        """Smoke test: Can we send and receive a basic message?"""
        test_message = protocol.create_message(
            MessageType.LOGIN,
            {"username": "test"}
        )
        
        # Send message
        protocol.send_json(self.client_socket, test_message)
        
        # Receive message
        received = protocol.recv_json(self.server_socket)
        
        self.assertEqual(test_message["type"], received["type"])
        self.assertEqual(test_message["data"], received["data"])

    # Boundary Tests
    def test_empty_data(self):
        """Boundary test: Empty data dictionary."""
        message = protocol.create_message(MessageType.ACK, {})
        self.assertTrue(protocol.validate_message(message))

    def test_large_message(self):
        """Boundary test: Large message payload."""
        large_data = {"content": "x" * 1000000}  # 1MB of data
        message = protocol.create_message(MessageType.SEND_MESSAGE, large_data)
        
        # Send and receive large message
        protocol.send_json(self.client_socket, message)
        received = protocol.recv_json(self.server_socket)
        
        self.assertEqual(message["data"], received["data"])

    def test_invalid_messages(self):
        """Boundary test: Various invalid message formats."""
        invalid_messages = [
            {},  # Empty message
            {"type": "LOGIN"},  # Missing required fields
            {"type": "INVALID", "data": {}, "timestamp": "", "status": ""},  # Invalid type
            {"type": "LOGIN", "data": "not_a_dict", "timestamp": "", "status": ""},  # Invalid data type
        ]
        
        for msg in invalid_messages:
            self.assertFalse(protocol.validate_message(msg))

    # Thorough Tests
    def test_all_message_types(self):
        """Test creating and validating all possible message types."""
        test_data = {"test": "data"}
        for msg_type in MessageType:
            message = protocol.create_message(msg_type, test_data)
            self.assertTrue(protocol.validate_message(message))
            self.assertEqual(message["type"], msg_type.value)

    def test_all_status_codes(self):
        """Test all possible status codes."""
        test_data = {"test": "data"}
        for status in StatusCode:
            message = protocol.create_message(
                MessageType.ACK,
                test_data,
                status=status
            )
            self.assertTrue(protocol.validate_message(message))
            self.assertEqual(message["status"], status.value)

    def test_concurrent_messages(self):
        """Test sending/receiving multiple messages concurrently."""
        message_count = 100
        received_messages = []
        send_errors = []
        receive_errors = []
        
        def send_messages():
            try:
                for i in range(message_count):
                    msg = protocol.create_message(
                        MessageType.SEND_MESSAGE,
                        {"content": f"message_{i}"}
                    )
                    protocol.send_json(self.client_socket, msg)
                    time.sleep(0.001)  # Small delay to simulate real conditions
            except Exception as e:
                send_errors.append(e)
        
        def receive_messages():
            try:
                for _ in range(message_count):
                    msg = protocol.recv_json(self.server_socket)
                    if msg:
                        received_messages.append(msg)
            except Exception as e:
                receive_errors.append(e)
        
        # Start concurrent send/receive
        send_thread = threading.Thread(target=send_messages)
        receive_thread = threading.Thread(target=receive_messages)
        
        send_thread.start()
        receive_thread.start()
        
        send_thread.join()
        receive_thread.join()
        
        # Verify results
        self.assertEqual(len(send_errors), 0, f"Send errors: {send_errors}")
        self.assertEqual(len(receive_errors), 0, f"Receive errors: {receive_errors}")
        self.assertEqual(len(received_messages), message_count)

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test sending to closed socket
        self.client_socket.close()
        result = protocol.send_json(self.client_socket, 
                                  protocol.create_message(MessageType.ACK, {}))
        self.assertTrue(isinstance(result, str))
        self.assertTrue("Error" in result)

    # Performance Tests
    def test_message_throughput(self):
        """Measure message throughput."""
        message_count = 1000
        start_time = time.time()
        
        # Send messages
        for i in range(message_count):
            msg = protocol.create_message(
                MessageType.SEND_MESSAGE,
                {"content": f"message_{i}"}
            )
            protocol.send_json(self.client_socket, msg)
        
        # Receive messages
        received = 0
        while received < message_count:
            msg = protocol.recv_json(self.server_socket)
            if msg:
                received += 1
        
        duration = time.time() - start_time
        throughput = message_count / duration
        
        print(f"\nThroughput: {throughput:.2f} messages/second")
        self.assertTrue(throughput > 0)

    def test_message_latency(self):
        """Measure message latency."""
        latencies = []
        test_iterations = 100
        
        for _ in range(test_iterations):
            start_time = time.time()
            
            # Send and receive a message
            msg = protocol.create_message(
                MessageType.SEND_MESSAGE,
                {"content": "test"}
            )
            protocol.send_json(self.client_socket, msg)
            protocol.recv_json(self.server_socket)
            
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        print(f"\nAverage latency: {avg_latency:.2f}ms")
        self.assertTrue(avg_latency > 0)

if __name__ == '__main__':
    unittest.main()
