"""
Raft consensus algorithm implementation for fault-tolerant chat system.
This module provides the core replication and consensus logic for the distributed chat service.
"""
import enum
import json
import logging
import random
import threading
import time
from typing import Dict, List, Optional, Set, Tuple, Any

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("raft")

class NodeState(enum.Enum):
    """Represents the state of a Raft node in the consensus algorithm."""
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2

class LogEntry:
    """Represents a single entry in the Raft log."""
    def __init__(self, term: int, command: Dict[str, Any], index: int):
        """
        Initialize a log entry.
        
        Args:
            term: Term number when entry was created
            command: The actual command to be replicated (a dictionary representation of a command)
            index: The index position in the log
        """
        self.term = term
        self.command = command
        self.index = index
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for serialization."""
        return {
            "term": self.term,
            "command": self.command,
            "index": self.index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create a LogEntry instance from a dictionary."""
        return cls(
            term=data["term"],
            command=data["command"],
            index=data["index"]
        )

class RaftNode:
    """
    Implementation of a node in the Raft consensus algorithm.
    
    Each node maintains its state and communicates with other nodes
    to achieve consensus on the log of commands.
    """
    
    def __init__(self, node_id: str, peers: Dict[str, str], storage_dir: str):
        """
        Initialize a Raft node.
        
        Args:
            node_id: Unique identifier for this node
            peers: Dictionary mapping peer IDs to their network addresses
            storage_dir: Directory to store persistent state
        """
        # Persistent state on all servers
        self.current_term = 0
        self.voted_for = None
        self.log: List[LogEntry] = []
        
        # Volatile state on all servers
        self.commit_index = 0
        self.last_applied = 0
        
        # Volatile state on leaders (reinitialized after election)
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}
        
        # Additional node state
        self.node_id = node_id
        self.peers = peers
        self.state = NodeState.FOLLOWER
        self.storage_dir = storage_dir
        self.leader_id = None
        
        # Concurrency control
        self.mutex = threading.RLock()
        self.apply_cond = threading.Condition(self.mutex)
        
        # Election timeout
        self.election_timeout = self.new_election_timeout()
        self.last_heartbeat = time.time()
        
        # Storage for callbacks to RPC implementations
        self._rpc_callbacks = {}
        
        # Server management
        self.is_running = True
        self.background_threads = []
        
    def new_election_timeout(self) -> float:
        """Generate a new random election timeout between 150-300ms."""
        return random.uniform(0.15, 0.3)
    
    def register_rpc_callbacks(self, callbacks: Dict[str, callable]) -> None:
        """
        Register callbacks for RPC methods.
        
        Args:
            callbacks: Dictionary mapping RPC names to callback functions
        """
        self._rpc_callbacks = callbacks
    
    def start(self) -> None:
        """Start the Raft node and its background threads."""
        self.load_persistent_state()
        
        # Start background threads
        self.is_running = True
        election_thread = threading.Thread(target=self._election_timer_thread, daemon=True)
        commit_thread = threading.Thread(target=self._commit_entries_thread, daemon=True)
        
        self.background_threads = [election_thread, commit_thread]
        for thread in self.background_threads:
            thread.start()
            
        logger.info(f"Raft node {self.node_id} started (state: {self.state})")
    
    def stop(self) -> None:
        """Stop the Raft node and its background threads."""
        self.is_running = False
        
        # Wait for background threads to finish
        for thread in self.background_threads:
            thread.join(timeout=1.0)
        
        logger.info(f"Raft node {self.node_id} stopped")
    
    def save_persistent_state(self) -> None:
        """Save persistent state to disk."""
        pass  # To be implemented with actual file operations
    
    def load_persistent_state(self) -> None:
        """Load persistent state from disk."""
        pass  # To be implemented with actual file operations
    
    def _election_timer_thread(self) -> None:
        """Background thread for election timeout."""
        while self.is_running:
            time.sleep(0.01)  # Small sleep to prevent CPU spinning
            
            with self.mutex:
                if self.state == NodeState.LEADER:
                    self._send_heartbeats()
                    time.sleep(0.05)  # Send heartbeats every 50ms
                    continue
                
                elapsed = time.time() - self.last_heartbeat
                if elapsed >= self.election_timeout:
                    self._start_election()
    
    def _commit_entries_thread(self) -> None:
        """Background thread for applying committed entries."""
        while self.is_running:
            with self.apply_cond:
                while self.is_running and self.last_applied >= self.commit_index:
                    self.apply_cond.wait(timeout=0.1)
                
                if not self.is_running:
                    break
                
                # Apply committed entries
                if self.last_applied < self.commit_index:
                    self.last_applied += 1
                    entry = self.log[self.last_applied]
                    
                    # Apply the command to the state machine
                    self._apply_command(entry.command)
    
    def _apply_command(self, command: Dict[str, Any]) -> Any:
        """
        Apply a command to the state machine.
        
        This is typically overridden by a derived class that implements
        the actual state machine logic.
        
        Args:
            command: The command to apply
            
        Returns:
            The result of applying the command
        """
        # Default implementation just logs the command
        logger.debug(f"Applied command: {command}")
        return None
    
    def _start_election(self) -> None:
        """Start a leader election."""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.election_timeout = self.new_election_timeout()
        self.last_heartbeat = time.time()
        
        logger.info(f"Node {self.node_id} starting election for term {self.current_term}")
        
        # Vote for self
        votes_received = 1
        votes_needed = (len(self.peers) + 1) // 2 + 1
        
        # Request votes from all peers
        last_log_index = len(self.log) - 1 if self.log else 0
        last_log_term = self.log[-1].term if self.log else 0
        
        for peer_id, peer_addr in self.peers.items():
            # Prepare request vote arguments
            request = {
                "term": self.current_term,
                "candidate_id": self.node_id,
                "last_log_index": last_log_index,
                "last_log_term": last_log_term
            }
            
            # Send RequestVote RPC asynchronously
            if "request_vote" in self._rpc_callbacks:
                self._rpc_callbacks["request_vote"](peer_id, peer_addr, request, 
                    lambda result, error=None: self._handle_vote_response(result, error, self.current_term))
    
    def _handle_vote_response(self, response: Dict[str, Any], error: Optional[Exception], request_term: int) -> None:
        """Handle a response to a RequestVote RPC."""
        if error:
            logger.error(f"Error in RequestVote RPC: {error}")
            return
        
        with self.mutex:
            # Ignore responses from previous terms
            if request_term != self.current_term:
                return
            
            # If we're no longer a candidate, ignore the response
            if self.state != NodeState.CANDIDATE:
                return
            
            # If the response term is higher than ours, become a follower
            if response["term"] > self.current_term:
                self.current_term = response["term"]
                self.state = NodeState.FOLLOWER
                self.voted_for = None
                self.leader_id = None
                return
            
            # Count the vote if granted
            if response["vote_granted"]:
                votes_received += 1
                votes_needed = (len(self.peers) + 1) // 2 + 1
                
                # If we have a majority, become leader
                if votes_received >= votes_needed:
                    self._become_leader()
    
    def _become_leader(self) -> None:
        """Transition to leader state."""
        self.state = NodeState.LEADER
        self.leader_id = self.node_id
        
        # Initialize leader state
        next_index = len(self.log)
        self.next_index = {peer_id: next_index for peer_id in self.peers}
        self.match_index = {peer_id: 0 for peer_id in self.peers}
        
        logger.info(f"Node {self.node_id} became leader for term {self.current_term}")
        
        # Send initial heartbeats
        self._send_heartbeats()
    
    def _send_heartbeats(self) -> None:
        """Send heartbeats (empty AppendEntries) to all peers."""
        for peer_id, peer_addr in self.peers.items():
            self._send_append_entries(peer_id, peer_addr)
    
    def _send_append_entries(self, peer_id: str, peer_addr: str) -> None:
        """
        Send AppendEntries RPC to a peer.
        
        Args:
            peer_id: ID of the peer
            peer_addr: Network address of the peer
        """
        if "append_entries" not in self._rpc_callbacks:
            return
            
        with self.mutex:
            if self.state != NodeState.LEADER:
                return
                
            # Prepare entries to send
            next_idx = self.next_index[peer_id]
            prev_log_index = next_idx - 1
            prev_log_term = 0
            
            if prev_log_index >= 0 and prev_log_index < len(self.log):
                prev_log_term = self.log[prev_log_index].term
                
            entries = self.log[next_idx:] if next_idx < len(self.log) else []
            
            # Prepare append entries arguments
            request = {
                "term": self.current_term,
                "leader_id": self.node_id,
                "prev_log_index": prev_log_index,
                "prev_log_term": prev_log_term,
                "entries": [e.to_dict() for e in entries],
                "leader_commit": self.commit_index
            }
            
            # Send AppendEntries RPC asynchronously
            self._rpc_callbacks["append_entries"](peer_id, peer_addr, request,
                lambda result, error=None: self._handle_append_entries_response(result, error, peer_id, len(entries)))
    
    def _handle_append_entries_response(self, response: Dict[str, Any], error: Optional[Exception], 
                                       peer_id: str, entries_sent: int) -> None:
        """Handle a response to an AppendEntries RPC."""
        if error:
            logger.error(f"Error in AppendEntries RPC to {peer_id}: {error}")
            return
            
        with self.mutex:
            # If we're no longer leader, ignore the response
            if self.state != NodeState.LEADER:
                return
                
            # If the response term is higher than ours, become a follower
            if response["term"] > self.current_term:
                self.current_term = response["term"]
                self.state = NodeState.FOLLOWER
                self.voted_for = None
                self.leader_id = None
                return
                
            if response["success"]:
                # Update nextIndex and matchIndex for the follower
                self.match_index[peer_id] = self.next_index[peer_id] + entries_sent - 1
                self.next_index[peer_id] = self.match_index[peer_id] + 1
                
                # Check if we can commit any new entries
                self._update_commit_index()
            else:
                # Follower's log is inconsistent with leader's; decrement nextIndex and retry
                self.next_index[peer_id] = max(1, self.next_index[peer_id] - 1)
                # Retry immediately with the updated nextIndex
                self._send_append_entries(peer_id, self.peers[peer_id])
    
    def _update_commit_index(self) -> None:
        """Update the commit index if possible."""
        # Find the highest log index that is replicated on a majority of servers
        for n in range(self.commit_index + 1, len(self.log)):
            if self.log[n].term == self.current_term:
                # Count how many servers have this entry
                count = 1  # Leader has it
                for peer_id in self.peers:
                    if self.match_index[peer_id] >= n:
                        count += 1
                
                # If we have a majority, update commit_index
                if count > (len(self.peers) + 1) // 2:
                    self.commit_index = n
                    self.apply_cond.notify()
                    return
    
    def append_command(self, command: Dict[str, Any]) -> bool:
        """
        Append a new command to the log (leader only).
        
        Args:
            command: The command to append
            
        Returns:
            True if the command was appended successfully, False otherwise
        """
        with self.mutex:
            if self.state != NodeState.LEADER:
                return False
                
            # Create a new log entry
            index = len(self.log)
            entry = LogEntry(
                term=self.current_term,
                command=command,
                index=index
            )
            
            # Append to local log
            self.log.append(entry)
            
            # Update matchIndex for leader itself
            self.match_index[self.node_id] = index
            
            # Trigger immediate replication to followers
            for peer_id, peer_addr in self.peers.items():
                self._send_append_entries(peer_id, peer_addr)
                
            return True
    
    def handle_request_vote(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a RequestVote RPC from a candidate.
        
        Args:
            request: The RequestVote request parameters
            
        Returns:
            The RequestVote response
        """
        with self.mutex:
            # If the request term is less than our current term, reject the vote
            if request["term"] < self.current_term:
                return {
                    "term": self.current_term,
                    "vote_granted": False
                }
                
            # If the request term is greater than our current term, update our term
            if request["term"] > self.current_term:
                self.current_term = request["term"]
                self.state = NodeState.FOLLOWER
                self.voted_for = None
                self.leader_id = None
                
            # Determine if we should grant the vote
            vote_granted = False
            
            # Check if we've already voted for someone else in this term
            if self.voted_for is None or self.voted_for == request["candidate_id"]:
                # Check if candidate's log is at least as up-to-date as ours
                last_log_index = len(self.log) - 1 if self.log else 0
                last_log_term = self.log[-1].term if self.log else 0
                
                log_is_up_to_date = (
                    request["last_log_term"] > last_log_term or
                    (request["last_log_term"] == last_log_term and 
                     request["last_log_index"] >= last_log_index)
                )
                
                if log_is_up_to_date:
                    vote_granted = True
                    self.voted_for = request["candidate_id"]
                    self.last_heartbeat = time.time()  # Reset election timeout
                    
            return {
                "term": self.current_term,
                "vote_granted": vote_granted
            }
    
    def handle_append_entries(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an AppendEntries RPC from the leader.
        
        Args:
            request: The AppendEntries request parameters
            
        Returns:
            The AppendEntries response
        """
        with self.mutex:
            # If the request term is less than our current term, reject
            if request["term"] < self.current_term:
                return {
                    "term": self.current_term,
                    "success": False,
                    "match_index": 0
                }
                
            # Reset election timeout since we've heard from the leader
            self.last_heartbeat = time.time()
            
            # If the request term is greater than our current term, update our term
            if request["term"] > self.current_term:
                self.current_term = request["term"]
                self.voted_for = None
                
            # Always become a follower when we get a valid AppendEntries
            if self.state != NodeState.FOLLOWER:
                self.state = NodeState.FOLLOWER
                
            # Update leader ID
            self.leader_id = request["leader_id"]
            
            # Check if log contains an entry at prevLogIndex with prevLogTerm
            prev_log_index = request["prev_log_index"]
            
            # If our log is too short, fail
            if prev_log_index >= len(self.log):
                return {
                    "term": self.current_term,
                    "success": False,
                    "match_index": len(self.log) - 1
                }
                
            # If we have an entry at prevLogIndex with a different term, fail
            if prev_log_index >= 0 and (
                prev_log_index >= len(self.log) or
                self.log[prev_log_index].term != request["prev_log_term"]
            ):
                # Find the first index in the conflicting term
                match_index = min(prev_log_index - 1, len(self.log) - 1)
                return {
                    "term": self.current_term,
                    "success": False,
                    "match_index": max(0, match_index)
                }
                
            # If we get here, we have a match at prevLogIndex
            
            # Process any new entries
            entries = [LogEntry.from_dict(e) for e in request["entries"]]
            
            if entries:
                # If existing entries conflict with new entries, delete them and all that follow
                insert_index = prev_log_index + 1
                
                # Truncate log if necessary
                if insert_index < len(self.log):
                    self.log = self.log[:insert_index]
                    
                # Append any new entries not already in the log
                self.log.extend(entries)
                
            # Update commit index if leader's commit index is higher
            if request["leader_commit"] > self.commit_index:
                self.commit_index = min(request["leader_commit"], len(self.log) - 1)
                self.apply_cond.notify()
                
            return {
                "term": self.current_term,
                "success": True,
                "match_index": prev_log_index + len(entries)
            }
            
    def get_cluster_status(self) -> Dict[str, Any]:
        """
        Get the current status of the Raft cluster.
        
        Returns:
            A dictionary with cluster status information
        """
        with self.mutex:
            members = []
            for peer_id, peer_addr in self.peers.items():
                state = "unknown"
                last_seen = 0
                
                # For now, just report peers as "connected"
                # In a real implementation, track heartbeat responses
                members.append({
                    "id": peer_id,
                    "address": peer_addr,
                    "state": state,
                    "last_seen": last_seen
                })
                
            # Add self to members
            members.append({
                "id": self.node_id,
                "address": "self",
                "state": self.state.name.lower(),
                "last_seen": int(time.time())
            })
                
            return {
                "leader_id": self.leader_id,
                "current_term": self.current_term,
                "members": members
            }
            
    def is_leader(self) -> bool:
        """Check if this node is the current leader."""
        with self.mutex:
            return self.state == NodeState.LEADER
