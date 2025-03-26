"""
Server startup script for distributed chat system.
This script creates and runs a chat server node that can participate
in the distributed consensus protocol.

Usage:
    python server.py --node-id <node_id> --port <port> [--peers <peer_addresses>]
"""
import os
import sys
import time
import yaml
import json
import threading
import argparse
from concurrent import futures
import grpc
import sqlite3

# Import the generated protobuf modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from distributed_chat import distributed_chat_pb2 as pb2
from distributed_chat import distributed_chat_pb2_grpc as pb2_grpc
from distributed_chat.node import ChatNode
from distributed_chat.chat_service import ChatService
from distributed_chat.replication_service import ReplicationService
from distributed_chat.logging_config import setup_logger, log_error, RPCLogger

# Set up logging
logger = setup_logger("chat_server")

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
        with RPCLogger(logger, "load_config", config_file=config_file, node_id=node_id):
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
        log_error(logger, e, {
            'operation': 'load_config',
            'config_file': config_file,
            'node_id': node_id
        })
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
    with RPCLogger(logger, "get_peer_addresses", current_node_id=current_node_id):
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
    with RPCLogger(logger, "create_server", node_id=node.node_id):
        try:
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
        except Exception as e:
            log_error(logger, e, {
                'operation': 'create_server',
                'node_id': node.node_id,
                'host': node.host,
                'port': node.port
            })
            raise

def initialize_database(db_path):
    """Initialize the database with required tables."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Create accounts table
        c.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        """)
        
        # Create messages table
        c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read INTEGER DEFAULT 0,
            FOREIGN KEY (sender) REFERENCES accounts(username),
            FOREIGN KEY (recipient) REFERENCES accounts(username)
        )
        """)
        
        conn.commit()
    finally:
        conn.close()

class ChatService(pb2_grpc.ChatServiceServicer):
    def __init__(self, node):
        self.node = node

    def Register(self, request, context):
        """
        Handle user registration.
        
        Args:
            request: UserCredentials protobuf message
            context: gRPC context
            
        Returns:
            Response protobuf message
        """
        logger.info(f"Register request for: {request.username}")
        
        # Check if username already exists (can be done by any node)
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            c.execute("SELECT 1 FROM accounts WHERE username = ?", (request.username,))
            if c.fetchone():
                conn.close()
                return pb2.Response(success=False, message="Username already exists")
            conn.close()
        
        # Forward write operation to leader if we're not the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                try:
                    if self.node.leader_id and self.node.leader_id in self.node.peers:
                        channel = grpc.insecure_channel(self.node.peers[self.node.leader_id])
                        stub = pb2_grpc.ChatServiceStub(channel)
                        return stub.Register(request)
                    else:
                        return pb2.Response(success=False, message="No leader available")
                except Exception as e:
                    logger.error(f"Failed to forward to leader: {e}")
                    return pb2.Response(success=False, message="Failed to reach leader")
            
            # We're the leader - handle the registration
            try:
                success = self._append_to_log('REGISTER', {
                    'username': request.username,
                    'password': request.password
                })
                
                if success:
                    return pb2.Response(success=True, message="Registration successful")
                else:
                    return pb2.Response(success=False, message="Registration failed")
            except Exception as e:
                logger.error(f"Error during registration: {e}")
                return pb2.Response(success=False, message=str(e))

def main():
    """Main function to parse arguments and start the server."""
    parser = argparse.ArgumentParser(description='Start a chat server node')
    parser.add_argument('--node-id', type=str, required=True, help='Unique node identifier')
    parser.add_argument('--port', type=int, required=True, help='Port to listen on')
    parser.add_argument('--peers', type=str, nargs='*', default=[], help='List of peer addresses (host:port)')
    args = parser.parse_args()
    
    # Create peer mapping
    peer_dict = {}
    for i, peer in enumerate(args.peers):
        if i + 1 != int(args.node_id):  # Don't include self in peers
            peer_dict[str(i + 1)] = peer
            
    # Initialize node
    db_path = f"node_{args.node_id}.db"
    node = ChatNode(args.node_id, peer_dict, db_path)
    
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add services
    chat_service = ChatService(node)
    node.chat_service = chat_service  # Give node reference to chat service
    pb2_grpc.add_ChatServiceServicer_to_server(chat_service, server)
    pb2_grpc.add_ReplicationServiceServicer_to_server(node, server)
    
    # Start server
    address = f"[::]:{args.port}"
    server.add_insecure_port(address)
    server.start()
    
    logger.info(f"Server {args.node_id} started on port {args.port}")
    logger.info(f"Peers: {peer_dict}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    main()
