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
    
    def __init__(self, node_id, host, port, peers, db_path=None):
        """
        Initialize a chat server node.
        
        Args:
            node_id: Unique identifier for this node
            host: Host address for gRPC server
            port: Port for gRPC server
            peers: Dictionary of peer node_id -> address (host:port)
            db_path: Path to SQLite database file for persistent storage
        """
        self.node_id = node_id
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.peers = peers  # Dict of node_id -> address
        
        # Persistent state on all servers
        self.current_term = 0
        self.voted_for = None
        self.log = []  # Log entries
        
        # Volatile state on all servers
        self.commit_index = 0  # Index of highest log entry known to be committed
        self.last_applied = 0  # Index of highest log entry applied to state machine
        
        # Volatile state on leaders (reinitialized after election)
        self.next_index = {}   # For each server, index of next log entry to send
        self.match_index = {}  # For each server, index of highest log entry known to be replicated
        
        # System state
        self.state = FOLLOWER
        self.election_timeout = self._random_timeout()
        self.last_heartbeat = time.time()
        self.leader_id = None
        
        # Database setup
        self.db_path = db_path or f"node_{node_id}.db"
        self.db_lock = threading.RLock()
        
        # Consensus lock to prevent race conditions
        self.node_lock = threading.RLock()
        
        # Initialize the database
        self._init_db()
        
        # Start background threads
        self._start_background_threads()
        
        logger.info(f"Node {node_id} initialized at {self.address}. Peers: {peers}")
    
    def _random_timeout(self):
        """
        Generate a random election timeout between 150-300 ms.
        
        Returns:
            float: Timeout in seconds
        """
        return random.uniform(0.15, 0.3)
    
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
    
    def _start_background_threads(self):
        """
        Start background threads for election timeout and leader heartbeat.
        """
        # Start election timer
        self.election_timer = threading.Thread(target=self._run_election_timer)
        self.election_timer.daemon = True
        self.election_timer.start()
        
        # If leader, start heartbeat timer
        self.heartbeat_timer = threading.Thread(target=self._run_heartbeat_timer)
        self.heartbeat_timer.daemon = True
        self.heartbeat_timer.start()
    
    def _run_election_timer(self):
        """
        Background thread that monitors election timeout and starts election if needed.
        """
        while True:
            with self.node_lock:
                # Only followers and candidates time out and start elections
                if self.state != LEADER:
                    elapsed = time.time() - self.last_heartbeat
                    if elapsed > self.election_timeout:
                        logger.info(f"Election timeout ({elapsed:.2f}s). Starting election.")
                        self._start_election()
            
            # Check every 50ms
            time.sleep(0.05)
    
    def _run_heartbeat_timer(self):
        """
        Background thread that sends heartbeats if this node is the leader.
        """
        while True:
            with self.node_lock:
                if self.state == LEADER:
                    self._send_heartbeats()
            
            # Send heartbeats every 100ms
            time.sleep(0.1)
    
    def _start_election(self):
        """
        Start a new election by transitioning to CANDIDATE state
        and requesting votes from peers.
        """
        with self.node_lock:
            # Increment current term and vote for self
            self.current_term += 1
            self.voted_for = self.node_id
            self.state = CANDIDATE
            
            # Reset election timeout
            self.last_heartbeat = time.time()
            self.election_timeout = self._random_timeout()
            
            logger.info(f"Node {self.node_id} started election for term {self.current_term}")
            
            # Request votes from all peers
            votes_received = 1  # Vote for self
            
            # Send RequestVote RPCs to all peers
            for peer_id, peer_addr in self.peers.items():
                try:
                    # Get last log index and term
                    last_log_index = len(self.log)
                    last_log_term = self.log[-1]['term'] if self.log else 0
                    
                    # Create gRPC channel to peer
                    channel = grpc.insecure_channel(peer_addr)
                    stub = pb2_grpc.ReplicationServiceStub(channel)
                    
                    # Create vote request
                    request = pb2.VoteRequest(
                        term=self.current_term,
                        candidate_id=self.node_id,
                        last_log_index=last_log_index,
                        last_log_term=last_log_term
                    )
                    
                    # Send request with timeout
                    response = stub.RequestVote(request, timeout=0.1)
                    
                    logger.debug(f"Received vote response from {peer_id}: {response}")
                    
                    # If response term is higher, revert to follower
                    if response.term > self.current_term:
                        self.current_term = response.term
                        self.state = FOLLOWER
                        self.voted_for = None
                        return
                    
                    # Count vote if granted
                    if response.vote_granted:
                        votes_received += 1
                
                except Exception as e:
                    logger.warning(f"Error requesting vote from {peer_id}: {e}")
            
            # If received votes from majority of servers, become leader
            if votes_received > (len(self.peers) + 1) / 2:
                self._become_leader()
    
    def _become_leader(self):
        """
        Transition to leader state and initialize leader state.
        """
        with self.node_lock:
            logger.info(f"Node {self.node_id} becoming leader for term {self.current_term}")
            self.state = LEADER
            self.leader_id = self.node_id
            
            # Initialize leader state
            for peer_id in self.peers:
                self.next_index[peer_id] = len(self.log) + 1
                self.match_index[peer_id] = 0
            
            # Send initial heartbeats
            self._send_heartbeats()
    
    def _send_heartbeats(self):
        """
        Send heartbeats (AppendEntries with no entries) to all peers.
        """
        logger.debug(f"Sending heartbeats for term {self.current_term}")
        
        for peer_id, peer_addr in self.peers.items():
            try:
                # Create gRPC channel to peer
                channel = grpc.insecure_channel(peer_addr)
                stub = pb2_grpc.ReplicationServiceStub(channel)
                
                # Get previous log info
                prev_log_index = self.next_index[peer_id] - 1
                prev_log_term = 0
                if prev_log_index > 0 and prev_log_index <= len(self.log):
                    prev_log_term = self.log[prev_log_index - 1]['term']
                
                # Create empty AppendEntries request (heartbeat)
                request = pb2.AppendEntriesRequest(
                    term=self.current_term,
                    leader_id=self.node_id,
                    prev_log_index=prev_log_index,
                    prev_log_term=prev_log_term,
                    entries=[],  # Empty for heartbeat
                    leader_commit=self.commit_index
                )
                
                # Send request with timeout
                response = stub.AppendEntries(request, timeout=0.1)
                
                # If response term is higher, revert to follower
                if response.term > self.current_term:
                    self.current_term = response.term
                    self.state = FOLLOWER
                    self.voted_for = None
                    return
            
            except Exception as e:
                logger.warning(f"Error sending heartbeat to {peer_id}: {e}")
    
    # Additional methods for request handling and log replication will be added
    # in the service implementation classes
