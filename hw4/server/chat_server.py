"""
Fault-tolerant chat server implementation.
Integrates Raft consensus with gRPC-based chat service.
"""
import argparse
import concurrent.futures
import grpc
import json
import logging
import os
import signal
import sys
import threading
import time
from typing import Dict, List, Optional, Any, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import proto-generated modules
from proto import chat_pb2, chat_pb2_grpc

# Import our modules
from common.raft import RaftNode, NodeState, LogEntry
from common.persistence import PersistentStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_server")

class ChatServer(chat_pb2_grpc.ChatServiceServicer, chat_pb2_grpc.RaftServiceServicer):
    """
    Implementation of the fault-tolerant chat server.
    Integrates gRPC service with Raft consensus and persistent storage.
    """
    
    def __init__(self, server_id: str, server_address: str, peers: Dict[str, str], 
                 data_dir: str, grpc_port: int):
        """
        Initialize the chat server.
        
        Args:
            server_id: Unique ID for this server
            server_address: Network address for this server (host:port)
            peers: Dictionary mapping peer IDs to their network addresses
            data_dir: Directory for persistent storage
            grpc_port: Port for gRPC server
        """
        self.server_id = server_id
        self.server_address = server_address
        self.grpc_port = grpc_port
        self.data_dir = data_dir
        
        # Initialize persistent storage
        self.storage = PersistentStorage(server_id, data_dir)
        
        # Initialize Raft node
        self.raft = RaftNode(server_id, peers, os.path.join(data_dir, server_id))
        
        # Register RPC callbacks
        self._register_rpc_callbacks()
        
        # For streaming clients
        self.active_streams = {}
        self.stream_lock = threading.RLock()
        
        # Server management
        self.server = None
        self.is_running = False
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        
        # Load initial state
        self._load_state()
        
    def _register_rpc_callbacks(self) -> None:
        """Register callbacks for Raft RPCs."""
        callbacks = {
            "request_vote": self._send_request_vote,
            "append_entries": self._send_append_entries
        }
        self.raft.register_rpc_callbacks(callbacks)
        
    def _load_state(self) -> None:
        """Load state from persistent storage."""
        # Load Raft metadata
        current_term, voted_for = self.storage.load_metadata()
        self.raft.current_term = current_term
        self.raft.voted_for = voted_for
        
        # Load log entries
        entries = self.storage.read_log_entries()
        for entry_dict in entries:
            entry = LogEntry(
                term=entry_dict["term"],
                command=entry_dict["command"],
                index=entry_dict["index"]
            )
            self.raft.log.append(entry)
            
        # Load snapshot info
        last_included_index, last_included_term = self.storage.load_snapshot()
        if last_included_index >= 0:
            # Update Raft state based on snapshot
            self.raft.commit_index = max(self.raft.commit_index, last_included_index)
            self.raft.last_applied = max(self.raft.last_applied, last_included_index)
            
    def start(self) -> None:
        """Start the chat server and Raft node."""
        if self.is_running:
            return
            
        # Start the Raft node
        self.raft.start()
        
        # Create and start the gRPC server
        self.server = grpc.server(self.executor)
        chat_pb2_grpc.add_ChatServiceServicer_to_server(self, self.server)
        chat_pb2_grpc.add_RaftServiceServicer_to_server(self, self.server)
        
        self.server.add_insecure_port(f"[::]:{self.grpc_port}")
        self.server.start()
        self.is_running = True
        
        logger.info(f"Chat server started on port {self.grpc_port}")
        
    def stop(self) -> None:
        """Stop the chat server and Raft node."""
        if not self.is_running:
            return
            
        logger.info("Stopping chat server...")
        
        # Stop the gRPC server
        if self.server:
            self.server.stop(grace=1.0)
            
        # Stop the Raft node
        self.raft.stop()
        
        # Clean up resources
        self.executor.shutdown(wait=False)
        
        self.is_running = False
        logger.info("Chat server stopped")
        
    def wait_for_termination(self) -> None:
        """Wait for server termination."""
        if self.server:
            self.server.wait_for_termination()
            
    # ----- Helper methods for Raft RPCs -----
    
    def _send_request_vote(self, peer_id: str, peer_addr: str, request: Dict[str, Any], 
                          callback: callable) -> None:
        """
        Send RequestVote RPC to a peer.
        
        Args:
            peer_id: ID of the peer
            peer_addr: Address of the peer
            request: RequestVote request
            callback: Callback for response
        """
        # Convert dictionary to protobuf message
        grpc_request = chat_pb2.VoteRequest(
            term=request["term"],
            candidate_id=request["candidate_id"],
            last_log_index=request["last_log_index"],
            last_log_term=request["last_log_term"]
        )
        
        # Create channel and stub
        channel = grpc.insecure_channel(peer_addr)
        stub = chat_pb2_grpc.RaftServiceStub(channel)
        
        # Make the RPC call asynchronously
        future = stub.RequestVote.future(grpc_request)
        future.add_done_callback(
            lambda f: self._handle_request_vote_response(f, callback, channel)
        )
    
    def _handle_request_vote_response(self, future, callback, channel):
        """Handle response from RequestVote RPC."""
        try:
            response = future.result()
            # Convert protobuf message to dictionary
            result = {
                "term": response.term,
                "vote_granted": response.vote_granted
            }
            callback(result)
        except Exception as e:
            callback(None, e)
        finally:
            channel.close()
    
    def _send_append_entries(self, peer_id: str, peer_addr: str, request: Dict[str, Any], 
                           callback: callable) -> None:
        """
        Send AppendEntries RPC to a peer.
        
        Args:
            peer_id: ID of the peer
            peer_addr: Address of the peer
            request: AppendEntries request
            callback: Callback for response
        """
        # Convert entries from dictionary to protobuf
        entries = []
        for entry_dict in request["entries"]:
            # Create the appropriate command based on the entry type
            log_entry = chat_pb2.LogEntry(
                term=entry_dict["term"],
                index=entry_dict["index"]
            )
            
            # Set the command field based on the type
            command = entry_dict["command"]
            if "message" in command:
                msg = command["message"]
                log_entry.message_command.id = msg.get("id", 0)
                log_entry.message_command.sender = msg.get("sender", "")
                log_entry.message_command.recipient = msg.get("recipient", "")
                log_entry.message_command.content = msg.get("content", "")
                log_entry.message_command.timestamp = msg.get("timestamp", "")
                log_entry.message_command.read = msg.get("read", False)
                log_entry.message_command.sequence_number = msg.get("sequence_number", 0)
            
            entries.append(log_entry)
        
        # Create the request
        grpc_request = chat_pb2.AppendEntriesRequest(
            term=request["term"],
            leader_id=request["leader_id"],
            prev_log_index=request["prev_log_index"],
            prev_log_term=request["prev_log_term"],
            entries=entries,
            leader_commit=request["leader_commit"]
        )
        
        # Create channel and stub
        channel = grpc.insecure_channel(peer_addr)
        stub = chat_pb2_grpc.RaftServiceStub(channel)
        
        # Make the RPC call asynchronously
        future = stub.AppendEntries.future(grpc_request)
        future.add_done_callback(
            lambda f: self._handle_append_entries_response(f, callback, channel)
        )
    
    def _handle_append_entries_response(self, future, callback, channel):
        """Handle response from AppendEntries RPC."""
        try:
            response = future.result()
            # Convert protobuf message to dictionary
            result = {
                "term": response.term,
                "success": response.success,
                "match_index": response.match_index
            }
            callback(result)
        except Exception as e:
            callback(None, e)
        finally:
            channel.close()
