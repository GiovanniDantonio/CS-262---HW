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
        return self.node._append_to_log(command_type, data)
        
    def _apply_entry_to_state_machine(self, log_entry):
        """
        Apply a log entry to the state machine (database).
        
        Args:
            log_entry: Log entry to apply
        """
        try:
            data = json.loads(log_entry['data'])
            conn = None
            
            try:
                with self.node.db_lock:
                    conn = sqlite3.connect(self.node.db_path)
                    c = conn.cursor()
                    
                    if log_entry['command_type'] == 'REGISTER':
                        # Hash the password before storing
                        hashed_password = hashlib.sha256(data['password'].encode('utf-8')).hexdigest()
                        c.execute(
                            "INSERT INTO accounts (username, password) VALUES (?, ?)",
                            (data['username'], hashed_password)
                        )
                        logger.info(f"Registered user: {data['username']}")
                        
                    elif log_entry['command_type'] == 'LOGIN':
                        c.execute(
                            "UPDATE accounts SET last_login = ? WHERE username = ?",
                            (data['timestamp'], data['username'])
                        )
                        
                    elif log_entry['command_type'] == 'SEND_MESSAGE':
                        c.execute(
                            "INSERT INTO messages (sender, recipient, content) VALUES (?, ?, ?)",
                            (data['sender'], data['recipient'], data['content'])
                        )
                        
                    elif log_entry['command_type'] == 'DELETE_MESSAGES':
                        for msg_id in data['message_ids']:
                            c.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
                            
                    elif log_entry['command_type'] == 'MARK_AS_READ':
                        for msg_id in data['message_ids']:
                            c.execute(
                                "UPDATE messages SET read = 1 WHERE id = ? AND recipient = ?",
                                (msg_id, data['username'])
                            )
                            
                    elif log_entry['command_type'] == 'DELETE_ACCOUNT':
                        c.execute("DELETE FROM messages WHERE sender = ? OR recipient = ?",
                                (data['username'], data['username']))
                        c.execute("DELETE FROM accounts WHERE username = ?",
                                (data['username'],))
                    
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Error applying log entry to state machine: {e}")
                if conn:
                    conn.rollback()
                raise
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            logger.error(f"Error parsing log entry: {e}")
            raise
    
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
        
        # Check if username already exists (can be done by any node)
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            c.execute("SELECT 1 FROM accounts WHERE username = ?", (request.username,))
            if c.fetchone():
                conn.close()
                return pb2.Response(success=False, message="Username already exists")
            conn.close()
        
        # Forward write operation to leader if we're not the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                try:
                    if self.node.leader_id and self.node.leader_id in self.node.peers:
                        channel = grpc.insecure_channel(self.node.peers[self.node.leader_id])
                        stub = pb2_grpc.ChatServiceStub(channel)
                        return stub.Register(request)
                    else:
                        # If we don't know the leader, handle it locally
                        logger.warning("No leader known, handling registration locally")
                except Exception as e:
                    logger.warning(f"Failed to forward to leader: {e}, handling locally")
            
            # We're either the leader or failed to forward - handle the registration
            success = self._append_to_log('REGISTER', {
                'username': request.username,
                'password': request.password
            })
            
            if success:
                return pb2.Response(success=True, message="Registration successful")
            else:
                return pb2.Response(success=False, message="Registration failed, please try again")

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
        
        # Hash the password for comparison
        hashed_password = hashlib.sha256(request.password.encode('utf-8')).hexdigest()
        
        # Login can be handled by any node
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            c.execute("SELECT password FROM accounts WHERE username = ?", (request.username,))
            record = c.fetchone()
            
            if not record or record[0] != hashed_password:
                conn.close()
                return pb2.LoginResponse(
                    success=False, 
                    message="Invalid username or password", 
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
                message="Login successful", 
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
        logger.info(f"ListAccounts request with pattern: {request.pattern}")
        
        # Read operations can be handled by any node
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            
            try:
                c.execute(
                    "SELECT username FROM accounts WHERE username LIKE ? ORDER BY username",
                    (request.pattern.replace('%', '*'),)
                )
                usernames = [row[0] for row in c.fetchall()]
                
                return pb2.AccountListResponse(usernames=usernames)
            finally:
                conn.close()

    def SendMessage(self, request, context):
        """
        Handle sending a message.
        
        Args:
            request: Message protobuf message
            context: gRPC context
            
        Returns:
            Response protobuf message
        """
        logger.info(f"SendMessage from {request.sender} to {request.recipient}")
        
        # Verify both users exist before attempting to send
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            
            # Check sender exists
            c.execute("SELECT 1 FROM accounts WHERE username = ?", (request.sender,))
            if not c.fetchone():
                conn.close()
                return pb2.Response(success=False, message="Sender account does not exist")
            
            # Check recipient exists
            c.execute("SELECT 1 FROM accounts WHERE username = ?", (request.recipient,))
            if not c.fetchone():
                conn.close()
                return pb2.Response(success=False, message="Recipient account does not exist")
            
            conn.close()
        
        # Forward write operation to leader if we're not the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                try:
                    if self.node.leader_id and self.node.leader_id in self.node.peers:
                        channel = grpc.insecure_channel(self.node.peers[self.node.leader_id])
                        stub = pb2_grpc.ChatServiceStub(channel)
                        return stub.SendMessage(request)
                    else:
                        # If we don't know the leader, handle it locally
                        logger.warning("No leader known, handling message locally")
                except Exception as e:
                    logger.warning(f"Failed to forward to leader: {e}, handling locally")
            
            # We're either the leader or failed to forward - handle the message
            success = self._append_to_log('SEND_MESSAGE', {
                'sender': request.sender,
                'recipient': request.recipient,
                'content': request.content
            })
            
            if success:
                # Notify recipient's stream if active
                with self.stream_lock:
                    if request.recipient in self.active_streams:
                        try:
                            self.active_streams[request.recipient].send(request)
                        except Exception as e:
                            logger.warning(f"Failed to stream message to {request.recipient}: {e}")
                
                return pb2.Response(success=True, message="Message sent successfully")
            else:
                return pb2.Response(success=True, message="Message queued for delivery")

    def GetMessages(self, request, context):
        """
        Handle fetching messages.
        
        Args:
            request: MessageRequest protobuf message
            context: gRPC context
            
        Returns:
            MessageList protobuf message
        """
        logger.info(f"GetMessages for {request.username} (limit {request.count})")
        
        # Read operations can be handled by any node
        with self.node.db_lock:
            conn = sqlite3.connect(self.node.db_path)
            c = conn.cursor()
            
            # Get messages where user is sender or recipient
            c.execute("""
                SELECT id, sender, recipient, content, timestamp, read
                FROM messages 
                WHERE sender = ? OR recipient = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (request.username, request.username, request.count))
            
            messages = []
            for row in c.fetchall():
                msg_id, sender, recipient, content, timestamp, read = row
                messages.append(pb2.Message(
                    id=msg_id,
                    sender=sender,
                    recipient=recipient,
                    content=content,
                    timestamp=timestamp,
                    read=bool(read)
                ))
            
            conn.close()
            
            return pb2.MessageList(messages=messages)
    
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
        logger.info(f"MarkAsRead request from {request.username} for {len(request.message_ids)} messages")
        
        # Forward write operation to leader if we're not the leader
        with self.node.node_lock:
            if self.node.state != 'leader':
                try:
                    if self.node.leader_id and self.node.leader_id in self.node.peers:
                        channel = grpc.insecure_channel(self.node.peers[self.node.leader_id])
                        stub = pb2_grpc.ChatServiceStub(channel)
                        return stub.MarkAsRead(request)
                    else:
                        # If we don't know the leader, handle it locally
                        logger.warning("No leader known, handling mark as read locally")
                except Exception as e:
                    logger.warning(f"Failed to forward to leader: {e}, handling locally")
            
            # We're either the leader or failed to forward - handle the operation
            success = self._append_to_log('MARK_AS_READ', {
                'username': request.username,
                'message_ids': request.message_ids
            })
            
            if success:
                return pb2.Response(success=True, message="Messages marked as read")
            else:
                return pb2.Response(success=True, message="Mark as read queued for processing")
    
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
