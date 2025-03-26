#!/usr/bin/env python3
"""
Script to demonstrate dynamic server addition in the distributed chat system.
This script allows adding a new server to an existing cluster.
"""
import os
import sys
import time
import grpc
import logging
import argparse

# Import the generated protobuf modules
from distributed_chat import distributed_chat_pb2 as pb2
from distributed_chat import distributed_chat_pb2_grpc as pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("add_server")

def add_server(leader_address, server_id, server_address):
    """
    Add a new server to the cluster.
    
    Args:
        leader_address: Address of the current leader node
        server_id: ID for the new server
        server_address: Address of the new server
    """
    try:
        # Connect to leader
        channel = grpc.insecure_channel(leader_address)
        stub = pb2_grpc.ReplicationServiceStub(channel)
        
        # Request to add server
        request = pb2.AddServerRequest(
            server_id=server_id,
            server_address=server_address
        )
        
        logger.info(f"Requesting to add server {server_id} at {server_address}")
        response = stub.AddServer(request)
        
        if not response.success:
            if response.leader_id and response.leader_address:
                logger.info(f"Redirecting to leader: {response.leader_address}")
                return add_server(response.leader_address, server_id, server_address)
            else:
                logger.error(f"Failed to add server: {response.message}")
                return False
        
        logger.info("Server added as non-voting member")
        
        # Start catchup process
        while True:
            catchup_request = pb2.CatchupRequest(
                server_id=server_id,
                last_log_index=0  # Start from beginning
            )
            
            catchup_response = stub.CatchupServer(catchup_request)
            if not catchup_response.success:
                logger.error(f"Catchup failed: {catchup_response.message}")
                return False
            
            if not catchup_response.entries:
                # No more entries needed, ready for promotion
                break
            
            logger.info(f"Received {len(catchup_response.entries)} log entries")
            time.sleep(1)  # Wait before next catchup request
        
        # Request promotion to voting member
        promote_request = pb2.PromoteServerRequest(server_id=server_id)
        promote_response = stub.PromoteServer(promote_request)
        
        if promote_response.success:
            logger.info("Server successfully promoted to voting member")
            return True
        else:
            logger.error(f"Promotion failed: {promote_response.message}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding server: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Add a new server to the chat cluster")
    parser.add_argument("leader_address", help="Address of the current leader node")
    parser.add_argument("server_id", help="ID for the new server")
    parser.add_argument("server_address", help="Address of the new server")
    
    args = parser.parse_args()
    
    if add_server(args.leader_address, args.server_id, args.server_address):
        print("Server successfully added to cluster")
        sys.exit(0)
    else:
        print("Failed to add server to cluster")
        sys.exit(1)

if __name__ == "__main__":
    main()
