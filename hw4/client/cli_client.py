"""
Command-line interface for the fault-tolerant chat system.
Provides a simple interactive client for testing and demonstration.
"""
import argparse
import cmd
import json
import logging
import os
import sys
import threading
import time
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client import ChatClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cli_client")

class ChatShell(cmd.Cmd):
    """Interactive shell for the chat client."""
    
    intro = "Fault-Tolerant Chat System CLI. Type help or ? to list commands.\n"
    prompt = "(chat) "
    
    def __init__(self, client: ChatClient):
        """
        Initialize the chat shell.
        
        Args:
            client: ChatClient instance
        """
        super().__init__()
        self.client = client
        self.message_lock = threading.Lock()
        
        # Start message streaming if logged in
        if self.client.current_username:
            self.client.start_message_stream(self._handle_incoming_message)
    
    def _handle_incoming_message(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming message from stream.
        
        Args:
            message: Message dictionary
        """
        with self.message_lock:
            print(f"\n\nNew message from {message['sender']}:")
            print(f"  > {message['content']}")
            print(f"\n{self.prompt}", end="", flush=True)
    
    def emptyline(self) -> bool:
        """Handle empty line input."""
        return False
    
    def do_register(self, arg: str) -> None:
        """
        Register a new user account.
        Usage: register <username> <password>
        """
        args = arg.split()
        if len(args) != 2:
            print("Usage: register <username> <password>")
            return
        
        username, password = args
        result = self.client.register(username, password)
        print(f"Result: {result['message']}")
    
    def do_login(self, arg: str) -> None:
        """
        Log in to the chat system.
        Usage: login <username> <password>
        """
        args = arg.split()
        if len(args) != 2:
            print("Usage: login <username> <password>")
            return
        
        username, password = args
        result = self.client.login(username, password)
        print(f"Result: {result['message']}")
        
        if result['success']:
            print(f"Logged in to server: {result.get('server_id', 'unknown')}")
            print(f"Unread messages: {result['unread_count']}")
            self.prompt = f"({username}) "
            
            # Start message streaming
            self.client.start_message_stream(self._handle_incoming_message)
    
    def do_logout(self, arg: str) -> None:
        """
        Log out from the chat system.
        Usage: logout
        """
        result = self.client.logout()
        print(f"Result: {result['message']}")
        
        if result['success']:
            self.prompt = "(chat) "
    
    def do_delete_account(self, arg: str) -> None:
        """
        Delete the current user account.
        Usage: delete_account
        """
        if not self.client.current_username:
            print("Error: Not logged in")
            return
        
        result = self.client.delete_account()
        print(f"Result: {result['message']}")
        
        if result['success']:
            self.prompt = "(chat) "
    
    def do_list(self, arg: str) -> None:
        """
        List user accounts.
        Usage: list [pattern] [page] [per_page]
        """
        args = arg.split()
        pattern = args[0] if len(args) > 0 else ""
        page = int(args[1]) if len(args) > 1 else 1
        per_page = int(args[2]) if len(args) > 2 else 10
        
        result = self.client.list_accounts(pattern, page, per_page)
        
        if result['success']:
            print(f"Accounts (Page {result['page']}):")
            for account in result['accounts']:
                print(f"  {account['username']}")
                if account.get('last_login'):
                    print(f"    Last login: {account['last_login']}")
            print(f"Showing {len(result['accounts'])} accounts (page {result['page']})")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def do_send(self, arg: str) -> None:
        """
        Send a message to another user.
        Usage: send <recipient> <message>
        """
        if not self.client.current_username:
            print("Error: Not logged in")
            return
        
        parts = arg.split(maxsplit=1)
        if len(parts) != 2:
            print("Usage: send <recipient> <message>")
            return
        
        recipient, content = parts
        result = self.client.send_message(recipient, content)
        print(f"Result: {result['message']}")
    
    def do_messages(self, arg: str) -> None:
        """
        Get messages for the current user.
        Usage: messages [count]
        """
        if not self.client.current_username:
            print("Error: Not logged in")
            return
        
        count = int(arg) if arg.strip() else 10
        result = self.client.get_messages(count)
        
        if result['success']:
            messages = result['messages']
            if not messages:
                print("No messages found")
                return
                
            print(f"Messages for {self.client.current_username}:")
            for msg in messages:
                read_status = "Read" if msg['read'] else "Unread"
                print(f"[{msg['id']}] From: {msg['sender']} ({read_status})")
                print(f"  > {msg['content']}")
                print(f"  Sent: {msg['timestamp']}")
                print("")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def do_read(self, arg: str) -> None:
        """
        Mark messages as read.
        Usage: read <message_id1> [message_id2] ...
        """
        if not self.client.current_username:
            print("Error: Not logged in")
            return
        
        try:
            message_ids = [int(id_str) for id_str in arg.split()]
            if not message_ids:
                print("Usage: read <message_id1> [message_id2] ...")
                return
                
            result = self.client.mark_as_read(message_ids)
            print(f"Result: {result['message']}")
        except ValueError:
            print("Error: Message IDs must be integers")
    
    def do_delete(self, arg: str) -> None:
        """
        Delete messages.
        Usage: delete <message_id1> [message_id2] ...
        """
        if not self.client.current_username:
            print("Error: Not logged in")
            return
        
        try:
            message_ids = [int(id_str) for id_str in arg.split()]
            if not message_ids:
                print("Usage: delete <message_id1> [message_id2] ...")
                return
                
            result = self.client.delete_messages(message_ids)
            print(f"Result: {result['message']}")
        except ValueError:
            print("Error: Message IDs must be integers")
    
    def do_status(self, arg: str) -> None:
        """
        Get the status of the chat cluster.
        Usage: status
        """
        status = self.client.get_cluster_status()
        
        if status:
            print(f"Cluster status:")
            print(f"  Current term: {status.current_term}")
            print(f"  Leader: {status.leader_id or 'Unknown'}")
            print(f"  Members:")
            for member in status.members:
                print(f"    {member.id} ({member.state}) at {member.address}")
        else:
            print("Failed to get cluster status")
    
    def do_connect(self, arg: str) -> None:
        """
        Connect to a specific server.
        Usage: connect <server_address>
        """
        if not arg:
            print("Usage: connect <server_address>")
            return
            
        if self.client._connect_to_server(arg):
            print(f"Connected to {arg}")
            
            # Refresh status display
            self.do_status("")
        else:
            print(f"Failed to connect to {arg}")
    
    def do_exit(self, arg: str) -> bool:
        """Exit the chat shell."""
        if self.client.current_username:
            print("Logging out...")
            self.client.logout()
            
        print("Goodbye!")
        return True
        
    def do_quit(self, arg: str) -> bool:
        """Exit the chat shell."""
        return self.do_exit(arg)
        
    def do_EOF(self, arg: str) -> bool:
        """Handle EOF (Ctrl+D)."""
        print()
        return self.do_exit(arg)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Chat client CLI")
    
    parser.add_argument('--servers', required=True, help='Comma-separated list of server addresses')
    parser.add_argument('--config', help='Path to cluster configuration file')
    
    return parser.parse_args()

def load_config(file_path: str) -> List[str]:
    """
    Load server addresses from a configuration file.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        List of server addresses
    """
    if not os.path.exists(file_path):
        logger.warning(f"Config file {file_path} not found")
        return []
    
    with open(file_path, 'r') as f:
        config = json.load(f)
    
    return list(config.get('servers', {}).values())

def main():
    """Main entry point."""
    args = parse_args()
    
    # Get server addresses
    server_addresses = args.servers.split(',')
    
    # Add servers from config file if provided
    if args.config:
        server_addresses.extend(load_config(args.config))
    
    # Create client
    client = ChatClient(server_addresses)
    
    # Start interactive shell
    shell = ChatShell(client)
    
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        client.close()

if __name__ == "__main__":
    main()
