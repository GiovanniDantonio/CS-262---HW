"""
Server handlers for the fault-tolerant chat service.
This module implements the gRPC handlers for the ChatService and RaftService.
"""
import sys
import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import proto-generated modules
from proto import chat_pb2

# Set up logging
logger = logging.getLogger("chat_handlers")

class ChatServiceHandlers:
    """
    Handlers for ChatService gRPC methods.
    Implements the service logic while delegating to Raft for consensus.
    """
    
    @staticmethod
    def register(server, request, context):
        """
        Handle user registration requests.
        
        Args:
            server: The ChatServer instance
            request: The registration request
            context: The gRPC context
            
        Returns:
            Response with success status and message
        """
        logger.info(f"Register request for: {request.username}")
        
        # Only leader can process write requests
        if not server.raft.is_leader():
            leader_id = server.raft.leader_id
            if leader_id and leader_id in server.raft.peers:
                return chat_pb2.Response(
                    success=False, 
                    message=f"Not the leader. Please try the leader node: {leader_id}"
                )
            return chat_pb2.Response(
                success=False, 
                message="Not the leader. Please try another node."
            )
        
        # Create a command to be replicated
        command = {
            "type": "register",
            "username": request.username,
            "password": _hash_password(request.password),
            "timestamp": time.time()
        }
        
        # Append to Raft log
        if server.raft.append_command(command):
            # Wait for command to be applied
            # In a real system, would need more sophisticated waiting/notification
            time.sleep(0.1)
            
            # Return result
            return chat_pb2.Response(success=True, message="Account created successfully.")
        else:
            return chat_pb2.Response(success=False, message="Failed to replicate command.")
            
    @staticmethod
    def login(server, request, context):
        """
        Handle user login requests.
        
        Args:
            server: The ChatServer instance
            request: The login request
            context: The gRPC context
            
        Returns:
            LoginResponse with success status, message, and unread count
        """
        logger.info(f"Login attempt for: {request.username}")
        
        # Login requests can be handled by any node
        command = {
            "type": "login",
            "username": request.username,
            "password": _hash_password(request.password),
            "timestamp": time.time()
        }
        
        # Apply directly to state machine (read-only operation)
        result = server.storage.apply_command_to_state_machine(command)
        
        return chat_pb2.LoginResponse(
            success=result["success"],
            message=result["message"],
            unread_count=result.get("unread_count", 0),
            server_id=server.server_id
        )
            
    @staticmethod
    def logout(server, request, context):
        """
        Handle user logout requests.
        
        Args:
            server: The ChatServer instance
            request: The logout request
            context: The gRPC context
            
        Returns:
            Response with success status and message
        """
        logger.info(f"Logout request for: {request.username}")
        
        # Remove from active streams if present
        with server.stream_lock:
            if request.username in server.active_streams:
                del server.active_streams[request.username]
                
        return chat_pb2.Response(success=True, message="Logged out successfully.")
    
    @staticmethod
    def delete_account(server, request, context):
        """
        Handle account deletion requests.
        
        Args:
            server: The ChatServer instance
            request: The delete account request
            context: The gRPC context
            
        Returns:
            Response with success status and message
        """
        logger.info(f"DeleteAccount request for: {request.username}")
        
        # Only leader can process write requests
        if not server.raft.is_leader():
            leader_id = server.raft.leader_id
            if leader_id and leader_id in server.raft.peers:
                return chat_pb2.Response(
                    success=False, 
                    message=f"Not the leader. Please try the leader node: {leader_id}"
                )
            return chat_pb2.Response(
                success=False, 
                message="Not the leader. Please try another node."
            )
        
        # Create a command to be replicated
        command = {
            "type": "delete_account",
            "username": request.username,
            "timestamp": time.time()
        }
        
        # Append to Raft log
        if server.raft.append_command(command):
            # Wait for command to be applied
            time.sleep(0.1)
            
            # Remove from active streams if present
            with server.stream_lock:
                if request.username in server.active_streams:
                    del server.active_streams[request.username]
                    
            return chat_pb2.Response(success=True, message="Account deleted successfully.")
        else:
            return chat_pb2.Response(success=False, message="Failed to replicate command.")
    
    @staticmethod
    def list_accounts(server, request, context):
        """
        Handle listing accounts requests.
        
        Args:
            server: The ChatServer instance
            request: The list accounts request
            context: The gRPC context
            
        Returns:
            AccountListResponse with list of accounts
        """
        logger.info(f"ListAccounts request: pattern='{request.pattern}', page={request.page}, per_page={request.per_page}")
        
        # Connect to the database directly for this read-only operation
        import sqlite3
        conn = sqlite3.connect(server.storage.snapshot_file)
        conn.row_factory = sqlite3.Row
        
        try:
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
                accounts.append(chat_pb2.Account(
                    username=row["username"],
                    created_at=row["created_at"] if row["created_at"] is not None else "",
                    last_login=row["last_login"] if row["last_login"] is not None else ""
                ))
                
            return chat_pb2.AccountListResponse(accounts=accounts, page=page, per_page=per_page)
            
        finally:
            conn.close()
    
    @staticmethod
    def send_message(server, request, context):
        """
        Handle sending message requests.
        
        Args:
            server: The ChatServer instance
            request: The send message request
            context: The gRPC context
            
        Returns:
            Response with success status and message
        """
        logger.info(f"SendMessage: from {request.sender} to {request.recipient}: {request.content}")
        
        # Only leader can process write requests
        if not server.raft.is_leader():
            leader_id = server.raft.leader_id
            if leader_id and leader_id in server.raft.peers:
                return chat_pb2.Response(
                    success=False, 
                    message=f"Not the leader. Please try the leader node: {leader_id}"
                )
            return chat_pb2.Response(
                success=False, 
                message="Not the leader. Please try another node."
            )
        
        # Create a command to be replicated
        command = {
            "type": "send_message",
            "sender": request.sender,
            "recipient": request.recipient,
            "content": request.content,
            "sequence_number": len(server.raft.log),
            "timestamp": time.time()
        }
        
        # Append to Raft log
        if server.raft.append_command(command):
            # Wait for command to be applied
            time.sleep(0.1)
            
            # Notify recipient if they have an active stream
            with server.stream_lock:
                if request.recipient in server.active_streams:
                    try:
                        # Create a new message object to send
                        message = chat_pb2.Message(
                            id=0,  # Will be filled in by client from response
                            sender=request.sender,
                            recipient=request.recipient,
                            content=request.content,
                            timestamp=str(time.time()),
                            read=False,
                            sequence_number=command["sequence_number"]
                        )
                        server.active_streams[request.recipient].send(message)
                    except Exception as e:
                        logger.error(f"Error notifying stream for {request.recipient}: {e}")
                    
            return chat_pb2.Response(success=True, message="Message sent successfully.")
        else:
            return chat_pb2.Response(success=False, message="Failed to replicate command.")
    
    @staticmethod
    def get_messages(server, request, context):
        """
        Handle fetching messages requests.
        
        Args:
            server: The ChatServer instance
            request: The get messages request
            context: The gRPC context
            
        Returns:
            MessageList with list of messages
        """
        logger.info(f"GetMessages: for {request.username} (limit {request.count})")
        
        # Connect to the database directly for this read-only operation
        import sqlite3
        conn = sqlite3.connect(server.storage.snapshot_file)
        conn.row_factory = sqlite3.Row
        
        try:
            c = conn.cursor()
            c.execute("""
                SELECT id, sender, recipient, content, timestamp, read, sequence_number 
                FROM messages WHERE recipient = ? 
                ORDER BY timestamp DESC LIMIT ?
            """, (request.username, request.count))
            
            messages = []
            for row in c.fetchall():
                messages.append(chat_pb2.Message(
                    id=row["id"],
                    sender=row["sender"],
                    recipient=row["recipient"],
                    content=row["content"],
                    timestamp=str(row["timestamp"]),
                    read=bool(row["read"]),
                    sequence_number=row["sequence_number"]
                ))
                
            return chat_pb2.MessageList(messages=messages)
            
        except Exception as e:
            logger.error(f"Error in GetMessages: {e}")
            return chat_pb2.MessageList(messages=[])
            
        finally:
            conn.close()
    
    @staticmethod
    def delete_messages(server, request, context):
        """
        Handle deleting messages requests.
        
        Args:
            server: The ChatServer instance
            request: The delete messages request
            context: The gRPC context
            
        Returns:
            Response with success status and message
        """
        logger.info(f"DeleteMessages: for {request.username}, IDs: {request.message_ids}")
        
        # Only leader can process write requests
        if not server.raft.is_leader():
            leader_id = server.raft.leader_id
            if leader_id and leader_id in server.raft.peers:
                return chat_pb2.Response(
                    success=False, 
                    message=f"Not the leader. Please try the leader node: {leader_id}"
                )
            return chat_pb2.Response(
                success=False, 
                message="Not the leader. Please try another node."
            )
        
        # Create a command to be replicated
        command = {
            "type": "delete_messages",
            "username": request.username,
            "message_ids": list(request.message_ids),
            "timestamp": time.time()
        }
        
        # Append to Raft log
        if server.raft.append_command(command):
            # Wait for command to be applied
            time.sleep(0.1)
            
            return chat_pb2.Response(success=True, message="Messages deleted successfully.")
        else:
            return chat_pb2.Response(success=False, message="Failed to replicate command.")
    
    @staticmethod
    def mark_as_read(server, request, context):
        """
        Handle marking messages as read requests.
        
        Args:
            server: The ChatServer instance
            request: The mark as read request
            context: The gRPC context
            
        Returns:
            Response with success status and message
        """
        logger.info(f"MarkAsRead: for {request.username}, IDs: {request.message_ids}")
        
        # Only leader can process write requests
        if not server.raft.is_leader():
            leader_id = server.raft.leader_id
            if leader_id and leader_id in server.raft.peers:
                return chat_pb2.Response(
                    success=False, 
                    message=f"Not the leader. Please try the leader node: {leader_id}"
                )
            return chat_pb2.Response(
                success=False, 
                message="Not the leader. Please try another node."
            )
        
        # Create a command to be replicated
        command = {
            "type": "mark_as_read",
            "username": request.username,
            "message_ids": list(request.message_ids),
            "timestamp": time.time()
        }
        
        # Append to Raft log
        if server.raft.append_command(command):
            # Wait for command to be applied
            time.sleep(0.1)
            
            return chat_pb2.Response(success=True, message="Messages marked as read.")
        else:
            return chat_pb2.Response(success=False, message="Failed to replicate command.")
    
    @staticmethod
    def stream_messages(server, request, context):
        """
        Handle streaming messages requests.
        
        Args:
            server: The ChatServer instance
            request: The stream messages request
            context: The gRPC context
            
        Returns:
            Stream of messages
        """
        logger.info(f"StreamMessages: starting for user {request.username}")
        
        # Register this stream
        with server.stream_lock:
            server.active_streams[request.username] = context
            
        try:
            # Keep the stream open
            while True:
                # Check if context has been cancelled
                if context.is_active() is False:
                    break
                    
                # Just sleep to keep the stream open
                # Actual messages are pushed from send_message handler
                time.sleep(1)
                
        except Exception as e:
            logger.warning(f"StreamMessages: client {request.username} disconnected: {e}")
            
        finally:
            # Clean up the stream registration
            with server.stream_lock:
                if request.username in server.active_streams:
                    del server.active_streams[request.username]
                    
        # Generator needs to return something to end
        return
        yield  # This line will never be reached but satisfies the generator requirement

class RaftServiceHandlers:
    """
    Handlers for RaftService gRPC methods.
    Implements the Raft consensus algorithm RPCs.
    """
    
    @staticmethod
    def request_vote(server, request, context):
        """
        Handle RequestVote RPC from a candidate.
        
        Args:
            server: The ChatServer instance
            request: The RequestVote request
            context: The gRPC context
            
        Returns:
            VoteResponse with term and vote granted status
        """
        logger.debug(f"RequestVote from {request.candidate_id} for term {request.term}")
        
        # Convert protobuf to dictionary for Raft node
        dict_request = {
            "term": request.term,
            "candidate_id": request.candidate_id,
            "last_log_index": request.last_log_index,
            "last_log_term": request.last_log_term
        }
        
        # Process the request in the Raft node
        result = server.raft.handle_request_vote(dict_request)
        
        # Convert result back to protobuf
        return chat_pb2.VoteResponse(
            term=result["term"],
            vote_granted=result["vote_granted"]
        )
    
    @staticmethod
    def append_entries(server, request, context):
        """
        Handle AppendEntries RPC from the leader.
        
        Args:
            server: The ChatServer instance
            request: The AppendEntries request
            context: The gRPC context
            
        Returns:
            AppendEntriesResponse with term, success status, and match index
        """
        logger.debug(f"AppendEntries from {request.leader_id} for term {request.term}")
        
        # Convert entries from protobuf to dictionary
        entries = []
        for entry_pb in request.entries:
            entry_dict = {
                "term": entry_pb.term,
                "index": entry_pb.index,
                "command": {}
            }
            
            # Extract the command based on which field is set
            which_command = entry_pb.WhichOneof("command")
            if which_command == "message_command":
                msg = entry_pb.message_command
                entry_dict["command"] = {
                    "type": "send_message",
                    "sender": msg.sender,
                    "recipient": msg.recipient,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "read": msg.read,
                    "sequence_number": msg.sequence_number
                }
            elif which_command == "user_auth_command":
                auth = entry_pb.user_auth_command
                entry_dict["command"] = {
                    "type": "register",
                    "username": auth.username,
                    "password": auth.password
                }
            elif which_command == "user_command":
                user = entry_pb.user_command
                entry_dict["command"] = {
                    "type": "delete_account",
                    "username": user.username
                }
            elif which_command == "delete_command":
                delete = entry_pb.delete_command
                entry_dict["command"] = {
                    "type": "delete_messages",
                    "username": delete.username,
                    "message_ids": list(delete.message_ids)
                }
            elif which_command == "read_command":
                read = entry_pb.read_command
                entry_dict["command"] = {
                    "type": "mark_as_read",
                    "username": read.username,
                    "message_ids": list(read.message_ids)
                }
                
            entries.append(entry_dict)
            
        # Convert protobuf to dictionary for Raft node
        dict_request = {
            "term": request.term,
            "leader_id": request.leader_id,
            "prev_log_index": request.prev_log_index,
            "prev_log_term": request.prev_log_term,
            "entries": entries,
            "leader_commit": request.leader_commit
        }
        
        # Process the request in the Raft node
        result = server.raft.handle_append_entries(dict_request)
        
        # Convert result back to protobuf
        return chat_pb2.AppendEntriesResponse(
            term=result["term"],
            success=result["success"],
            match_index=result["match_index"]
        )
    
    @staticmethod
    def join_cluster(server, request, context):
        """
        Handle JoinCluster RPC from a new server.
        
        Args:
            server: The ChatServer instance
            request: The JoinCluster request
            context: The gRPC context
            
        Returns:
            Response with success status and message
        """
        logger.info(f"JoinCluster request from {request.server_id} at {request.server_address}")
        
        # Only leader can add new servers
        if not server.raft.is_leader():
            leader_id = server.raft.leader_id
            if leader_id and leader_id in server.raft.peers:
                return chat_pb2.Response(
                    success=False, 
                    message=f"Not the leader. Please try the leader node: {leader_id}"
                )
            return chat_pb2.Response(
                success=False, 
                message="Not the leader. Please try another node."
            )
        
        # Add the new server to peers
        server.raft.peers[request.server_id] = request.server_address
        
        # Initialize nextIndex and matchIndex for the new server
        server.raft.next_index[request.server_id] = len(server.raft.log)
        server.raft.match_index[request.server_id] = 0
        
        # Send initial heartbeat
        server._send_append_entries(request.server_id, request.server_address)
        
        return chat_pb2.Response(
            success=True,
            message=f"Successfully joined the cluster as follower. Leader is {server.server_id}."
        )
    
    @staticmethod
    def get_cluster_status(server, request, context):
        """
        Handle GetClusterStatus RPC.
        
        Args:
            server: The ChatServer instance
            request: The GetClusterStatus request
            context: The gRPC context
            
        Returns:
            ClusterStatusResponse with leader ID, current term, and members list
        """
        logger.info(f"GetClusterStatus request from {request.server_id}")
        
        # Get status from Raft node
        status = server.raft.get_cluster_status()
        
        # Convert dictionary to protobuf
        members = []
        for member in status["members"]:
            members.append(chat_pb2.ClusterMember(
                id=member["id"],
                address=member["address"],
                state=member["state"],
                last_seen=member["last_seen"]
            ))
            
        return chat_pb2.ClusterStatusResponse(
            leader_id=status["leader_id"] if status["leader_id"] else "",
            current_term=status["current_term"],
            members=members
        )
    
    @staticmethod
    def transfer_snapshot(server, request, context):
        """
        Handle TransferSnapshot RPC.
        
        Args:
            server: The ChatServer instance
            request: The TransferSnapshot request
            context: The gRPC context
            
        Returns:
            Stream of SnapshotChunk messages
        """
        logger.info(f"TransferSnapshot request from {request.server_id}")
        
        # Get the snapshot file path
        snapshot_file = server.storage.snapshot_file
        
        # Check if file exists
        if not os.path.exists(snapshot_file):
            return
            
        # Get snapshot metadata
        last_included_index, last_included_term = server.storage.load_snapshot()
        
        # Read and send the snapshot file in chunks
        with open(snapshot_file, 'rb') as f:
            chunk_size = 1024 * 1024  # 1MB chunks
            offset = 0
            
            while True:
                data = f.read(chunk_size)
                if not data:
                    # Send the final chunk
                    yield chat_pb2.SnapshotChunk(
                        offset=offset,
                        data=b'',
                        done=True,
                        last_included_index=last_included_index,
                        last_included_term=last_included_term
                    )
                    break
                    
                # Send a chunk
                yield chat_pb2.SnapshotChunk(
                    offset=offset,
                    data=data,
                    done=False,
                    last_included_index=last_included_index,
                    last_included_term=last_included_term
                )
                
                offset += len(data)

def _hash_password(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
