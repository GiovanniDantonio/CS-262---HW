"""
Server launcher for the fault-tolerant chat system.
This script starts a chat server instance and, if requested, joins it to a cluster.
It registers the ChatService with the ChatServer instance and the RaftService
with a custom implementation (MyRaftService).
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
import grpc
import concurrent.futures

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import ChatServer
from proto import chat_pb2, chat_pb2_grpc
from server.raft_service_impl import MyRaftService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("server_launcher")


def parse_args():
    parser = argparse.ArgumentParser(description="Start a fault-tolerant chat server")
    parser.add_argument('--id', required=True, help='Unique server ID')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, required=True, help='Port to listen on')
    parser.add_argument('--data-dir', default='./data', help='Directory for persistent storage')
    parser.add_argument('--config-file', help='Path to cluster configuration file')
    parser.add_argument('--join', help='Leader address to join (host:port)')
    return parser.parse_args()


def load_cluster_config(file_path):
    if not os.path.exists(file_path):
        logger.warning(f"Config file {file_path} not found")
        return {}
    with open(file_path, 'r') as f:
        config = json.load(f)
    return config.get('servers', {})


def join_cluster(server_id, server_address, leader_address):
    """
    Join an existing cluster by contacting the leader.
    """
    try:
        channel = grpc.insecure_channel(leader_address)
        stub = chat_pb2_grpc.RaftServiceStub(channel)
        request = chat_pb2.JoinRequest(
            server_id=server_id,
            server_address=server_address
        )
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
    args = parse_args()
    os.makedirs(args.data_dir, exist_ok=True)
    server_address = f"{args.host}:{args.port}"

    # Load peer configuration (if provided) and remove self from peers.
    peers = {}
    if args.config_file:
        peers = load_cluster_config(args.config_file)
        if args.id in peers:
            del peers[args.id]

    # Create ChatServer instance to handle ChatService RPCs.
    chat_server = ChatServer(
        server_id=args.id,
        server_address=server_address,
        peers=peers,
        data_dir=args.data_dir,
        grpc_port=args.port
    )

    # Set up signal handlers for graceful shutdown.
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, stopping server...")
        stop_server()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create a gRPC server with a thread pool executor.
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
    grpc_server = grpc.server(executor)

    # Register ChatService with the ChatServer instance.
    chat_pb2_grpc.add_ChatServiceServicer_to_server(chat_server, grpc_server)
    # Register RaftService with your custom implementation.
    raft_service = MyRaftService()
    chat_pb2_grpc.add_RaftServiceServicer_to_server(raft_service, grpc_server)

    grpc_server.add_insecure_port(f"[::]:{args.port}")
    grpc_server.start()

    # Start the ChatServer's internal logic (e.g., Raft node, persistent storage, etc.)
    chat_server.start()

    logger.info(f"Server {args.id} started on {server_address}")

    # Join cluster if the join flag is provided.
    if args.join:
        logger.info(f"Attempting to join cluster via {args.join}...")
        if not join_cluster(args.id, server_address, args.join):
            logger.warning("Failed to join cluster. Continuing as standalone node.")

    def stop_server():
        logger.info("Stopping gRPC server and ChatServer...")
        grpc_server.stop(grace=1.0)
        chat_server.stop()
        executor.shutdown(wait=False)

    try:
        grpc_server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping server...")
        stop_server()


if __name__ == "__main__":
    main()
