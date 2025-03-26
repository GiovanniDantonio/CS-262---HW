"""
Server implementation for distributed chat system.
Handles client requests and participates in the Raft consensus protocol.
"""
import os
import sys
import time
import json
import logging
import argparse
import threading
from concurrent import futures
import grpc

# Import the generated protobuf modules
import distributed_chat_pb2 as pb2
import distributed_chat_pb2_grpc as pb2_grpc

# Import node implementation
from node import ChatNode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger('chat_server')

class ChatService(pb2_grpc.ChatServiceServicer):
    """
    Implementation of the chat service.
    Handles client requests and forwards them to the node for consensus.
    """
    
    def __init__(self, node):
        """
        Initialize chat service.
        
        Args:
            node: ChatNode instance that handles consensus
        """
        self.node = node
    
    def Register(self, request, context):
        """Handle user registration."""
        try:
            username = request.username
            password = request.password
            
            # Forward to leader if not leader
            if not self.node.is_leader():
                if self.node.leader_id:
                    try:
                        leader_stub = self._get_peer_stub(self.node.leader_id)
                        return leader_stub.Register(request)
                    except Exception as e:
                        logger.error(f"Error forwarding Register to leader: {e}")
                        return pb2.Response(success=False, message="Leader unavailable")
                else:
                    return pb2.Response(success=False, message="No leader available")
            
            # Check if username exists
            with self.node.db_lock:
                cursor = self.node.db.cursor()
                cursor.execute("SELECT username FROM accounts WHERE username = ?", (username,))
                if cursor.fetchone():
                    return pb2.Response(success=False, message="Username already exists")
                
                # Add user
                cursor.execute(
                    "INSERT INTO accounts (username, password) VALUES (?, ?)",
                    (username, password)
                )
                self.node.db.commit()
                
            return pb2.Response(success=True, message="Registration successful")
            
        except Exception as e:
            logger.error(f"Error in Register: {e}")
            return pb2.Response(success=False, message=str(e))
    
    def Login(self, request, context):
        """Handle user login."""
        try:
            username = request.username
            password = request.password
            
            # Forward to leader if not leader
            if not self.node.is_leader():
                if self.node.leader_id:
                    try:
                        leader_stub = self._get_peer_stub(self.node.leader_id)
                        return leader_stub.Login(request)
                    except Exception as e:
                        logger.error(f"Error forwarding Login to leader: {e}")
                        return pb2.LoginResponse(success=False, message="Leader unavailable")
                else:
                    return pb2.LoginResponse(success=False, message="No leader available")
            
            # Verify credentials
            with self.node.db_lock:
                cursor = self.node.db.cursor()
                cursor.execute(
                    "SELECT password FROM accounts WHERE username = ?",
                    (username,)
                )
                result = cursor.fetchone()
                if not result or result[0] != password:
                    return pb2.LoginResponse(success=False, message="Invalid credentials")
                
                # Get unread count
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0",
                    (username,)
                )
                unread_count = cursor.fetchone()[0]
                
                # Update last login
                cursor.execute(
                    "UPDATE accounts SET last_login = CURRENT_TIMESTAMP, online = 1 WHERE username = ?",
                    (username,)
                )
                self.node.db.commit()
                
            return pb2.LoginResponse(
                success=True,
                message="Login successful",
                unread_count=unread_count
            )
            
        except Exception as e:
            logger.error(f"Error in Login: {e}")
            return pb2.LoginResponse(success=False, message=str(e))

def main():
    """Main function to parse arguments and start the server."""
    parser = argparse.ArgumentParser(description='Start a chat server node')
    parser.add_argument('--node-id', type=str, required=True, help='Unique node identifier')
    parser.add_argument('--port', type=int, required=True, help='Port to listen on')
    parser.add_argument('--peers', type=str, nargs='*', default=[], help='List of peer addresses (host:port)')
    args = parser.parse_args()
    
    try:
        # Create peer mapping
        peer_dict = {}
        for i, peer in enumerate(args.peers):
            if i + 1 != int(args.node_id):  # Don't include self in peers
                peer_dict[str(i + 1)] = peer
                
        # Initialize node
        db_path = f"node_{args.node_id}.db"
        node = ChatNode(args.node_id, peer_dict, db_path)
        
        # Create gRPC server
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 10 * 1024 * 1024),
                ('grpc.max_receive_message_length', 10 * 1024 * 1024),
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
                ('grpc.keepalive_permit_without_calls', True),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.http2.min_time_between_pings_ms', 10000),
                ('grpc.http2.min_ping_interval_without_data_ms', 5000),
            ]
        )
        
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
            logger.info("Shutting down server...")
            server.stop(0)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
