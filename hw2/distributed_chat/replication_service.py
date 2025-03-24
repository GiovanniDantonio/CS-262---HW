"""
Replication service implementation for distributed fault-tolerant chat system.
Handles server-to-server communication for consensus and replication.
"""
import os
import sys
import time
import json
import logging
import threading
import grpc
import sqlite3

# Import the generated protobuf modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from distributed_chat import distributed_chat_pb2 as pb2
from distributed_chat import distributed_chat_pb2_grpc as pb2_grpc

logger = logging.getLogger("replication_service")

class ReplicationService(pb2_grpc.ReplicationServiceServicer):
    """
    Implementation of the ReplicationService defined in the proto file.
    Handles server-to-server communication for Raft consensus protocol.
    """
    
    def __init__(self, node):
        """
        Initialize the replication service with a reference to the node.
        
        Args:
            node: ChatNode instance this service belongs to
        """
        self.node = node
    
    def RequestVote(self, request, context):
        """
        Handle vote requests from candidate nodes.
        
        Args:
            request: VoteRequest protobuf message containing term, candidate_id, etc.
            context: gRPC context
            
        Returns:
            VoteResponse protobuf message
        """
        with self.node.node_lock:
            logger.debug(f"Received vote request from {request.candidate_id} for term {request.term}")
            
            # If request term is lower than current term, reject vote
            if request.term < self.node.current_term:
                return pb2.VoteResponse(term=self.node.current_term, vote_granted=False)
            
            # If request term is higher than current term, update term and revert to follower
            if request.term > self.node.current_term:
                self.node.current_term = request.term
                self.node.state = 'follower'
                self.node.voted_for = None
            
            # Check if we can vote for this candidate
            vote_granted = False
            if (self.node.voted_for is None or self.node.voted_for == request.candidate_id):
                # Check if candidate's log is at least as up-to-date as ours
                last_log_index = len(self.node.log)
                last_log_term = self.node.log[-1]['term'] if self.node.log else 0
                
                if (request.last_log_term > last_log_term or 
                    (request.last_log_term == last_log_term and 
                     request.last_log_index >= last_log_index)):
                    # Grant vote
                    vote_granted = True
                    self.node.voted_for = request.candidate_id
                    # Reset election timeout when we grant a vote
                    self.node.last_heartbeat = time.time()
            
            logger.debug(f"Vote granted: {vote_granted}")
            return pb2.VoteResponse(term=self.node.current_term, vote_granted=vote_granted)
    
    def AppendEntries(self, request, context):
        """
        Handle append entries requests (used for both log replication and heartbeats).
        
        Args:
            request: AppendEntriesRequest protobuf message
            context: gRPC context
            
        Returns:
            AppendEntriesResponse protobuf message
        """
        with self.node.node_lock:
            logger.debug(f"Received AppendEntries from {request.leader_id} for term {request.term}")
            
            # Reply false if term < currentTerm
            if request.term < self.node.current_term:
                return pb2.AppendEntriesResponse(
                    term=self.node.current_term,
                    success=False,
                    match_index=0
                )
            
            # Valid leader, update state
            self.node.last_heartbeat = time.time()
            self.node.leader_id = request.leader_id
            
            # If RPC request contains term T > currentTerm, set currentTerm = T
            if request.term > self.node.current_term:
                self.node.current_term = request.term
                self.node.voted_for = None
            
            # Ensure we're a follower since we received valid AppendEntries
            if self.node.state != 'follower':
                self.node.state = 'follower'
            
            # Check if log contains an entry at prevLogIndex with prevLogTerm
            if request.prev_log_index > 0:
                if len(self.node.log) < request.prev_log_index:
                    # Log doesn't have prevLogIndex entry
                    return pb2.AppendEntriesResponse(
                        term=self.node.current_term,
                        success=False,
                        match_index=len(self.node.log)
                    )
                
                if request.prev_log_index > 0 and self.node.log[request.prev_log_index - 1]['term'] != request.prev_log_term:
                    # Log has prevLogIndex but terms don't match
                    # Delete the existing entry and all that follow
                    self.node.log = self.node.log[:request.prev_log_index - 1]
                    return pb2.AppendEntriesResponse(
                        term=self.node.current_term,
                        success=False,
                        match_index=len(self.node.log)
                    )
            
            # Process log entries
            if request.entries:
                # Convert entries to more usable format
                entries = []
                for entry in request.entries:
                    entries.append({
                        'term': entry.term,
                        'index': entry.index,
                        'data': entry.data,
                        'command_type': entry.command_type
                    })
                
                # Find where logs diverge, if at all
                current_idx = request.prev_log_index
                for i, entry in enumerate(entries):
                    if current_idx + i + 1 > len(self.node.log) or self.node.log[current_idx + i]['term'] != entry['term']:
                        # Cut log here and append new entries
                        self.node.log = self.node.log[:current_idx + i]
                        self.node.log.extend(entries[i:])
                        break
            
            # Update commit index if leader commit > commit index
            if request.leader_commit > self.node.commit_index:
                self.node.commit_index = min(request.leader_commit, len(self.node.log))
                # Apply log entries up to new commit index
                self._apply_log_entries()
            
            return pb2.AppendEntriesResponse(
                term=self.node.current_term,
                success=True,
                match_index=len(self.node.log)
            )
    
    def SyncData(self, request, context):
        """
        Synchronize log data between servers.
        
        Args:
            request: SyncRequest protobuf message
            context: gRPC context
            
        Returns:
            SyncResponse protobuf message
        """
        with self.node.node_lock:
            logger.debug(f"Received SyncData request from {context.peer()}, from_index={request.from_index}, to_index={request.to_index}")
            
            # Collect requested log entries
            entries = []
            for i in range(request.from_index, min(request.to_index + 1, len(self.node.log) + 1)):
                if i > 0 and i <= len(self.node.log):
                    log_entry = self.node.log[i - 1]
                    pb_entry = pb2.LogEntry(
                        term=log_entry['term'],
                        index=i,
                        data=log_entry['data'],
                        command_type=log_entry['command_type']
                    )
                    entries.append(pb_entry)
            
            return pb2.SyncResponse(entries=entries, success=True)
    
    def GetState(self, request, context):
        """
        Get the current state of this node (for debugging and recovery).
        
        Args:
            request: GetStateRequest protobuf message
            context: gRPC context
            
        Returns:
            StateResponse protobuf message
        """
        with self.node.node_lock:
            logger.debug(f"Received GetState request from {context.peer()}")
            
            response = pb2.StateResponse(
                current_term=self.node.current_term,
                voted_for=self.node.voted_for or "",
                commit_index=self.node.commit_index,
                last_applied=self.node.last_applied,
                success=True
            )
            
            # Add log entries if requested
            if request.include_log_entries:
                from_idx = max(1, request.from_log_index)
                for i in range(from_idx, len(self.node.log) + 1):
                    log_entry = self.node.log[i - 1]
                    pb_entry = pb2.LogEntry(
                        term=log_entry['term'],
                        index=i,
                        data=log_entry['data'],
                        command_type=log_entry['command_type']
                    )
                    response.log_entries.append(pb_entry)
            
            return response
    
    def _apply_log_entries(self):
        """
        Apply committed log entries to the state machine.
        """
        with self.node.db_lock:
            while self.node.last_applied < self.node.commit_index:
                self.node.last_applied += 1
                log_entry = self.node.log[self.node.last_applied - 1]
                
                # Apply the entry to the state machine
                self._apply_entry_to_state_machine(log_entry)
                
                logger.debug(f"Applied log entry {self.node.last_applied}: {log_entry['command_type']}")
    
    def _apply_entry_to_state_machine(self, log_entry):
        """
        Apply a log entry to the state machine (database).
        
        Args:
            log_entry: Log entry to apply
        """
        try:
            # Parse command from log entry
            command_type = log_entry['command_type']
            command_data = json.loads(log_entry['data'].decode('utf-8'))
            
            conn = None
            try:
                conn = sqlite3.connect(self.node.db_path)
                c = conn.cursor()
                
                # Execute command based on type
                if command_type == 'REGISTER':
                    c.execute(
                        "INSERT INTO accounts (username, password) VALUES (?, ?)",
                        (command_data['username'], command_data['password'])
                    )
                elif command_type == 'LOGIN':
                    c.execute(
                        "UPDATE accounts SET last_login = ? WHERE username = ?",
                        (command_data['timestamp'], command_data['username'])
                    )
                elif command_type == 'DELETE_ACCOUNT':
                    c.execute("DELETE FROM messages WHERE sender = ? OR recipient = ?", 
                             (command_data['username'], command_data['username']))
                    c.execute("DELETE FROM accounts WHERE username = ?", 
                             (command_data['username'],))
                elif command_type == 'SEND_MESSAGE':
                    c.execute(
                        "INSERT INTO messages (sender, recipient, content, read) VALUES (?, ?, ?, 0)",
                        (command_data['sender'], command_data['recipient'], command_data['content'])
                    )
                elif command_type == 'DELETE_MESSAGES':
                    placeholders = ','.join('?' for _ in command_data['message_ids'])
                    params = command_data['message_ids'] + [command_data['username'], command_data['username']]
                    c.execute(
                        f"DELETE FROM messages WHERE id IN ({placeholders}) AND (sender = ? OR recipient = ?)",
                        params
                    )
                elif command_type == 'MARK_AS_READ':
                    placeholders = ','.join('?' for _ in command_data['message_ids'])
                    params = command_data['message_ids'] + [command_data['username']]
                    c.execute(
                        f"UPDATE messages SET read = 1 WHERE id IN ({placeholders}) AND recipient = ?",
                        params
                    )
                
                conn.commit()
                
            except Exception as e:
                logger.error(f"Error applying log entry to state machine: {e}")
                if conn:
                    conn.rollback()
            finally:
                if conn:
                    conn.close()
                
        except Exception as e:
            logger.error(f"Error parsing log entry: {e}")
