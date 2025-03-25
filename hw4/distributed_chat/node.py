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
        self.election_timer = threading.Thread(target=self._heartbeat_loop)
        self.election_timer.daemon = True
        self.election_timer.start()
        
        # If leader, start heartbeat timer
        self.heartbeat_timer = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_timer.daemon = True
        self.heartbeat_timer.start()
    
    def _heartbeat_loop(self):
        """
        Main heartbeat loop that handles leader election and leader heartbeats.
        This is the core of the Raft consensus algorithm implementation.
        """
        while True:
            try:
                time.sleep(0.05)  # Check state every 50ms
                
                with self.node_lock:
                    current_time = time.time()
                    
                    # If leader, send heartbeats
                    if self.state == LEADER:
                        if current_time - self.last_heartbeat >= 0.05:  # Send heartbeat every 50ms
                            self._send_heartbeats()
                            self.last_heartbeat = current_time
                            
                    # If follower or candidate, check for election timeout
                    else:
                        if current_time - self.last_heartbeat > self.election_timeout:
                            logger.info(f"Election timeout triggered for node {self.node_id}")
                            # Transition to candidate and start election
                            self._start_election()
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                # Continue running even if there's an error
    
    def _start_election(self):
        """
        Start an election by incrementing term, voting for self, and requesting votes.
        """
        with self.node_lock:
            # Become a candidate
            self.state = CANDIDATE
            self.current_term += 1
            self.voted_for = self.node_id
            self.leader_id = None
            votes_received = 1  # Vote for self
            
            logger.info(f"Starting election for term {self.current_term}")
            
            # Reset election timeout
            self.election_timeout = self._random_timeout()
            self.last_heartbeat = time.time()
            
            # Request votes from all peers
            for peer_id, peer_address in self.peers.items():
                if peer_id == self.node_id:
                    continue
                
                # Send vote request in a separate thread to avoid blocking
                threading.Thread(
                    target=self._request_vote_from_peer,
                    args=(peer_id, peer_address, self.current_term, votes_received),
                    daemon=True
                ).start()
    
    def _request_vote_from_peer(self, peer_id, peer_address, term, votes_received):
        """
        Request vote from a single peer in a background thread.
        
        Args:
            peer_id: ID of the peer to request vote from
            peer_address: Address of the peer
            term: Current term
            votes_received: Shared votes counter
        """
        try:
            with grpc.insecure_channel(peer_address) as channel:
                stub = pb2_grpc.ReplicationServiceStub(channel)
                
                # Prepare vote request
                last_log_index = len(self.log)
                last_log_term = self.log[-1]['term'] if self.log else 0
                
                # Request vote
                response = stub.RequestVote(
                    pb2.VoteRequest(
                        term=term,
                        candidate_id=self.node_id,
                        last_log_index=last_log_index,
                        last_log_term=last_log_term
                    )
                )
                
                # Process response
                with self.node_lock:
                    # If no longer a candidate or term changed, ignore response
                    if self.state != CANDIDATE or self.current_term != term:
                        return
                    
                    # If received a higher term, convert to follower
                    if response.term > self.current_term:
                        self.current_term = response.term
                        self.state = FOLLOWER
                        self.voted_for = None
                        self.last_heartbeat = time.time()
                        return
                    
                    # If vote granted, increment vote count
                    if response.vote_granted:
                        votes_received += 1
                        logger.info(f"Received vote from node {peer_id}, total votes: {votes_received}")
                        
                        # Check if we have a majority
                        if votes_received > len(self.peers) / 2:
                            logger.info(f"Node {self.node_id} won election for term {self.current_term}")
                            # Become leader
                            self._become_leader()
        except Exception as e:
            logger.error(f"Error requesting vote from {peer_id}: {e}")
    
    def _become_leader(self):
        """
        Transition to leader state and initialize leader state.
        """
        with self.node_lock:
            if self.state != CANDIDATE:
                return
                
            self.state = LEADER
            self.leader_id = self.node_id
            logger.info(f"Node {self.node_id} becoming leader for term {self.current_term}")
            
            # Initialize leader state
            for peer_id in self.peers:
                if peer_id != self.node_id:
                    self.next_index[peer_id] = len(self.log) + 1
                    self.match_index[peer_id] = 0
            
            # Send immediate heartbeat to establish authority
            self._send_heartbeats()
            self.last_heartbeat = time.time()
            
            # Persist state
            self._persist_state()
    
    def _send_heartbeats(self):
        """
        Send heartbeats (empty AppendEntries RPCs) to all peers to maintain authority.
        """
        for peer_id, peer_address in self.peers.items():
            if peer_id == self.node_id:
                continue
                
            # Send heartbeat in background thread
            threading.Thread(
                target=self._send_append_entries,
                args=(peer_id, peer_address, []),  # Empty entries for heartbeat
                daemon=True
            ).start()
    
    def _send_append_entries(self, peer_id, peer_address, entries):
        """
        Send AppendEntries RPC to a peer.
        
        Args:
            peer_id: ID of the peer
            peer_address: Address of the peer
            entries: Log entries to send ([] for heartbeat)
        """
        try:
            with grpc.insecure_channel(peer_address) as channel:
                stub = pb2_grpc.ReplicationServiceStub(channel)
                
                # Prepare request
                with self.node_lock:
                    # If no longer leader, stop sending
                    if self.state != LEADER:
                        return
                        
                    # Get next index for this peer
                    next_idx = self.next_index.get(peer_id, len(self.log) + 1)
                    
                    # Find prev log index and term
                    prev_log_index = next_idx - 1
                    prev_log_term = 0
                    if prev_log_index > 0 and prev_log_index <= len(self.log):
                        prev_log_term = self.log[prev_log_index - 1]['term']
                    
                    # Create entries for this peer
                    if not entries:  # Heartbeat
                        log_entries = []
                    else:
                        log_entries = entries
                    
                    # Create AppendEntries request
                    request = pb2.AppendEntriesRequest(
                        term=self.current_term,
                        leader_id=self.node_id,
                        prev_log_index=prev_log_index,
                        prev_log_term=prev_log_term,
                        entries=json.dumps(log_entries),
                        leader_commit=self.commit_index
                    )
                
                # Send request
                response = stub.AppendEntries(request)
                
                # Process response
                with self.node_lock:
                    # If no longer leader or term changed, stop processing
                    if self.state != LEADER or self.current_term != request.term:
                        return
                    
                    # If received higher term, become follower
                    if response.term > self.current_term:
                        self.current_term = response.term
                        self.state = FOLLOWER
                        self.voted_for = None
                        self.leader_id = None
                        self.last_heartbeat = time.time()
                        return
                    
                    # If success, update next and match indices
                    if response.success:
                        if entries:  # Not just a heartbeat
                            new_next_idx = prev_log_index + len(log_entries) + 1
                            self.next_index[peer_id] = new_next_idx
                            self.match_index[peer_id] = new_next_idx - 1
                            
                            # Check if we can advance commit index
                            self._update_commit_index()
                    else:
                        # If failure due to log inconsistency, decrement next_index and retry
                        if self.next_index[peer_id] > 1:
                            self.next_index[peer_id] -= 1
                            # Retry immediately
                            self._send_append_entries(peer_id, peer_address, entries)
        except Exception as e:
            logger.error(f"Error sending AppendEntries to {peer_id}: {e}")
            # Mark node as potentially down
            # This helps with fault tolerance in case a node is unreachable
            with self.node_lock:
                if self.state == LEADER:
                    logger.warning(f"Node {peer_id} appears to be down")
                    # We'll continue trying in the next heartbeat cycle
    
    def _update_commit_index(self):
        """
        Update the commit index based on the matched indices of all nodes.
        This is called after successful AppendEntries responses.
        """
        with self.node_lock:
            if self.state != LEADER:
                return
                
            # Find the highest index that is replicated on a majority of nodes
            for n in range(len(self.log), self.commit_index, -1):
                # Count nodes that have this entry
                count = 1  # Leader has it
                for peer_id in self.peers:
                    if peer_id != self.node_id and self.match_index.get(peer_id, 0) >= n:
                        count += 1
                
                # If majority and entry is from current term, commit it
                if count > len(self.peers) / 2 and self.log[n-1]['term'] == self.current_term:
                    self.commit_index = n
                    logger.info(f"Updated commit index to {n}")
                    # Apply committed entries
                    self._apply_committed_entries()
                    break
    
    def _apply_committed_entries(self):
        """
        Apply all committed but not yet applied log entries to the state machine.
        """
        with self.node_lock:
            while self.last_applied < self.commit_index:
                self.last_applied += 1
                entry = self.log[self.last_applied - 1]
                
                # Apply the command to the state machine
                self._apply_log_entry(entry)
                
                logger.info(f"Applied log entry at index {self.last_applied}: {entry['command']}")
    
    def _apply_log_entry(self, entry):
        """
        Apply a single log entry to the state machine.
        
        Args:
            entry: Log entry to apply
        """
        command = entry['command']
        data = entry['data']
        
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            try:
                if command == 'REGISTER':
                    # Register a new user
                    c.execute(
                        "INSERT INTO accounts (username, password_hash) VALUES (?, ?)",
                        (data['username'], data['password_hash'])
                    )
                    
                elif command == 'SEND_MESSAGE':
                    # Send a message
                    c.execute(
                        "INSERT INTO messages (sender, recipient, content, timestamp) VALUES (?, ?, ?, ?)",
                        (data['sender'], data['recipient'], data['content'], data['timestamp'])
                    )
                    
                elif command == 'DELETE_MESSAGE':
                    # Delete a message
                    c.execute(
                        "DELETE FROM messages WHERE rowid = ?",
                        (data['message_id'],)
                    )
                    
                # Add other command handlers as needed
                
                conn.commit()
            except Exception as e:
                logger.error(f"Error applying log entry: {e}")
                conn.rollback()
            finally:
                conn.close()
                
    def _recover_from_leader_failure(self):
        """
        Initiate recovery actions when leader appears to be down.
        Called when AppendEntries timeout occurs multiple times.
        """
        with self.node_lock:
            if self.state != FOLLOWER:
                return
                
            logger.warning(f"Leader {self.leader_id} appears to be down, starting election")
            # Start election to find a new leader
            self._start_election()
            
    def _persist_state(self):
        """
        Persist critical state to disk to support crash recovery.
        """
        state = {
            'current_term': self.current_term,
            'voted_for': self.voted_for,
            'log': self.log
        }
        
        try:
            with open(f"node_{self.node_id}_state.json", 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Error persisting state: {e}")
