#!/usr/bin/env python3

import timeit
import sys
import builtins
import json
import ast

# Import JSON-based protocol
from reg.protocol import (
    create_message as json_create_message,
    validate_message as json_validate_message,
    MessageType as JsonMessageType
)

# Import Custom-based protocol
from custom.protocol import (
    create_message as custom_create_message,
    validate_message as custom_validate_message,
    MessageType as CustomMessageType
)

# -------------------------------
# Define a sample message object
# -------------------------------
sample_message = {
    "type": "login",
    "data": {
        "username": "testuser",
        "password": "hashed_password_example"
    },
    "timestamp": "2025-02-12T12:00:00",
    "status": "pending"
}

# -----------------------------------------
# JSON Serialization/Deserialization
# -----------------------------------------
def json_serialize(message: dict) -> str:
    """
    1) Use the JSON protocol's create_message to build a dict.
    2) Convert it to a JSON string.
    """
    msg_dict = json_create_message(JsonMessageType.LOGIN, message)
    return json.dumps(msg_dict)

def json_deserialize(msg_str: str) -> dict:
    """
    1) Convert the JSON string back to a dict.
    2) Optionally validate the dict using the JSON protocol.
    """
    msg_dict = json.loads(msg_str)
    json_validate_message(msg_dict)
    return msg_dict

# -----------------------------------------------
# Custom Serialization/Deserialization
# -----------------------------------------------
def custom_serialize(message: dict) -> str:
    """
    1) Use the custom protocol's create_message to build a dict.
    2) Convert it to a plain string (str(...) of the dict).
    """
    msg_dict = custom_create_message(CustomMessageType.LOGIN, message)
    return str(msg_dict)

def custom_deserialize(msg_str: str) -> dict:
    """
    1) Convert the string back to a dict using ast.literal_eval.
    2) Optionally validate the dict using the custom protocol.
    """
    msg_dict = ast.literal_eval(msg_str)
    custom_validate_message(msg_dict)
    return msg_dict

# -------------------------------------------------
# Serialize sample message with both approaches
# -------------------------------------------------
json_serialized = json_serialize(sample_message)
custom_serialized = custom_serialize(sample_message)

print("Serialized message sizes:")
print("  JSON size:   ", len(json_serialized), "characters")
print("  Custom size: ", len(custom_serialized), "characters")

# -------------------------------------------------
# Benchmark Serialization Performance
# -------------------------------------------------
iterations = 100

json_serialize_time = timeit.timeit(
    lambda: json_serialize(sample_message), 
    number=iterations
)
custom_serialize_time = timeit.timeit(
    lambda: custom_serialize(sample_message), 
    number=iterations
)

print("\nSerialization performance over", iterations, "iterations:")
print("  JSON serialize time:   {:.4f} seconds".format(json_serialize_time))
print("  Custom serialize time: {:.4f} seconds".format(custom_serialize_time))

# -------------------------------------------------
# Benchmark Deserialization Performance
# -------------------------------------------------
json_deserialize_time = timeit.timeit(
    lambda: json_deserialize(json_serialized),
    number=iterations
)
custom_deserialize_time = timeit.timeit(
    lambda: custom_deserialize(custom_serialized),
    number=iterations
)

print("\nDeserialization performance over", iterations, "iterations:")
print("  JSON deserialize time:   {:.4f} seconds".format(json_deserialize_time))
print("  Custom deserialize time: {:.4f} seconds".format(custom_deserialize_time))
