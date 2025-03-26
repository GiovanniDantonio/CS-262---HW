"""
Fault-tolerant client implementation for chat system.
"""
import logging
import socket
import threading
import time
from typing import Dict, List, Optional, Tuple

from ..common.config import ClusterConfig
from ..common.protocol import MessageType, StatusCode, create_message, send_json, receive_json

logger = logging.getLogger(__name__)

class ChatClient:
    def __init__(self, config_path: str):
        self.config = ClusterConfig(config_path)
        self.nodes = self.config.get_all_nodes()
        self.retry_interval = self.config.get_client_retry_interval_ms() / 1000
        
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.username: Optional[str] = None
        self.current_node: Optional[Dict] = None
        
        # Message handling
        self.message_handlers: Dict[MessageType, callable] = {}
        self.message_lock = threading.Lock()
        
        # Background thread for receiving messages
        self.receiver_thread: Optional[threading.Thread] = None
        self.running = False
    
    def register_handler(self, msg_type: MessageType, handler: callable) -> None:
        """Register a handler for a specific message type."""
        with self.message_lock:
            self.message_handlers[msg_type] = handler
    
    def connect(self) -> bool:
        """Connect to any available node in the cluster."""
        # Try each node until we find one that's available
        for node in self.nodes:
            try:
                logger.info(f"Attempting to connect to {node['host']}:{node['port']}")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((node["host"], node["port"]))
                
                self.socket = sock
                self.current_node = node
                self.connected = True
                
                # Start receiver thread
                self.running = True
                self.receiver_thread = threading.Thread(target=self._receive_messages)
                self.receiver_thread.daemon = True
                self.receiver_thread.start()
                
                logger.info(f"Connected to node {node['id']}")
                return True
                
            except Exception as e:
                logger.warning(f"Failed to connect to {node['host']}:{node['port']}: {e}")
                continue
        
        logger.error("Failed to connect to any node in the cluster")
        return False
    
    def disconnect(self) -> None:
        """Disconnect from the current node."""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.receiver_thread and threading.current_thread() != self.receiver_thread:
            self.receiver_thread.join()
            self.receiver_thread = None
        
        self.current_node = None
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to the cluster."""
        self.disconnect()
        return self.connect()
    
    def _receive_messages(self) -> None:
        """Background thread for receiving messages."""
        while self.running and self.socket:
            try:
                msg = receive_json(self.socket)
                if not msg:
                    break
                
                self._handle_message(msg)
                
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break
        
        # Connection lost
        self.connected = False
        self._handle_connection_loss()
    
    def _handle_message(self, msg: Dict) -> None:
        """Handle received message."""
        try:
            msg_type = MessageType[msg["type"]]
            
            with self.message_lock:
                handler = self.message_handlers.get(msg_type)
                if handler:
                    handler(msg["data"])
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _handle_connection_loss(self) -> None:
        """Handle loss of connection to current node."""
        while self.running:
            logger.info("Connection lost, attempting to reconnect...")
            if self.reconnect():
                # Re-authenticate if we were logged in
                if self.username:
                    self._reauthenticate()
                break
            
            time.sleep(self.retry_interval)
    
    def _reauthenticate(self) -> None:
        """Re-authenticate with new node after reconnection."""
        # This would re-send the last successful login/create account command
        pass
    
    def _send_with_retry(self, msg_type: MessageType, data: Dict,
                        max_retries: int = 3) -> Optional[Dict]:
        """Send message with retry on failure."""
        retries = 0
        while retries < max_retries:
            try:
                if not self.connected:
                    if not self.reconnect():
                        time.sleep(self.retry_interval)
                        retries += 1
                        continue
                
                msg = create_message(msg_type, data)
                send_json(self.socket, msg)
                
                response = receive_json(self.socket)
                if not response:
                    raise ConnectionError("No response received")
                
                # Check if we need to redirect to a different node
                if response["data"]["status"] == StatusCode.REDIRECT.name:
                    self._handle_redirect(response["data"])
                    retries += 1
                    continue
                
                return response
                
            except Exception as e:
                logger.error(f"Error sending {msg_type.name}: {e}")
                self.connected = False
                retries += 1
        
        return None
    
    def _handle_redirect(self, data: Dict) -> None:
        """Handle redirect to new leader."""
        try:
            # Connect to new leader
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((data["leader_host"], data["leader_port"]))
            
            # Switch connection
            old_socket = self.socket
            self.socket = sock
            
            try:
                old_socket.close()
            except:
                pass
            
            # Update current node
            for node in self.nodes:
                if node["host"] == data["leader_host"] and node["port"] == data["leader_port"]:
                    self.current_node = node
                    break
            
            logger.info(f"Redirected to new leader at {data['leader_host']}:{data['leader_port']}")
            
        except Exception as e:
            logger.error(f"Failed to handle redirect: {e}")
            self.connected = False
    
    def create_account(self, username: str, password: str) -> bool:
        """Create a new account."""
        response = self._send_with_retry(MessageType.CREATE_ACCOUNT, {
            "username": username,
            "password": password
        })
        
        if response and response["data"]["status"] == StatusCode.SUCCESS.name:
            self.username = username
            return True
        return False
    
    def login(self, username: str, password: str) -> bool:
        """Log in to an existing account."""
        response = self._send_with_retry(MessageType.LOGIN, {
            "username": username,
            "password": password
        })
        
        if response and response["data"]["status"] == StatusCode.SUCCESS.name:
            self.username = username
            return True
        return False
    
    def logout(self) -> bool:
        """Log out from current account."""
        if not self.username:
            return False
        
        response = self._send_with_retry(MessageType.LOGOUT, {
            "username": self.username
        })
        
        if response and response["data"]["status"] == StatusCode.SUCCESS.name:
            self.username = None
            return True
        return False
    
    def delete_account(self) -> bool:
        """Delete current account."""
        if not self.username:
            return False
        
        response = self._send_with_retry(MessageType.DELETE_ACCOUNT, {
            "username": self.username
        })
        
        if response and response["data"]["status"] == StatusCode.SUCCESS.name:
            self.username = None
            return True
        return False
    
    def list_accounts(self) -> Optional[List[str]]:
        """List all accounts."""
        response = self._send_with_retry(MessageType.LIST_ACCOUNTS, {})
        
        if response and response["data"]["status"] == StatusCode.SUCCESS.name:
            return response["data"]["accounts"]
        return None
    
    def send_message(self, recipient: str, content: str) -> bool:
        """Send a message to another user."""
        if not self.username:
            return False
        
        response = self._send_with_retry(MessageType.SEND_MESSAGE, {
            "sender": self.username,
            "recipient": recipient,
            "content": content
        })
        
        return response and response["data"]["status"] == StatusCode.SUCCESS.name
    
    def get_messages(self) -> Optional[List[Dict]]:
        """Get messages for current user."""
        if not self.username:
            return None
        
        response = self._send_with_retry(MessageType.GET_MESSAGES, {
            "username": self.username
        })
        
        if response and response["data"]["status"] == StatusCode.SUCCESS.name:
            return response["data"]["messages"]
        return None
    
    def delete_messages(self, message_ids: List[int]) -> bool:
        """Delete specific messages."""
        if not self.username:
            return False
        
        response = self._send_with_retry(MessageType.DELETE_MESSAGES, {
            "username": self.username,
            "message_ids": message_ids
        })
        
        return response and response["data"]["status"] == StatusCode.SUCCESS.name
    
    def mark_as_read(self, message_ids: List[int]) -> bool:
        """Mark messages as read."""
        if not self.username:
            return False
        
        response = self._send_with_retry(MessageType.MARK_AS_READ, {
            "username": self.username,
            "message_ids": message_ids
        })
        
        return response and response["data"]["status"] == StatusCode.SUCCESS.name

def main() -> None:
    """Main entry point for command-line interface."""
    import argparse
    import cmd
    import getpass
    
    class ChatShell(cmd.Cmd):
        intro = "Welcome to the fault-tolerant chat client. Type help or ? to list commands."
        prompt = "(chat) "
        
        def __init__(self, client: ChatClient):
            super().__init__()
            self.client = client
            
            # Register broadcast handler
            client.register_handler(MessageType.BROADCAST,
                                 lambda data: print(f"\nBroadcast: {data}"))
        
        def do_create(self, arg):
            """Create a new account: create <username>"""
            username = arg.strip()
            if not username:
                print("Usage: create <username>")
                return
            
            password = getpass.getpass()
            if self.client.create_account(username, password):
                print("Account created successfully")
            else:
                print("Failed to create account")
        
        def do_login(self, arg):
            """Log in to an existing account: login <username>"""
            username = arg.strip()
            if not username:
                print("Usage: login <username>")
                return
            
            password = getpass.getpass()
            if self.client.login(username, password):
                print("Logged in successfully")
                self.prompt = f"({username}) "
            else:
                print("Failed to log in")
        
        def do_logout(self, arg):
            """Log out from current account"""
            if self.client.logout():
                print("Logged out successfully")
                self.prompt = "(chat) "
            else:
                print("Failed to log out")
        
        def do_delete(self, arg):
            """Delete current account"""
            if self.client.delete_account():
                print("Account deleted successfully")
                self.prompt = "(chat) "
            else:
                print("Failed to delete account")
        
        def do_list(self, arg):
            """List all accounts"""
            accounts = self.client.list_accounts()
            if accounts:
                print("Accounts:")
                for account in accounts:
                    print(f"- {account}")
            else:
                print("Failed to list accounts")
        
        def do_send(self, arg):
            """Send a message: send <recipient> <message>"""
            try:
                recipient, message = arg.split(maxsplit=1)
            except ValueError:
                print("Usage: send <recipient> <message>")
                return
            
            if self.client.send_message(recipient, message):
                print("Message sent successfully")
            else:
                print("Failed to send message")
        
        def do_messages(self, arg):
            """Get your messages"""
            messages = self.client.get_messages()
            if messages:
                print("Messages:")
                for msg in messages:
                    print(f"From {msg['sender']}: {msg['content']}")
            else:
                print("No messages or failed to get messages")
        
        def do_quit(self, arg):
            """Quit the chat client"""
            self.client.disconnect()
            return True
    
    parser = argparse.ArgumentParser(description="Start chat client")
    parser.add_argument("--config", default="cluster_config.json",
                       help="Path to cluster configuration file")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start client
    client = ChatClient(args.config)
    if not client.connect():
        print("Failed to connect to any node in the cluster")
        return
    
    # Start shell
    ChatShell(client).cmdloop()

if __name__ == "__main__":
    main()
