#!/usr/bin/env python3

import timeit
import json
import sys
import logging
from google.protobuf import json_format
from reg.chat_pb2 import Message as GrpcMessage
from reg.protocol import create_message, MessageType, StatusCode

# Disable debug logging
logging.getLogger("chat_protocol").setLevel(logging.WARNING)

# Sample message that matches both JSON and gRPC structure
sample_data = {
    "id": 1,
    "sender": "alice",
    "recipient": "bob",
    "content": "Hello, how are you?",
    "timestamp": "2025-02-22T20:42:12",
    "read": False
}

def create_grpc_message(data):
    """Create a gRPC message from dictionary data"""
    message = GrpcMessage()
    return json_format.Parse(json.dumps(data), message)

def create_json_message(data):
    """Create a JSON message from dictionary data"""
    return create_message(MessageType.SEND_MESSAGE, data)

# Create messages once for size comparison
grpc_message = create_grpc_message(sample_data)
json_message = create_json_message(sample_data)

# Size comparison
grpc_size = len(grpc_message.SerializeToString())
json_size = len(json.dumps(json_message).encode())

print("Message Size Comparison:")
print(f"gRPC size: {grpc_size} bytes")
print(f"JSON size: {json_size} bytes")
print(f"Size difference: {abs(grpc_size - json_size)} bytes")
if grpc_size < json_size:
    print(f"gRPC is {(json_size/grpc_size - 1)*100:.1f}% smaller than JSON\n")
else:
    print(f"JSON is {(grpc_size/json_size - 1)*100:.1f}% smaller than gRPC\n")

# Performance benchmarking
iterations = [100, 1000, 10000]

print("Performance Benchmarking:")
print("------------------------")

for n in iterations:
    print(f"\nIterations: {n}")
    
    # gRPC serialization
    grpc_serialize_time = timeit.timeit(
        lambda: create_grpc_message(sample_data).SerializeToString(),
        number=n
    )
    
    # gRPC deserialization
    serialized_grpc = grpc_message.SerializeToString()
    grpc_deserialize_time = timeit.timeit(
        lambda: GrpcMessage().ParseFromString(serialized_grpc),
        number=n
    )
    
    # JSON serialization
    json_serialize_time = timeit.timeit(
        lambda: json.dumps(create_json_message(sample_data)),
        number=n
    )
    
    # JSON deserialization
    serialized_json = json.dumps(json_message)
    json_deserialize_time = timeit.timeit(
        lambda: json.loads(serialized_json),
        number=n
    )
    
    print(f"gRPC Serialization:   {grpc_serialize_time:.4f} seconds")
    print(f"gRPC Deserialization: {grpc_deserialize_time:.4f} seconds")
    print(f"JSON Serialization:   {json_serialize_time:.4f} seconds")
    print(f"JSON Deserialization: {json_deserialize_time:.4f} seconds")
