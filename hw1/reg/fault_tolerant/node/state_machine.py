"""
State machine implementation for fault-tolerant chat system.
Implements Raft consensus algorithm for leader election and log replication.
"""
import logging
import sqlite3
import threading
import time
from typing import Dict, List, Optional, Tuple
import random
import json

from ..common.protocol import MessageType, NodeRole, StatusCode

logger = logging.getLogger(__name__)

class LogEntry:
    def __init__(self, term: int, command: Dict, index: int):
        self.term = term
        self.command = command
        self.index = index

class StateMachine:
    def __init__(self, node_id: int, nodes: List[Dict], db_path: str):
        self.node_id = node_id
        self.nodes = nodes
        self.db_path = db_path
        
        # Persistent state
        self.current_term = 0
        self.voted_for = None
        self.log: List[LogEntry] = []
        
        # Volatile state
        self.commit_index = 0
        self.last_applied = 0
        self.role = NodeRole.FOLLOWER
        self.leader_id = None
        self.votes_received = set()
        
        # Leader volatile state
        self.next_index: Dict[int, int] = {}
        self.match_index: Dict[int, int] = {}
        
        # Initialize database
        self._init_db()
        
        # Election timer
        self.last_heartbeat = time.time()
        self.election_timeout = self._get_random_timeout()
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create tables
        c.execute('''CREATE TABLE IF NOT EXISTS accounts (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read INTEGER DEFAULT 0,
            FOREIGN KEY (sender) REFERENCES accounts(username),
            FOREIGN KEY (recipient) REFERENCES accounts(username)
        )''')
        
        # Create tables for Raft state
        c.execute('''CREATE TABLE IF NOT EXISTS raft_state (
            current_term INTEGER,
            voted_for TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS raft_log (
            index_id INTEGER PRIMARY KEY,
            term INTEGER,
            command TEXT
        )''')
        
        conn.commit()
        conn.close()
    
    def apply_command(self, command: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Apply a command to the state machine."""
        with self.lock:
            if self.role != NodeRole.LEADER:
                if self.leader_id:
                    leader_node = None
                    for node in self.nodes:
                        if node["id"] == self.leader_id:
                            leader_node = node
                            break
                    if leader_node:
                        return StatusCode.REDIRECT, {
                            "leader_host": leader_node["host"],
                            "leader_port": leader_node["port"]
                        }
                return StatusCode.ERROR, {"message": "No leader available"}
            
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                
                msg_type = MessageType[command["type"]]
                data = command["data"]
                
                if msg_type == MessageType.CREATE_ACCOUNT:
                    return self._handle_create_account(c, data)
                elif msg_type == MessageType.LOGIN:
                    return self._handle_login(c, data)
                elif msg_type == MessageType.LOGOUT:
                    return self._handle_logout(c, data)
                elif msg_type == MessageType.DELETE_ACCOUNT:
                    return self._handle_delete_account(c, data)
                elif msg_type == MessageType.LIST_ACCOUNTS:
                    return self._handle_list_accounts(c)
                elif msg_type == MessageType.SEND_MESSAGE:
                    return self._handle_send_message(c, data)
                elif msg_type == MessageType.GET_MESSAGES:
                    return self._handle_get_messages(c, data)
                elif msg_type == MessageType.DELETE_MESSAGES:
                    return self._handle_delete_messages(c, data)
                elif msg_type == MessageType.MARK_AS_READ:
                    return self._handle_mark_as_read(c, data)
                else:
                    return StatusCode.ERROR, {"message": "Unknown command"}
                
            except Exception as e:
                logger.error(f"Error applying command: {e}")
                return StatusCode.ERROR, {"message": str(e)}
            finally:
                conn.close()
    
    def _handle_create_account(self, c: sqlite3.Cursor, data: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle account creation."""
        try:
            c.execute("INSERT INTO accounts (username, password) VALUES (?, ?)",
                     (data["username"], data["password"]))
            c.connection.commit()
            return StatusCode.SUCCESS, None
        except sqlite3.IntegrityError:
            return StatusCode.ERROR, {"message": "Username already exists"}
    
    def _handle_login(self, c: sqlite3.Cursor, data: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle login."""
        c.execute("SELECT password FROM accounts WHERE username = ?",
                 (data["username"],))
        row = c.fetchone()
        
        if row and row[0] == data["password"]:
            c.execute("UPDATE accounts SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
                     (data["username"],))
            c.connection.commit()
            return StatusCode.SUCCESS, None
        return StatusCode.ERROR, {"message": "Invalid credentials"}
    
    def _handle_logout(self, c: sqlite3.Cursor, data: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle logout."""
        return StatusCode.SUCCESS, None
    
    def _handle_delete_account(self, c: sqlite3.Cursor, data: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle account deletion."""
        c.execute("DELETE FROM accounts WHERE username = ?", (data["username"],))
        c.connection.commit()
        return StatusCode.SUCCESS, None
    
    def _handle_list_accounts(self, c: sqlite3.Cursor) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle account listing."""
        c.execute("SELECT username FROM accounts")
        accounts = [row[0] for row in c.fetchall()]
        return StatusCode.SUCCESS, {"accounts": accounts}
    
    def _handle_send_message(self, c: sqlite3.Cursor, data: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle message sending."""
        c.execute("INSERT INTO messages (sender, recipient, content) VALUES (?, ?, ?)",
                 (data["sender"], data["recipient"], data["content"]))
        c.connection.commit()
        return StatusCode.SUCCESS, None
    
    def _handle_get_messages(self, c: sqlite3.Cursor, data: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle message retrieval."""
        c.execute("""
            SELECT id, sender, recipient, content, timestamp, read
            FROM messages
            WHERE recipient = ?
            ORDER BY timestamp DESC
        """, (data["username"],))
        
        messages = [{
            "id": row[0],
            "sender": row[1],
            "recipient": row[2],
            "content": row[3],
            "timestamp": row[4],
            "read": bool(row[5])
        } for row in c.fetchall()]
        
        return StatusCode.SUCCESS, {"messages": messages}
    
    def _handle_delete_messages(self, c: sqlite3.Cursor, data: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle message deletion."""
        c.execute("DELETE FROM messages WHERE id IN ({})".format(
            ",".join("?" * len(data["message_ids"]))),
            data["message_ids"])
        c.connection.commit()
        return StatusCode.SUCCESS, None
    
    def _handle_mark_as_read(self, c: sqlite3.Cursor, data: Dict) -> Tuple[StatusCode, Optional[Dict]]:
        """Handle marking messages as read."""
        c.execute("UPDATE messages SET read = 1 WHERE id IN ({})".format(
            ",".join("?" * len(data["message_ids"]))),
            data["message_ids"])
        c.connection.commit()
        return StatusCode.SUCCESS, None
    
    def _get_random_timeout(self) -> float:
        """Get random election timeout between 150-300ms."""
        return random.uniform(0.15, 0.3)
    
    def _reset_election_timer(self) -> None:
        """Reset election timer."""
        self.last_heartbeat = time.time()
        self.election_timeout = self._get_random_timeout()
    
    def check_election_timeout(self) -> bool:
        """Check if election timeout has occurred."""
        with self.lock:
            if self.role == NodeRole.LEADER:
                return False
            
            elapsed = time.time() - self.last_heartbeat
            return elapsed > self.election_timeout
    
    def start_election(self) -> None:
        """Start leader election."""
        with self.lock:
            self.role = NodeRole.CANDIDATE
            self.current_term += 1
            self.voted_for = self.node_id
            self.votes_received = {self.node_id}
            self._reset_election_timer()
            
            # Persist state
            self._persist_state()
            
            # Send RequestVote RPCs
            for node in self.nodes:
                if node["id"] != self.node_id:
                    self._send_request_vote(node["id"])
    
    def handle_vote_request(self, term: int, candidate_id: int, 
                          last_log_index: int, last_log_term: int) -> Tuple[int, bool]:
        """Handle incoming RequestVote RPC."""
        with self.lock:
            if term < self.current_term:
                return self.current_term, False
            
            if term > self.current_term:
                self._become_follower(term)
            
            if (self.voted_for is None or self.voted_for == candidate_id) and \
               self._is_log_up_to_date(last_log_index, last_log_term):
                self.voted_for = candidate_id
                self._persist_state()
                return self.current_term, True
            
            return self.current_term, False
    
    def handle_vote_response(self, term: int, voter_id: int, granted: bool) -> None:
        """Handle vote response."""
        with self.lock:
            if self.role != NodeRole.CANDIDATE or term != self.current_term:
                return
            
            if term > self.current_term:
                self._become_follower(term)
                return
            
            if granted:
                self.votes_received.add(voter_id)
                if len(self.votes_received) > len(self.nodes) // 2:
                    self._become_leader()
    
    def _become_follower(self, term: int) -> None:
        """Convert to follower state."""
        self.role = NodeRole.FOLLOWER
        self.current_term = term
        self.voted_for = None
        self.leader_id = None
        self._reset_election_timer()
        self._persist_state()
    
    def _become_leader(self) -> None:
        """Convert to leader state."""
        self.role = NodeRole.LEADER
        self.leader_id = self.node_id
        
        # Initialize leader state
        last_log_index = len(self.log)
        self.next_index = {node["id"]: last_log_index + 1 for node in self.nodes}
        self.match_index = {node["id"]: 0 for node in self.nodes}
        
        # Send initial empty AppendEntries
        self._send_heartbeat()
    
    def _is_log_up_to_date(self, last_log_index: int, last_log_term: int) -> bool:
        """Check if candidate's log is at least as up-to-date as receiver's log."""
        if not self.log:
            return True
        
        our_last_term = self.log[-1].term
        our_last_index = len(self.log) - 1
        
        if last_log_term != our_last_term:
            return last_log_term > our_last_term
        return last_log_index >= our_last_index
    
    def _persist_state(self) -> None:
        """Persist Raft state to disk."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Update Raft state
        c.execute("DELETE FROM raft_state")
        c.execute("INSERT INTO raft_state (current_term, voted_for) VALUES (?, ?)",
                 (self.current_term, self.voted_for))
        
        conn.commit()
        conn.close()
    
    def _send_request_vote(self, target_id: int) -> None:
        """Send RequestVote RPC to target node."""
        last_log_index = len(self.log) - 1
        last_log_term = self.log[last_log_index].term if self.log else 0
        
        # This would be implemented by the node server to actually send the RPC
        pass
    
    def _send_heartbeat(self) -> None:
        """Send heartbeat (empty AppendEntries) to all followers."""
        for node in self.nodes:
            if node["id"] != self.node_id:
                self._send_append_entries(node["id"])
    
    def _send_append_entries(self, target_id: int) -> None:
        """Send AppendEntries RPC to target node."""
        prev_log_index = self.next_index[target_id] - 1
        prev_log_term = self.log[prev_log_index].term if prev_log_index >= 0 and self.log else 0
        
        # Get entries to send
        entries = self.log[self.next_index[target_id]:]
        
        # This would be implemented by the node server to actually send the RPC
        pass
