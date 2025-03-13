"""
Server launcher for the fault-tolerant chat system.
This script starts a chat server instance and joins it to a cluster.
"""
import argparse
import json
import logging
import os
import signal
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import ChatServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("server_launcher")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Start a fault-tolerant chat server")
    
    parser.add_argument('--id', required=True, help='Unique server ID')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, required=True, help='Port to listen on')
    parser.add_argument('--data-dir', default='./data', help='Directory for persistent storage')
    parser.add_argument('--config-file', help='Path to cluster configuration file')
    parser.add_argument('--join', help='Leader address to join (host:port)')
    
    return parser.parse_args()

def load_cluster_config(file_path):
    """
    Load cluster configuration from a JSON file.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        Dictionary mapping server IDs to addresses
    """
    if not os.path.exists(file_path):
        logger.warning(f"Config file {file_path} not found")
        return {}
    
    with open(file_path, 'r') as f:
        config = json.load(f)
    
    return config.get('servers', {})

def join_cluster(server_id, server_address, leader_address):
    """
    Join an existing cluster by contacting the leader.
    
    Args:
        server_id: ID of this server
        server_address: Address of this server
        leader_address: Address of the leader to contact
        
    Returns:
        True if successfully joined, False otherwise
    """
    import grpc
    from proto import chat_pb2, chat_pb2_grpc
    
    try:
        # Create channel and stub
        channel = grpc.insecure_channel(leader_address)
        stub = chat_pb2_grpc.RaftServiceStub(channel)
        
        # Create request
        request = chat_pb2.JoinRequest(
            server_id=server_id,
            server_address=server_address
        )
        
        # Send request
        response = stub.JoinCluster(request)
        
        if response.success:
            logger.info(f"Successfully joined cluster: {response.message}")
            return True
        else:
            logger.error(f"Failed to join cluster: {response.message}")
            return False
            
    except Exception as e:
        logger.error(f"Error joining cluster: {e}")
        return False
    finally:
        if 'channel' in locals():
            channel.close()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Ensure data directory exists
    os.makedirs(args.data_dir, exist_ok=True)
    
    # Server address for gRPC
    server_address = f"{args.host}:{args.port}"
    
    # Load peer configuration
    peers = {}
    if args.config_file:
        peers = load_cluster_config(args.config_file)
        
        # Remove self from peers
        if args.id in peers:
            del peers[args.id]
    
    # Create the server
    server = ChatServer(
        server_id=args.id,
        server_address=server_address,
        peers=peers,
        data_dir=args.data_dir,
        grpc_port=args.port
    )
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, stopping server...")
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the server
    server.start()
    logger.info(f"Server {args.id} started on {server_address}")
    
    # Join cluster if requested
    if args.join:
        logger.info(f"Attempting to join cluster via {args.join}...")
        join_result = join_cluster(args.id, server_address, args.join)
        
        if not join_result:
            logger.warning("Failed to join cluster. Continuing as standalone node.")
    
    # Wait for termination
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping server...")
        server.stop()

if __name__ == "__main__":
    main()
