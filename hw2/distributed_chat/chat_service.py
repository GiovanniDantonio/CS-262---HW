"""
Chat service implementation for distributed fault-tolerant chat system.
Handles client-server communication for the chat application.
"""
import os
import sys
import time
import json
import logging
import threading
import hashlib
import sqlite3
from datetime import datetime
import grpc

# Import the generated protobuf modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from distributed_chat import distributed_chat_pb2 as pb2
from distributed_chat import distributed_chat_pb2_grpc as pb2_grpc

logger = logging.getLogger("chat_service")

class ChatService(pb2_grpc.ChatServiceServicer):
    """
    Implementation of the ChatService defined in the proto file.
    Handles client-server communication for the chat application.
    """
    
    def __init__(self, node):
        """
        Initialize the chat service with a reference to the node.
        
        Args:
            node: ChatNode instance this service belongs to
        """
        self.node = node
        # For streaming clients: map username -> context
        self.active_streams = {}
        self.stream_lock = threading.Lock()
        
    def _hash_password(self, password):
        """
        Hash a password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def _append_to_log(self, command_type, data):
        """
        Append an operation to the log and replicate to followers.
        
        Args:
            command_type: Type of command (e.g., "REGISTER", "SEND_MESSAGE")
            data: Dictionary containing command data
            
        Returns:
            bool: True if operation was successful
        """
        # Only the leader can append to log
        with self.node.node_lock:
            if self.node.state != 'leader':
                logger.warning(f"Cannot append to log: not leader (current state: {self.node.state})")
                return False
            
            # Create log entry
            entry = {
                'term': self.node.current_term,
                'data': json.dumps(data).encode('utf-8'),
                'command_type': command_type
            }
            
            # Append to local log
            self.node.log.append(entry)
            log_index = len(self.node.log)
            
            # Replicate to followers
            success_count = 1  # Count self
            for peer_id, peer_addr in self.node.peers.items():
                try:
                    # Create gRPC channel to peer
                    channel = grpc.insecure_channel(peer_addr)
                    stub = pb2_grpc.ReplicationServiceStub(channel)
                    
                    # Get previous log info
                    prev_log_index = self.node.next_index[peer_id] - 1
                    prev_log_term = 0
                    if prev_log_index > 0 and prev_log_index <= len(self.node.log):
                        prev_log_term = self.node.log[prev_log_index - 1]['term']
                    
                    # Create AppendEntries request with new entry
                    pb_entry = pb2.LogEntry(
                        term=entry['term'],
                        index=log_index,
                        data=entry['data'],
                        command_type=entry['command_type']
                    )
                    
                    request = pb2.AppendEntriesRequest(
                        term=self.node.current_term,
                        leader_id=self.node.node_id,
                        prev_log_index=prev_log_index,
                        prev_log_term=prev_log_term,
                        entries=[pb_entry],
                        leader_commit=self.node.commit_index
                    )
                    
                    # Send request with timeout
                    response = stub.AppendEntries(request, timeout=0.5)
                    
                    # If response term is higher, revert to follower
                    if response.term > self.node.current_term:
                        self.node.current_term = response.term
                        self.node.state = 'follower'
                        self.node.voted_for = None
                        return False
                    
                    # If successful, update indices
                    if response.success:
                        self.node.next_index[peer_id] = log_index + 1
                        self.node.match_index[peer_id] = log_index
                        success_count += 1
                    else:
                        # If AppendEntries fails, decrement nextIndex and retry
                        self.node.next_index[peer_id] = max(1, min(self.node.next_index[peer_id] - 1, response.match_index + 1))
                        # We'll retry on next heartbeat
                
                except Exception as e:
                    logger.warning(f"Error replicating to {peer_id}: {e}")
            
            # If replicated to majority, commit the entry
            if success_count > (len(self.node.peers) + 1) / 2:
                self.node.commit_index = log_index
                # Apply entry to state machine
                with self.node.db_lock:
                    while self.node.last_applied < self.node.commit_index:
                        self.node.last_applied += 1
                        log_entry = self.node.log[self.node.last_applied - 1]
                        self._apply_entry_to_state_machine(log_entry)
                return True
            
            return False
    
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
    
    def _redirect_to_leader(self, context):
        """
        Add leader address to gRPC metadata for client to retry.
        
        Args:
            context: gRPC context
            
        Returns:
            bool: True if redirected, False if no leader known
        """
        if self.node.leader_id and self.node.leader_id != self.node.node_id:
            # Find leader address
            if self.node.leader_id in self.node.peers:
                leader_addr = self.node.peers[self.node.leader_id]
                context.set_trailing_metadata((
                    ('leader-id', self.node.leader_id),
                    ('leader-addr', leader_addr),
                ))
                return True
        return False
    
    # --- ChatService methods ---
    
    def Register(self, request, context):
        """
        Handle user registration.
        
        Args:
            request: UserCredentials protobuf message
            context: gRPC context
            
        Returns:
            Response protobuf message
        """
        logger.info(f"Register request for: {request.username}")
        
        # Check if we're the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                # Redirect to leader
                if self._redirect_to_leader(context):
                    return pb2.Response(
                        success=False,
                        message=f"Not leader, try leader at {self.node.peers[self.node.leader_id]}"
                    )
                else:
                    return pb2.Response(
                        success=False,
                        message="Not leader, and no leader known. Try again later."
                    )
            
            # Check if username already exists (to avoid unnecessary log entries)
            with self.node.db_lock:
                conn = sqlite3.connect(self.node.db_path)
                c = conn.cursor()
                c.execute("SELECT username FROM accounts WHERE username = ?", (request.username,))
                if c.fetchone():
                    conn.close()
                    return pb2.Response(success=False, message="Username already exists.")
                conn.close()
            
            # Append to log
            success = self._append_to_log('REGISTER', {
                'username': request.username,
                'password': request.password
            })
            
            if success:
                return pb2.Response(success=True, message="Account created successfully.")
            else:
                return pb2.Response(success=False, message="Failed to create account, could not reach consensus.")
    
    def Login(self, request, context):
        """
        Handle user login.
        
        Args:
            request: UserCredentials protobuf message
            context: gRPC context
            
        Returns:
            LoginResponse protobuf message
        """
        logger.info(f"Login attempt for: {request.username}")
        
        # Login can be handled by any node
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            c.execute("SELECT password FROM accounts WHERE username = ?", (request.username,))
            record = c.fetchone()
            
            if not record or record[0] != request.password:
                conn.close()
                return pb2.LoginResponse(
                    success=False, 
                    message="Invalid username or password.", 
                    unread_count=0
                )
            
            # Count unread messages
            c.execute("SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0", (request.username,))
            unread_count = c.fetchone()[0]
            conn.close()
            
            # Record login in the log (needs to be done by leader)
            with self.node.node_lock:
                if self.node.state == 'leader':
                    self._append_to_log('LOGIN', {
                        'username': request.username,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    # Try to forward to leader
                    try:
                        if self.node.leader_id and self.node.leader_id in self.node.peers:
                            channel = grpc.insecure_channel(self.node.peers[self.node.leader_id])
                            stub = pb2_grpc.ChatServiceStub(channel)
                            stub.Login(request)
                    except Exception as e:
                        logger.warning(f"Failed to forward login to leader: {e}")
            
            logger.info(f"Login successful for {request.username}. Unread: {unread_count}")
            return pb2.LoginResponse(
                success=True, 
                message="Login successful.", 
                unread_count=unread_count
            )
    
    def Logout(self, request, context):
        """
        Handle user logout.
        
        Args:
            request: Username protobuf message
            context: gRPC context
            
        Returns:
            Response protobuf message
        """
        logger.info(f"Logout request for: {request.username}")
        
        # Remove from active streams if present
        with self.stream_lock:
            if request.username in self.active_streams:
                del self.active_streams[request.username]
        
        return pb2.Response(success=True, message="Logged out successfully.")
    
    def DeleteAccount(self, request, context):
        """
        Handle account deletion.
        
        Args:
            request: Username protobuf message
            context: gRPC context
            
        Returns:
            Response protobuf message
        """
        logger.info(f"DeleteAccount request for: {request.username}")
        
        # Check if we're the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                # Redirect to leader
                if self._redirect_to_leader(context):
                    return pb2.Response(
                        success=False,
                        message=f"Not leader, try leader at {self.node.peers[self.node.leader_id]}"
                    )
                else:
                    return pb2.Response(
                        success=False,
                        message="Not leader, and no leader known. Try again later."
                    )
            
            # Get unread message count (for response)
            unread_count = 0
            with self.node.db_lock:
                conn = sqlite3.connect(self.node.db_path)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0", (request.username,))
                unread_count = c.fetchone()[0]
                conn.close()
            
            # Append to log
            success = self._append_to_log('DELETE_ACCOUNT', {
                'username': request.username
            })
            
            # Remove from active streams if present
            with self.stream_lock:
                if request.username in self.active_streams:
                    del self.active_streams[request.username]
            
            if success:
                return pb2.Response(
                    success=True, 
                    message=f"Account deleted. Unread messages: {unread_count}"
                )
            else:
                return pb2.Response(
                    success=False, 
                    message="Failed to delete account, could not reach consensus."
                )
    
    def ListAccounts(self, request, context):
        """
        Handle listing accounts.
        
        Args:
            request: AccountListRequest protobuf message
            context: gRPC context
            
        Returns:
            AccountListResponse protobuf message
        """
        logger.info(f"ListAccounts request: pattern='{request.pattern}', page={request.page}, per_page={request.per_page}")
        
        # This can be handled by any node (read-only)
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            
            pattern = request.pattern if request.pattern else "%"
            page = request.page if request.page > 0 else 1
            per_page = request.per_page if request.per_page > 0 else 10
            offset = (page - 1) * per_page
            
            c.execute(
                "SELECT username, created_at, last_login FROM accounts WHERE username LIKE ? ORDER BY username LIMIT ? OFFSET ?",
                (pattern, per_page, offset)
            )
            
            rows = c.fetchall()
            accounts = []
            for row in rows:
                accounts.append(pb2.Account(
                    username=row[0],
                    created_at=row[1] if row[1] is not None else "",
                    last_login=row[2] if row[2] is not None else ""
                ))
            
            conn.close()
            
            return pb2.AccountListResponse(
                accounts=accounts, 
                page=page, 
                per_page=per_page
            )
    
    def SendMessage(self, request, context):
        """
        Handle sending a message.
        
        Args:
            request: Message protobuf message
            context: gRPC context
            
        Returns:
            Response protobuf message
        """
        logger.info(f"SendMessage: from {request.sender} to {request.recipient}: {request.content}")
        
        # Check if we're the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                # Redirect to leader
                if self._redirect_to_leader(context):
                    return pb2.Response(
                        success=False,
                        message=f"Not leader, try leader at {self.node.peers[self.node.leader_id]}"
                    )
                else:
                    return pb2.Response(
                        success=False,
                        message="Not leader, and no leader known. Try again later."
                    )
            
            # Append to log
            success = self._append_to_log('SEND_MESSAGE', {
                'sender': request.sender,
                'recipient': request.recipient,
                'content': request.content
            })
            
            if success:
                return pb2.Response(success=True, message="Message sent successfully.")
            else:
                return pb2.Response(success=False, message="Failed to send message, could not reach consensus.")
    
    def GetMessages(self, request, context):
        """
        Handle fetching messages.
        
        Args:
            request: MessageRequest protobuf message
            context: gRPC context
            
        Returns:
            MessageList protobuf message
        """
        logger.info(f"GetMessages: for {request.username} (limit {request.count})")
        
        # This can be handled by any node (read-only)
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            
            try:
                c.execute(
                    "SELECT id, sender, recipient, content, timestamp, read FROM messages WHERE recipient = ? ORDER BY timestamp DESC LIMIT ?",
                    (request.username, request.count)
                )
                
                messages = []
                for row in c.fetchall():
                    messages.append(pb2.Message(
                        id=row[0],
                        sender=row[1],
                        recipient=row[2],
                        content=row[3],
                        timestamp=row[4],
                        read=bool(row[5])
                    ))
                
                return pb2.MessageList(messages=messages)
            
            except Exception as e:
                logger.error(f"Error in GetMessages: {e}")
                return pb2.MessageList(messages=[])
            
            finally:
                conn.close()
    
    def DeleteMessages(self, request, context):
        """
        Handle deletion of messages.
        
        Args:
            request: DeleteMessageRequest protobuf message
            context: gRPC context
            
        Returns:
            Response protobuf message
        """
        logger.info(f"DeleteMessages: for {request.username}, IDs: {request.message_ids}")
        
        if not request.message_ids:
            return pb2.Response(success=False, message="No message IDs provided.")
        
        # Check if we're the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                # Redirect to leader
                if self._redirect_to_leader(context):
                    return pb2.Response(
                        success=False,
                        message=f"Not leader, try leader at {self.node.peers[self.node.leader_id]}"
                    )
                else:
                    return pb2.Response(
                        success=False,
                        message="Not leader, and no leader known. Try again later."
                    )
            
            # Append to log
            success = self._append_to_log('DELETE_MESSAGES', {
                'username': request.username,
                'message_ids': list(request.message_ids)
            })
            
            if success:
                return pb2.Response(success=True, message=f"Deleted messages successfully.")
            else:
                return pb2.Response(success=False, message="Failed to delete messages, could not reach consensus.")
    
    def MarkAsRead(self, request, context):
        """
        Handle marking messages as read.
        
        Args:
            request: MarkAsReadRequest protobuf message
            context: gRPC context
            
        Returns:
            Response protobuf message
        """
        logger.info(f"MarkAsRead: for {request.username}, IDs: {request.message_ids}")
        
        if not request.message_ids:
            return pb2.Response(success=False, message="No message IDs provided.")
        
        # Check if we're the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                # Redirect to leader
                if self._redirect_to_leader(context):
                    return pb2.Response(
                        success=False,
                        message=f"Not leader, try leader at {self.node.peers[self.node.leader_id]}"
                    )
                else:
                    return pb2.Response(
                        success=False,
                        message="Not leader, and no leader known. Try again later."
                    )
            
            # Append to log
            success = self._append_to_log('MARK_AS_READ', {
                'username': request.username,
                'message_ids': list(request.message_ids)
            })
            
            if success:
                return pb2.Response(success=True, message=f"Marked messages as read successfully.")
            else:
                return pb2.Response(success=False, message="Failed to mark messages as read, could not reach consensus.")
    
    def StreamMessages(self, request, context):
        """
        Stream unread messages for the given user in real time.
        
        Args:
            request: Username protobuf message
            context: gRPC context
            
        Returns:
            Stream of Message protobuf messages
        """
        logger.info(f"StreamMessages: starting for user {request.username}")
        
        # Register this stream
        with self.stream_lock:
            self.active_streams[request.username] = context
        
        try:
            # Initial delivery of unread messages
            with self.node.db_lock:
                conn = sqlite3.connect(self.node.db_path)
                c = conn.cursor()
                c.execute(
                    "SELECT id, sender, recipient, content, timestamp, read FROM messages WHERE recipient = ? AND read = 0 ORDER BY timestamp DESC LIMIT 50",
                    (request.username,)
                )
                rows = c.fetchall()
                conn.close()
                
                for row in rows:
                    yield pb2.Message(
                        id=row[0],
                        sender=row[1],
                        recipient=row[2],
                        content=row[3],
                        timestamp=row[4],
                        read=bool(row[5])
                    )
            
            # Keep checking for new messages
            while True:
                # Wait a bit before checking again
                time.sleep(3)
                
                # Check for new unread messages
                with self.node.db_lock:
                    conn = sqlite3.connect(self.node.db_path)
                    c = conn.cursor()
                    c.execute(
                        "SELECT id, sender, recipient, content, timestamp, read FROM messages WHERE recipient = ? AND read = 0 ORDER BY timestamp DESC LIMIT 50",
                        (request.username,)
                    )
                    rows = c.fetchall()
                    conn.close()
                    
                    for row in rows:
                        yield pb2.Message(
                            id=row[0],
                            sender=row[1],
                            recipient=row[2],
                            content=row[3],
                            timestamp=row[4],
                            read=bool(row[5])
                        )
        
        except grpc.RpcError:
            logger.warning(f"StreamMessages: client {request.username} disconnected")
        
        finally:
            # Unregister this stream
            with self.stream_lock:
                if request.username in self.active_streams:
                    del self.active_streams[request.username]
