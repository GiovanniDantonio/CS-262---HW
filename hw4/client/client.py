"""
Client implementation for the fault-tolerant chat system.
Provides connection management, server discovery, and automatic failover.
"""
import grpc
import json
import logging
import os
import sys
import threading
import time
from typing import Dict, List, Optional, Any, Callable

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import proto-generated modules
from proto import chat_pb2, chat_pb2_grpc

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_client")

class ChatClient:
    """
    Client for the fault-tolerant chat system.
    Handles connections, automatic failover, and server discovery.
    """
    
    def __init__(self, server_addresses: List[str], client_id: str = None):
        """
        Initialize the chat client.
        
        Args:
            server_addresses: List of server addresses to try connecting to
            client_id: Optional client identifier
        """
        self.server_addresses = server_addresses
        self.client_id = client_id or f"client-{int(time.time())}"
        
        # Connection management
        self.current_server = None
        self.leader_address = None
        self.channel = None
        self.chat_stub = None
        self.raft_stub = None
        
        # Authentication state
        self.current_username = None
        self.message_stream = None
        self.message_callback = None
        self.stream_thread = None
        self.stream_active = False
        
        # Server status tracking
        self.known_servers = {}  # server_id -> address
        self.server_status = {}  # server_id -> status
        
        # Find an initial server
        self._connect_to_server()
    
    def _connect_to_server(self, specific_address: str = None) -> bool:
        """
        Connect to a server.
        
        Args:
            specific_address: Optional specific server address to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        # Close existing channel if any
        if self.channel:
            self.channel.close()
            
        # Try specific address if provided
        if specific_address:
            addresses = [specific_address]
        else:
            addresses = self.server_addresses
            
        # Try each address until one works
        for address in addresses:
            try:
                logger.info(f"Attempting to connect to {address}...")
                self.channel = grpc.insecure_channel(address)
                self.chat_stub = chat_pb2_grpc.ChatServiceStub(self.channel)
                self.raft_stub = chat_pb2_grpc.RaftServiceStub(self.channel)
                
                # Test connection
                status = self.get_cluster_status()
                if status:
                    self.current_server = address
                    logger.info(f"Connected to server at {address}")
                    
                    # Update known servers and leader
                    self._update_server_info(status)
                    return True
            except Exception as e:
                logger.warning(f"Failed to connect to {address}: {e}")
                
        logger.error("Failed to connect to any server")
        return False
    
    def _update_server_info(self, status: chat_pb2.ClusterStatusResponse) -> None:
        """
        Update known servers and leader information.
        
        Args:
            status: Cluster status response
        """
        # Update leader
        if status.leader_id:
            for member in status.members:
                if member.id == status.leader_id and member.address != "self":
                    self.leader_address = member.address
                    break
            
        # Update known servers
        for member in status.members:
            if member.address != "self":
                self.known_servers[member.id] = member.address
                self.server_status[member.id] = member.state
    
    def _ensure_connected(self) -> bool:
        """
        Ensure client is connected to a server.
        
        Returns:
            True if connected, False otherwise
        """
        if self.channel is None:
            return self._connect_to_server()
        return True
    
    def _reconnect_if_needed(self, e: Exception) -> bool:
        """
        Reconnect to another server if needed.
        
        Args:
            e: Exception that triggered the reconnection
            
        Returns:
            True if successfully reconnected, False otherwise
        """
        logger.warning(f"Connection error: {e}")
        
        # Try to connect to leader if known
        if self.leader_address and self.leader_address != self.current_server:
            if self._connect_to_server(self.leader_address):
                return True
        
        # Try other known servers
        for server_id, address in self.known_servers.items():
            if address != self.current_server:
                if self._connect_to_server(address):
                    return True
        
        # Try original server list
        return self._connect_to_server()
    
    def _handle_not_leader_error(self, message: str) -> bool:
        """
        Handle "not the leader" error.
        
        Args:
            message: Error message from server
            
        Returns:
            True if successfully reconnected to leader, False otherwise
        """
        # Check if message contains leader information
        import re
        match = re.search(r"leader node: (\w+)", message)
        
        if match:
            leader_id = match.group(1)
            if leader_id in self.known_servers:
                logger.info(f"Redirecting to leader {leader_id} at {self.known_servers[leader_id]}")
                return self._connect_to_server(self.known_servers[leader_id])
        
        # Try to get cluster status and connect to leader
        try:
            status = self.get_cluster_status()
            if status and status.leader_id and status.leader_id in self.known_servers:
                return self._connect_to_server(self.known_servers[status.leader_id])
        except Exception:
            pass
        
        return False
    
    def register(self, username: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: Username to register
            password: Password for the account
            
        Returns:
            Dict with success status and message
        """
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server"}
        
        request = chat_pb2.UserAuth(username=username, password=password)
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.Register(request)
                
                if not response.success and "Not the leader" in response.message:
                    if not self._handle_not_leader_error(response.message):
                        break
                    continue
                
                return {
                    "success": response.success,
                    "message": response.message
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        return {"success": False, "message": "Failed to register user"}
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Log in a user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Dict with success status, message, and unread count
        """
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server", "unread_count": 0}
        
        request = chat_pb2.UserAuth(username=username, password=password)
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.Login(request)
                
                if response.success:
                    self.current_username = username
                    
                return {
                    "success": response.success,
                    "message": response.message,
                    "unread_count": response.unread_count,
                    "server_id": response.server_id
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        return {"success": False, "message": "Failed to log in", "unread_count": 0}
    
    def logout(self) -> Dict[str, Any]:
        """
        Log out the current user.
        
        Returns:
            Dict with success status and message
        """
        if not self.current_username:
            return {"success": False, "message": "Not logged in"}
        
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server"}
        
        # Stop message stream if active
        self._stop_message_stream()
        
        request = chat_pb2.UserRequest(username=self.current_username)
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.Logout(request)
                
                if response.success:
                    self.current_username = None
                
                return {
                    "success": response.success,
                    "message": response.message
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        # Even if server call fails, clear local state
        self.current_username = None
        return {"success": True, "message": "Logged out locally"}
    
    def delete_account(self) -> Dict[str, Any]:
        """
        Delete the current user's account.
        
        Returns:
            Dict with success status and message
        """
        if not self.current_username:
            return {"success": False, "message": "Not logged in"}
        
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server"}
        
        # Stop message stream if active
        self._stop_message_stream()
        
        request = chat_pb2.UserRequest(username=self.current_username)
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.DeleteAccount(request)
                
                if not response.success and "Not the leader" in response.message:
                    if not self._handle_not_leader_error(response.message):
                        break
                    continue
                
                if response.success:
                    self.current_username = None
                
                return {
                    "success": response.success,
                    "message": response.message
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        return {"success": False, "message": "Failed to delete account"}
    
    def list_accounts(self, pattern: str = "", page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        List user accounts.
        
        Args:
            pattern: Optional pattern to filter usernames
            page: Page number for pagination
            per_page: Items per page
            
        Returns:
            Dict with list of accounts and pagination info
        """
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server", "accounts": []}
        
        request = chat_pb2.AccountQuery(
            pattern=pattern,
            page=page,
            per_page=per_page
        )
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.ListAccounts(request)
                
                accounts = []
                for account in response.accounts:
                    accounts.append({
                        "username": account.username,
                        "created_at": account.created_at,
                        "last_login": account.last_login
                    })
                
                return {
                    "success": True,
                    "accounts": accounts,
                    "page": response.page,
                    "per_page": response.per_page
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        return {"success": False, "message": "Failed to list accounts", "accounts": []}
    
    def send_message(self, recipient: str, content: str) -> Dict[str, Any]:
        """
        Send a message.
        
        Args:
            recipient: Username of recipient
            content: Message content
            
        Returns:
            Dict with success status and message
        """
        if not self.current_username:
            return {"success": False, "message": "Not logged in"}
        
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server"}
        
        request = chat_pb2.Message(
            sender=self.current_username,
            recipient=recipient,
            content=content
        )
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.SendMessage(request)
                
                if not response.success and "Not the leader" in response.message:
                    if not self._handle_not_leader_error(response.message):
                        break
                    continue
                
                return {
                    "success": response.success,
                    "message": response.message
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        return {"success": False, "message": "Failed to send message"}
    
    def get_messages(self, count: int = 10) -> Dict[str, Any]:
        """
        Get messages for current user.
        
        Args:
            count: Maximum number of messages to retrieve
            
        Returns:
            Dict with list of messages
        """
        if not self.current_username:
            return {"success": False, "message": "Not logged in", "messages": []}
        
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server", "messages": []}
        
        request = chat_pb2.MessageQuery(
            username=self.current_username,
            count=count
        )
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.GetMessages(request)
                
                messages = []
                for msg in response.messages:
                    messages.append({
                        "id": msg.id,
                        "sender": msg.sender,
                        "recipient": msg.recipient,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "read": msg.read,
                        "sequence_number": msg.sequence_number
                    })
                
                return {
                    "success": True,
                    "messages": messages
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        return {"success": False, "message": "Failed to get messages", "messages": []}
    
    def delete_messages(self, message_ids: List[int]) -> Dict[str, Any]:
        """
        Delete messages.
        
        Args:
            message_ids: List of message IDs to delete
            
        Returns:
            Dict with success status and message
        """
        if not self.current_username:
            return {"success": False, "message": "Not logged in"}
        
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server"}
        
        request = chat_pb2.MessageDeleteRequest(
            username=self.current_username,
            message_ids=message_ids
        )
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.DeleteMessages(request)
                
                if not response.success and "Not the leader" in response.message:
                    if not self._handle_not_leader_error(response.message):
                        break
                    continue
                
                return {
                    "success": response.success,
                    "message": response.message
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        return {"success": False, "message": "Failed to delete messages"}
    
    def mark_as_read(self, message_ids: List[int]) -> Dict[str, Any]:
        """
        Mark messages as read.
        
        Args:
            message_ids: List of message IDs to mark as read
            
        Returns:
            Dict with success status and message
        """
        if not self.current_username:
            return {"success": False, "message": "Not logged in"}
        
        if not self._ensure_connected():
            return {"success": False, "message": "Not connected to any server"}
        
        request = chat_pb2.MessageReadRequest(
            username=self.current_username,
            message_ids=message_ids
        )
        
        for _ in range(3):  # Retry up to 3 times
            try:
                response = self.chat_stub.MarkAsRead(request)
                
                if not response.success and "Not the leader" in response.message:
                    if not self._handle_not_leader_error(response.message):
                        break
                    continue
                
                return {
                    "success": response.success,
                    "message": response.message
                }
            except grpc.RpcError as e:
                if not self._reconnect_if_needed(e):
                    break
        
        return {"success": False, "message": "Failed to mark messages as read"}
    
    def _message_stream_thread(self) -> None:
        """Background thread for streaming messages."""
        while self.stream_active and self.current_username:
            try:
                if not self._ensure_connected():
                    time.sleep(1)
                    continue
                
                request = chat_pb2.UserRequest(username=self.current_username)
                self.message_stream = self.chat_stub.StreamMessages(request)
                
                for message in self.message_stream:
                    if not self.stream_active:
                        break
                    
                    # Call the callback with the message
                    if self.message_callback:
                        msg_dict = {
                            "id": message.id,
                            "sender": message.sender,
                            "recipient": message.recipient,
                            "content": message.content,
                            "timestamp": message.timestamp,
                            "read": message.read,
                            "sequence_number": message.sequence_number
                        }
                        self.message_callback(msg_dict)
            
            except grpc.RpcError as e:
                logger.warning(f"Message stream error: {e}")
                
                # Clear the stream and try to reconnect
                self.message_stream = None
                if not self._reconnect_if_needed(e):
                    time.sleep(3)  # Wait before retry
            
            except Exception as e:
                logger.error(f"Unexpected error in message stream: {e}")
                time.sleep(3)  # Wait before retry
    
    def start_message_stream(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Start streaming messages for the current user.
        
        Args:
            callback: Function to call when a message is received
            
        Returns:
            True if stream started, False otherwise
        """
        if not self.current_username:
            return False
        
        if not self._ensure_connected():
            return False
        
        # Stop existing stream if any
        self._stop_message_stream()
        
        # Set up new stream
        self.message_callback = callback
        self.stream_active = True
        
        # Start stream thread
        self.stream_thread = threading.Thread(target=self._message_stream_thread)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        return True
    
    def _stop_message_stream(self) -> None:
        """Stop the message stream."""
        if self.stream_active:
            self.stream_active = False
            
            if self.message_stream:
                try:
                    self.message_stream.cancel()
                except:
                    pass
                self.message_stream = None
            
            if self.stream_thread:
                self.stream_thread.join(timeout=1.0)
                self.stream_thread = None
    
    def get_cluster_status(self) -> Optional[chat_pb2.ClusterStatusResponse]:
        """
        Get status of the Raft cluster.
        
        Returns:
            ClusterStatusResponse or None if failed
        """
        if not self._ensure_connected():
            return None
        
        request = chat_pb2.ClusterStatusRequest(server_id=self.client_id)
        
        try:
            return self.raft_stub.GetClusterStatus(request)
        except Exception as e:
            logger.warning(f"Failed to get cluster status: {e}")
            return None
    
    def close(self) -> None:
        """Close the client connection."""
        self._stop_message_stream()
        
        if self.channel:
            self.channel.close()
            self.channel = None
            
        self.current_username = None
        logger.info("Client closed")
