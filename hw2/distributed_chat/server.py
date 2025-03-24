"""
Server startup script for distributed chat system.
This script creates and runs a chat server node that can participate
in the distributed consensus protocol.

Usage:
    python server.py --id <node_id> --host <host> --port <port> [--config <config_file>]
"""
import os
import sys
import time
import yaml
import json
import logging
import argparse
import threading
import grpc
from concurrent import futures

# Import the generated protobuf modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from distributed_chat import distributed_chat_pb2 as pb2
from distributed_chat import distributed_chat_pb2_grpc as pb2_grpc
from distributed_chat.node import ChatNode
from distributed_chat.chat_service import ChatService
from distributed_chat.replication_service import ReplicationService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("chat_server")

def load_config(config_file, node_id=None):
    """
    Load configuration from YAML file.
    
    Args:
        config_file: Path to configuration file
        node_id: Optional node ID to filter configuration
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # If node_id is specified, get only that node's config
        if node_id and 'nodes' in config:
            for node_config in config['nodes']:
                if node_config['id'] == node_id:
                    return node_config
            raise ValueError(f"Node ID {node_id} not found in config")
        
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        if node_id:
            # Return minimal default config for the specified node
            return {
                'id': node_id,
                'host': 'localhost',
                'port': 50051 + int(node_id),
                'db_path': f'node_{node_id}.db'
            }
        else:
            # Return minimal default config
            return {
                'nodes': [
                    {'id': '1', 'host': 'localhost', 'port': 50051, 'db_path': 'node_1.db'},
                    {'id': '2', 'host': 'localhost', 'port': 50052, 'db_path': 'node_2.db'},
                    {'id': '3', 'host': 'localhost', 'port': 50053, 'db_path': 'node_3.db'},
                ]
            }

def get_peer_addresses(config, current_node_id):
    """
    Extract peer addresses from configuration.
    
    Args:
        config: Configuration dictionary with 'nodes' list
        current_node_id: ID of the current node
        
    Returns:
        dict: Dictionary of peer_id -> host:port
    """
    peers = {}
    for node in config['nodes']:
        node_id = node['id']
        if node_id != current_node_id:
            peers[node_id] = f"{node['host']}:{node['port']}"
    return peers

def create_server(node):
    """
    Create a gRPC server for the chat node.
    
    Args:
        node: ChatNode instance to serve
        
    Returns:
        tuple: (server, port) - gRPC server and the port it's listening on
    """
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add chat service
    chat_service = ChatService(node)
    pb2_grpc.add_ChatServiceServicer_to_server(chat_service, server)
    
    # Add replication service
    replication_service = ReplicationService(node)
    pb2_grpc.add_ReplicationServiceServicer_to_server(replication_service, server)
    
    # Add listening port
    server_address = f"{node.host}:{node.port}"
    port = server.add_insecure_port(server_address)
    
    return server, port

def main():
    """
    Main function to parse arguments and start the server.
    """
    parser = argparse.ArgumentParser(description='Start a chat server node')
    parser.add_argument('--id', type=str, help='Node ID')
    parser.add_argument('--host', type=str, help='Host address to bind to')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--db', type=str, help='Path to database file')
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        all_config = load_config(args.config)
        if args.id:
            # Get config for specific node
            node_config = None
            for node in all_config['nodes']:
                if node['id'] == args.id:
                    node_config = node
                    break
            if not node_config:
                raise ValueError(f"Node ID {args.id} not found in config")
        else:
            # Use first node in config
            node_config = all_config['nodes'][0]
            args.id = node_config['id']
    else:
        # Create default config
        all_config = load_config(None)
        if args.id:
            # Create default config for this node
            node_config = {
                'id': args.id,
                'host': args.host or 'localhost',
                'port': args.port or (50051 + int(args.id)),
                'db_path': args.db or f'node_{args.id}.db'
            }
        else:
            # Use first node in default config
            node_config = all_config['nodes'][0]
            args.id = node_config['id']
    
    # Override config with command line arguments
    if args.host:
        node_config['host'] = args.host
    if args.port:
        node_config['port'] = args.port
    if args.db:
        node_config['db_path'] = args.db
    
    # Get peer addresses
    peers = get_peer_addresses(all_config, args.id)
    
    # Create node
    node = ChatNode(
        node_id=args.id,
        host=node_config['host'],
        port=node_config['port'],
        peers=peers,
        db_path=node_config['db_path']
    )
    
    # Create and start gRPC server
    server, port = create_server(node)
    server.start()
    
    logger.info(f"Server started on {node_config['host']}:{node_config['port']}")
    logger.info(f"Node ID: {args.id}")
    logger.info(f"Peers: {peers}")
    
    try:
        # Keep server running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(0)

if __name__ == "__main__":
    main()
