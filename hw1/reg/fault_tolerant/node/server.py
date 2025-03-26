"""
Node server implementation for fault-tolerant chat system.
"""
import argparse
import logging
import socket
import threading
from typing import Dict, List, Optional, Tuple

from ..common.config import ClusterConfig
from ..common.protocol import MessageType, NodeRole, StatusCode, create_message, send_json, receive_json
from .state_machine import StateMachine

logger = logging.getLogger(__name__)

class NodeServer:
    def __init__(self, node_id: int, config_path: str = None):
        # Load configuration
        self.config = ClusterConfig(config_path)
        self.node_id = node_id
        self.node_config = self.config.get_node_by_id(node_id)
        
        # Initialize state machine
        self.state_machine = StateMachine(node_id, self.config.get_all_nodes(), f"node{node_id}.db")
        
        # Server socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.node_config["host"], self.node_config["port"]))
        self.socket.listen(5)
        
        # Client connections
        self.clients: Dict[socket.socket, threading.Thread] = {}
        self.clients_lock = threading.Lock()
        
        # Node state
        self.running = True
    
    def start(self) -> None:
        """Start the node server."""
        logger.info(f"Starting node {self.node_id}")
        
        # Start election timer thread
        election_thread = threading.Thread(target=self._run_election_timer)
        election_thread.daemon = True
        election_thread.start()
        
        # Accept client connections
        try:
            while self.running:
                client_sock, addr = self.socket.accept()
                logger.info(f"New connection from {addr}")
                
                client_thread = threading.Thread(target=self._handle_client, args=(client_sock,))
                client_thread.daemon = True
                client_thread.start()
                
                with self.clients_lock:
                    self.clients[client_sock] = client_thread
                
        except Exception as e:
            logger.error(f"Error in server loop: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the node server."""
        logger.info(f"Stopping node {self.node_id}")
        self.running = False
        
        # Close all client connections
        with self.clients_lock:
            for sock in self.clients:
                try:
                    sock.close()
                except:
                    pass
            self.clients.clear()
        
        # Close server socket
        try:
            self.socket.close()
        except:
            pass
    
    def _run_election_timer(self) -> None:
        """Run election timer thread."""
        while self.running:
            if self.state_machine.check_election_timeout():
                self.state_machine.start_election()
    
    def _handle_client(self, client_sock: socket.socket) -> None:
        """Handle client connection."""
        try:
            while self.running:
                msg = receive_json(client_sock)
                if not msg:
                    break
                
                response = self._handle_message(msg)
                send_json(client_sock, response)
                
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            with self.clients_lock:
                self.clients.pop(client_sock, None)
            try:
                client_sock.close()
            except:
                pass
    
    def _handle_message(self, msg: Dict) -> Dict:
        """Handle client message."""
        try:
            msg_type = MessageType[msg["type"]]
            
            # Handle Raft protocol messages
            if msg_type == MessageType.REQUEST_VOTE:
                term, granted = self.state_machine.handle_vote_request(
                    msg["data"]["term"],
                    msg["data"]["candidate_id"],
                    msg["data"]["last_log_index"],
                    msg["data"]["last_log_term"]
                )
                return create_message(MessageType.REQUEST_VOTE_RESPONSE, {
                    "term": term,
                    "vote_granted": granted
                })
            
            elif msg_type == MessageType.REQUEST_VOTE_RESPONSE:
                self.state_machine.handle_vote_response(
                    msg["data"]["term"],
                    msg["data"]["voter_id"],
                    msg["data"]["vote_granted"]
                )
                return create_message(MessageType.ACK, {})
            
            # Handle client requests
            else:
                status, data = self.state_machine.apply_command(msg)
                return create_message(MessageType.RESPONSE, {
                    "status": status.name,
                    **(data or {})
                })
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return create_message(MessageType.RESPONSE, {
                "status": StatusCode.ERROR.name,
                "message": str(e)
            })

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("node_id", type=int, help="Node ID")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()
    
    # Start server
    server = NodeServer(args.node_id, args.config)
    server.start()

if __name__ == "__main__":
    main()
