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
        self.state = FOLLOWER
        self.leader_id = None
        self.election_timeout = random.uniform(5.0, 10.0)  # Longer timeout
        self.last_heartbeat = time.time()
        
        # Leader state
        self.next_index = {peer: 1 for peer in peers}
        self.match_index = {peer: 0 for peer in peers}
        
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
            try:
                with self.node_lock:
                    # Only start election if we're a follower and haven't received heartbeat
                    if (self.state == FOLLOWER and 
                        time.time() - self.last_heartbeat > self.election_timeout):
                        self._start_election()
                
                # Sleep for a short time to avoid busy waiting
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in election timer: {e}")
            
    def _run_heartbeat_timer(self):
        """Run the heartbeat timer loop for leaders."""
        while True:
            try:
                with self.node_lock:
                    if self.state == LEADER:
                        self._send_heartbeat()
                
                # Send heartbeats every 2 seconds
                time.sleep(2.0)
            except Exception as e:
                logger.error(f"Error in heartbeat timer: {e}")
            
    def _start_election(self):
        """Start a new election."""
        with self.node_lock:
            # Increment term and vote for self
            self.current_term += 1
            self.voted_for = self.node_id
            self.state = CANDIDATE
            self._persist_state()
            
            logger.info(f"Node {self.node_id} starting election for term {self.current_term}")
            
            # Reset election timeout
            self.election_timeout = random.uniform(5.0, 10.0)
            self.last_heartbeat = time.time()
            
            # Request votes from all peers
            votes = 1  # Vote for self
            total_nodes = len(self.peers) + 1
            majority = (total_nodes // 2) + 1
            
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
                    
                    response = stub.RequestVote(request, timeout=2.0)  # Longer RPC timeout
                    
                    if response.term > self.current_term:
                        # Revert to follower if we see higher term
                        self.current_term = response.term
                        self.state = FOLLOWER
                        self.voted_for = None
                        self._persist_state()
                        return
                    
                    if response.vote_granted:
                        votes += 1
                        if votes >= majority:
                            logger.info(f"Node {self.node_id} won election with {votes}/{total_nodes} votes")
                            self._become_leader()
                            return
                        
                except Exception as e:
                    logger.warning(f"Failed to get vote from {peer_id}: {e}")
            
            # If we get here without becoming leader, revert to follower
            self.state = FOLLOWER
            self.voted_for = None
            self._persist_state()
            
    def _become_leader(self):
        """Transition to leader state."""
        with self.node_lock:
            self.state = LEADER
            self.leader_id = self.node_id
            
            # Initialize leader state
            self.next_index = {peer: len(self.log) + 1 for peer in self.peers}
            self.match_index = {peer: 0 for peer in self.peers}
            
            # Send initial empty AppendEntries RPCs (heartbeat)
            self._send_heartbeat()
            
            logger.info(f"Node {self.node_id} became leader for term {self.current_term}")
            
    def _send_heartbeat(self):
        """Send AppendEntries RPCs to all peers (empty for heartbeat)."""
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
                
                response = stub.AppendEntries(request, timeout=2.0)  # Longer RPC timeout
                
                if response.term > self.current_term:
                    # Step down if we see higher term
                    self.current_term = response.term
                    self.state = FOLLOWER
                    self.voted_for = None
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
            self.state = FOLLOWER
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

    def SyncData(self, request, context):
        """
        Handle SyncData RPC from other nodes.
        Used to sync state between nodes.
        
        Args:
            request: SyncDataRequest protobuf message
            context: gRPC context
            
        Returns:
            SyncDataResponse protobuf message
        """
        try:
            with self.node_lock:
                # Update term if needed
                if request.term > self.current_term:
                    self.current_term = request.term
                    self.state = FOLLOWER
                    self.voted_for = None
                    self._persist_state()
                
                # Get requested data
                with self.db_lock:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    # Get accounts
                    cursor.execute("SELECT username, password FROM accounts")
                    accounts = cursor.fetchall()
                    
                    # Get messages
                    cursor.execute("SELECT sender, recipient, content, timestamp FROM messages")
                    messages = cursor.fetchall()
                    conn.close()
                
                return pb2.SyncDataResponse(
                    term=self.current_term,
                    success=True,
                    accounts=[
                        pb2.Account(username=username, password=password)
                        for username, password in accounts
                    ],
                    messages=[
                        pb2.Message(
                            sender=sender,
                            recipient=recipient,
                            content=content,
                            timestamp=timestamp
                        )
                        for sender, recipient, content, timestamp in messages
                    ]
                )
                
        except Exception as e:
            logger.error(f"Error in SyncData: {e}")
            return pb2.SyncDataResponse(
                term=self.current_term,
                success=False
            )

    def GetState(self, request, context):
        """
        Handle GetState RPC from other nodes.
        Used to get the current state of this node.
        
        Args:
            request: GetStateRequest protobuf message
            context: gRPC context
            
        Returns:
            GetStateResponse protobuf message
        """
        try:
            with self.node_lock:
                return pb2.GetStateResponse(
                    term=self.current_term,
                    state=self.state,
                    leader_id=self.leader_id or "",
                    last_log_index=len(self.log),
                    last_log_term=self.log[-1]['term'] if self.log else 0,
                    commit_index=self.commit_index,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"Error in GetState: {e}")
            return pb2.GetStateResponse(
                term=self.current_term,
                state=FOLLOWER,
                success=False
            )
