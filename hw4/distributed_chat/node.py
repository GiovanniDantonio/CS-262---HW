"""
Node implementation for distributed fault-tolerant chat system.
This module handles a single server node that implements the Raft consensus algorithm.
"""
import os
import sys
import time
import json
import sqlite3
import hashlib
import logging
import threading
import socket
import random
import grpc
from datetime import datetime
from concurrent import futures

# Import the generated protobuf modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from distributed_chat import distributed_chat_pb2 as pb2
from distributed_chat import distributed_chat_pb2_grpc as pb2_grpc

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("chat_node")

# Node states
FOLLOWER = 'follower'
CANDIDATE = 'candidate'
LEADER = 'leader'

class ChatNode:
    """
    A node in the distributed chat system implementing Raft consensus.
    Each node can be a leader, candidate, or follower and participates in the
    consensus protocol to ensure data is replicated correctly.
    """
    
    def __init__(self, node_id, peers, db_path):
        """
        Initialize node state.
        
        Args:
            node_id: Unique identifier for this node
            peers: Dictionary mapping peer IDs to their addresses
            db_path: Path to SQLite database file
        """
        self.node_id = node_id
        self.peers = peers
        self.db_path = db_path
        
        # Persistent state
        self.current_term = 0
        self.voted_for = None
        self.log = []
        
        # Volatile state
        self.commit_index = 0
        self.last_applied = 0
        self.state = 'follower'
        self.leader_id = None
        self.election_timeout = random.uniform(1.5, 3.0)
        self.last_heartbeat = time.time()
        
        # Leader state
        self.next_index = {peer: 1 for peer in peers}
        self.match_index = {peer: 0 for peer in peers}
        
        # Dynamic membership state
        self.non_voting_members = {}  # server_id -> address
        self.catchup_status = {}  # server_id -> {'last_index': int, 'status': 'catching_up'|'ready'}
        
        # Locks
        self.node_lock = threading.RLock()
        self.db_lock = threading.RLock()
        
        # Initialize database
        self._init_db()
        
        # Load persistent state if it exists
        self._load_persistent_state()
        
        # Start election timer
        self.election_timer = threading.Thread(target=self._run_election_timer)
        self.election_timer.daemon = True
        self.election_timer.start()
        
        # Start heartbeat timer
        self.heartbeat_timer = threading.Thread(target=self._run_heartbeat_timer)
        self.heartbeat_timer.daemon = True
        self.heartbeat_timer.start()
        
        logger.info(f"Node {node_id} initialized in {self.state} state")
        
    def _run_election_timer(self):
        """Run the election timeout loop."""
        while True:
            with self.node_lock:
                # Only start election if we're a follower and haven't received heartbeat
                if (self.state == 'follower' and 
                    time.time() - self.last_heartbeat > self.election_timeout):
                    self._start_election()
            
            # Sleep for a short time to avoid busy waiting
            time.sleep(0.1)
            
    def _run_heartbeat_timer(self):
        """Run the heartbeat timer loop for leaders."""
        while True:
            with self.node_lock:
                if self.state == 'leader':
                    self._send_heartbeat()
            
            # Send heartbeats every 500ms
            time.sleep(0.5)
            
    def _start_election(self):
        """Start a new election."""
        with self.node_lock:
            # Increment term and vote for self
            self.current_term += 1
            self.voted_for = self.node_id
            self.state = 'candidate'
            self._persist_state()
            
            logger.info(f"Node {self.node_id} starting election for term {self.current_term}")
            
            # Reset election timeout
            self.election_timeout = random.uniform(1.5, 3.0)
            self.last_heartbeat = time.time()
            
            # Request votes from all peers
            votes = 1  # Vote for self
            for peer_id, peer_addr in self.peers.items():
                try:
                    channel = grpc.insecure_channel(peer_addr)
                    stub = pb2_grpc.ReplicationServiceStub(channel)
                    
                    request = pb2.RequestVoteRequest(
                        term=self.current_term,
                        candidate_id=self.node_id,
                        last_log_index=len(self.log),
                        last_log_term=self.log[-1]['term'] if self.log else 0
                    )
                    
                    response = stub.RequestVote(request, timeout=0.5)
                    
                    if response.term > self.current_term:
                        # Revert to follower if we see higher term
                        self.current_term = response.term
                        self.state = 'follower'
                        self.voted_for = None
                        self._persist_state()
                        return
                    
                    if response.vote_granted:
                        votes += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to get vote from {peer_id}: {e}")
            
            # If we got majority of votes, become leader
            if votes > (len(self.peers) + 1) / 2:
                logger.info(f"Node {self.node_id} won election for term {self.current_term}")
                self._become_leader()
            else:
                # If we didn't get majority, revert to follower
                self.state = 'follower'
                self.voted_for = None
                self._persist_state()
                
    def _become_leader(self):
        """Transition to leader state."""
        with self.node_lock:
            self.state = 'leader'
            self.leader_id = self.node_id
            
            # Initialize leader state
            self.next_index = {peer: len(self.log) + 1 for peer in self.peers}
            self.match_index = {peer: 0 for peer in self.peers}
            
            # Initialize non-voting member state
            for server_id in self.non_voting_members:
                self.next_index[server_id] = len(self.log) + 1
                self.match_index[server_id] = 0
            
            # Send initial empty AppendEntries RPCs (heartbeat)
            self._send_heartbeat()
            
            logger.info(f"Node {self.node_id} became leader for term {self.current_term}")
            
    def AddServer(self, request, context):
        """Handle request to add a new server to the cluster."""
        with self.node_lock:
            if self.state != 'leader':
                return pb2.AddServerResponse(
                    success=False,
                    message="Not the leader",
                    leader_id=self.leader_id,
                    leader_address=self.peers.get(self.leader_id, '')
                )
            
            server_id = request.server_id
            server_address = request.server_address
            
            # Check if server is already a member
            if server_id in self.peers:
                return pb2.AddServerResponse(
                    success=False,
                    message="Server is already a voting member"
                )
            
            if server_id in self.non_voting_members:
                return pb2.AddServerResponse(
                    success=False,
                    message="Server is already a non-voting member"
                )
            
            # Add server as non-voting member
            self.non_voting_members[server_id] = server_address
            self.next_index[server_id] = len(self.log) + 1
            self.match_index[server_id] = 0
            self.catchup_status[server_id] = {
                'last_index': 0,
                'status': 'catching_up'
            }
            
            logger.info(f"Added server {server_id} as non-voting member")
            
            return pb2.AddServerResponse(
                success=True,
                message="Server added as non-voting member"
            )
    
    def CatchupServer(self, request, context):
        """Handle catchup request from a non-voting member."""
        with self.node_lock:
            if self.state != 'leader':
                return pb2.CatchupResponse(
                    success=False,
                    message="Not the leader"
                )
            
            server_id = request.server_id
            last_log_index = request.last_log_index
            
            if server_id not in self.non_voting_members:
                return pb2.CatchupResponse(
                    success=False,
                    message="Server is not a non-voting member"
                )
            
            # Send missing entries
            entries = []
            if last_log_index < len(self.log):
                entries = self.log[last_log_index:]
            
            # Update catchup status
            if entries:
                self.catchup_status[server_id]['last_index'] = len(self.log)
            else:
                # If no entries needed, server is caught up
                self.catchup_status[server_id]['status'] = 'ready'
            
            return pb2.CatchupResponse(
                success=True,
                message="Catchup entries sent",
                entries=entries,
                leader_commit=self.commit_index
            )
    
    def PromoteServer(self, request, context):
        """Handle request to promote a non-voting member to voting member."""
        with self.node_lock:
            if self.state != 'leader':
                return pb2.PromoteServerResponse(
                    success=False,
                    message="Not the leader"
                )
            
            server_id = request.server_id
            
            if server_id not in self.non_voting_members:
                return pb2.PromoteServerResponse(
                    success=False,
                    message="Server is not a non-voting member"
                )
            
            if self.catchup_status[server_id]['status'] != 'ready':
                return pb2.PromoteServerResponse(
                    success=False,
                    message="Server is not ready for promotion"
                )
            
            # Move server from non-voting to voting members
            server_address = self.non_voting_members.pop(server_id)
            self.peers[server_id] = server_address
            
            # Clean up catchup status
            del self.catchup_status[server_id]
            
            logger.info(f"Promoted server {server_id} to voting member")
            
            return pb2.PromoteServerResponse(
                success=True,
                message="Server promoted to voting member"
            )
            
    def _send_heartbeat(self):
        """Send AppendEntries RPCs to all peers (empty for heartbeat)."""
        # Send to voting members
        for peer_id, peer_addr in self.peers.items():
            try:
                channel = grpc.insecure_channel(peer_addr)
                stub = pb2_grpc.ReplicationServiceStub(channel)
                
                prev_log_index = self.next_index[peer_id] - 1
                prev_log_term = 0
                if prev_log_index > 0 and prev_log_index <= len(self.log):
                    prev_log_term = self.log[prev_log_index - 1]['term']
                
                request = pb2.AppendEntriesRequest(
                    term=self.current_term,
                    leader_id=self.node_id,
                    prev_log_index=prev_log_index,
                    prev_log_term=prev_log_term,
                    entries=[],
                    leader_commit=self.commit_index
                )
                
                response = stub.AppendEntries(request, timeout=0.5)
                
                if response.term > self.current_term:
                    self.current_term = response.term
                    self.state = 'follower'
                    self.voted_for = None
                    self._persist_state()
                    return
                    
            except Exception as e:
                logger.warning(f"Failed to send heartbeat to {peer_id}: {e}")
                
        # Send to non-voting members
        for server_id, addr in self.non_voting_members.items():
            try:
                channel = grpc.insecure_channel(addr)
                stub = pb2_grpc.ReplicationServiceStub(channel)
                
                request = pb2.AppendEntriesRequest(
                    term=self.current_term,
                    leader_id=self.node_id,
                    prev_log_index=prev_log_index,
                    prev_log_term=prev_log_term,
                    entries=[],  # Empty for heartbeat
                    leader_commit=self.commit_index
                )
                
                response = stub.AppendEntries(request, timeout=0.5)
                
                if response.term > self.current_term:
                    # Step down if we see higher term
                    self.current_term = response.term
                    self.state = 'follower'
                    self.voted_for = None
                    self.leader_id = None
                    self._persist_state()
                    return
                
            except Exception as e:
                logger.warning(f"Failed to send heartbeat to {peer_id}: {e}")
                
    def _persist_state(self):
        """Persist node state to disk."""
        try:
            state = {
                'current_term': self.current_term,
                'voted_for': self.voted_for,
                'log': self.log
            }
            with open(f"{self.db_path}.state", 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Error persisting state: {e}")
            
    def _load_persistent_state(self):
        """Load persisted state from disk."""
        try:
            state_path = f"{self.db_path}.state"
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state = json.load(f)
                    self.current_term = state['current_term']
                    self.voted_for = state['voted_for']
                    self.log = state['log']
        except Exception as e:
            logger.error(f"Error loading persistent state: {e}")
            
    def _init_db(self):
        """
        Initialize the SQLite database with required tables.
        Creates tables for accounts, messages, and raft state.
        """
        logger.info(f"Initializing database at {self.db_path}")
        with self.db_lock:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                
                # Account table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                ''')
                
                # Messages table
                c.execute('''
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
                ''')
                
                # Raft state table (for persistent Raft state)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS raft_state (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                ''')
                
                # Log entries table (for Raft log)
                c.execute('''
                    CREATE TABLE IF NOT EXISTS log_entries (
                        index_id INTEGER PRIMARY KEY,
                        term INTEGER NOT NULL,
                        command_type TEXT NOT NULL,
                        data BLOB NOT NULL
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.error(f"Database initialization failed: {e}")
                raise
            finally:
                conn.close()
                
    def AppendEntries(self, request, context):
        """
        Handle AppendEntries RPC from leader.
        
        Args:
            request: AppendEntriesRequest protobuf message
            context: gRPC context
            
        Returns:
            AppendEntriesResponse protobuf message
        """
        with self.node_lock:
            if request.term < self.current_term:
                return pb2.AppendEntriesResponse(
                    term=self.current_term,
                    success=False,
                    match_index=len(self.log)
                )
            
            # Update term if needed
            if request.term > self.current_term:
                self.current_term = request.term
                self.voted_for = None
                self._persist_state()
            
            # Accept leader
            self.state = 'follower'
            self.leader_id = request.leader_id
            self.last_heartbeat = time.time()
            
            # Check if log contains entry at prev_log_index with matching term
            if (request.prev_log_index > len(self.log) or 
                (request.prev_log_index > 0 and 
                 self.log[request.prev_log_index - 1]['term'] != request.prev_log_term)):
                return pb2.AppendEntriesResponse(
                    term=self.current_term,
                    success=False,
                    match_index=len(self.log)
                )
            
            # Process entries
            for entry_json in request.entries:
                entry = json.loads(entry_json)
                
                # Remove conflicting entries
                if request.prev_log_index + 1 <= len(self.log):
                    self.log = self.log[:request.prev_log_index]
                
                # Append new entry
                self.log.append(entry)
                
                # Apply to state machine if committed
                if request.leader_commit > self.commit_index:
                    self.commit_index = min(request.leader_commit, len(self.log))
                    while self.last_applied < self.commit_index:
                        self.last_applied += 1
                        self.chat_service._apply_entry_to_state_machine(self.log[self.last_applied - 1])
            
            self._persist_state()
            
            return pb2.AppendEntriesResponse(
                term=self.current_term,
                success=True,
                match_index=len(self.log)
            )
            
    def RequestVote(self, request, context):
        """
        Handle RequestVote RPC from candidate.
        
        Args:
            request: RequestVoteRequest protobuf message
            context: gRPC context
            
        Returns:
            RequestVoteResponse protobuf message
        """
        with self.node_lock:
            if request.term < self.current_term:
                return pb2.RequestVoteResponse(
                    term=self.current_term,
                    vote_granted=False
                )
            
            # Update term if needed
            if request.term > self.current_term:
                self.current_term = request.term
                self.voted_for = None
                self._persist_state()
            
            # Check if we can vote for this candidate
            last_log_index = len(self.log)
            last_log_term = self.log[-1]['term'] if self.log else 0
            
            if ((self.voted_for is None or self.voted_for == request.candidate_id) and
                (request.last_log_term > last_log_term or
                 (request.last_log_term == last_log_term and
                  request.last_log_index >= last_log_index))):
                # Vote for candidate
                self.voted_for = request.candidate_id
                self._persist_state()
                return pb2.RequestVoteResponse(
                    term=self.current_term,
                    vote_granted=True
                )
            
            return pb2.RequestVoteResponse(
                term=self.current_term,
                vote_granted=False
            )
