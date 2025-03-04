import socket
import threading
import time
import random
import queue
import logging
import datetime
import os
from typing import List, Dict, Tuple, Optional

class VirtualMachine:
    """
    Represents a virtual machine in the distributed system model.
    Each machine has its own clock rate, logical clock, and message queue.
    """
    
    def __init__(self, machine_id: int, port: int, peer_ports: List[int]):
        """
        Initialize a virtual machine with a specific ID and clock rate.
        
        Args:
            machine_id: Unique identifier for this machine
            port: Port on which this machine will listen for messages
            peer_ports: Ports of other machines to connect to
        """
        # Basic properties
        self.machine_id = machine_id
        self.port = port
        self.peer_ports = peer_ports
        
        # Randomize clock rate (1-6 ticks per second)
        self.clock_rate = random.randint(1, 6)
        self.tick_interval = 1.0 / self.clock_rate
        
        # Initialize logical clock
        self.logical_clock = 0
        
        # Initialize message queue
        self.message_queue = queue.Queue()
        
        # Socket for listening to incoming connections
        self.server_socket = None
        
        # Connections to peer machines
        self.peer_connections: Dict[int, socket.socket] = {}
        
        # Setup logging
        self.setup_logging()
        
        # Flags for control
        self.running = False
        self.initialized = False

    def setup_logging(self):
        """Set up logging for this virtual machine."""
        log_filename = os.path.join("logs", f"machine_{self.machine_id}.log")
        
        # Configure file handler
        file_handler = logging.FileHandler(log_filename, mode='w')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Configure logger
        self.logger = logging.getLogger(f"VM-{self.machine_id}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
        # Log initial information
        self.logger.info(f"Virtual Machine {self.machine_id} initialized")
        self.logger.info(f"Clock Rate: {self.clock_rate} ticks/second")
        self.logger.info(f"Listening on port: {self.port}")
        self.logger.info(f"Peer ports: {self.peer_ports}")

    def initialize_network(self):
        """
        Initialize network connections.
        This includes setting up a server socket and connecting to peers.
        """
        if self.initialized:
            return
            
        # Create and configure server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen(5)
        
        # Start listening thread
        self.listener_thread = threading.Thread(target=self.listen_for_connections)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        
        # Connect to peers
        self.connect_to_peers()
        
        self.initialized = True
        self.logger.info("Network initialization completed")

    def connect_to_peers(self):
        """
        Establish connections to peer virtual machines.
        """
        for peer_port in self.peer_ports:
            # Connect to all peers regardless of port number
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_socket.connect(('localhost', peer_port))
                    self.peer_connections[peer_port] = peer_socket
                    self.logger.info(f"Connected to peer on port {peer_port}")
                    break
                except ConnectionRefusedError:
                    retry_count += 1
                    time.sleep(1)  # Wait before retrying
                    
            if retry_count == max_retries:
                self.logger.error(f"Failed to connect to peer on port {peer_port}")

    def listen_for_connections(self):
        """
        Listen for incoming connections from other virtual machines.
        This runs in a separate thread.
        """
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_port = addr[1]
                self.peer_connections[client_port] = client_socket
                self.logger.info(f"Accepted connection from {addr}")
                
                # Start a thread to receive messages from this client
                receiver_thread = threading.Thread(
                    target=self.receive_messages, 
                    args=(client_socket,)
                )
                receiver_thread.daemon = True
                receiver_thread.start()
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {e}")

    def receive_messages(self, client_socket):
        """
        Receive and process messages from a connected client.
        This runs in a separate thread.
        
        Args:
            client_socket: Socket connected to the client
        """
        while self.running:
            try:
                # Receive message
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                # Parse message (assuming format: "logical_clock:sender_id")
                message = data.decode('utf-8')
                received_clock, sender_id = map(int, message.split(':'))
                
                # Add to message queue
                self.message_queue.put((received_clock, sender_id))
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error receiving message: {e}")
                break
                
        client_socket.close()

    def send_message(self, target_ports):
        """
        Send the current logical clock value to specified target machines.
        
        Args:
            target_ports: List of ports to send the message to
        """
        # Increment logical clock before sending
        self.logical_clock += 1
        
        # Prepare message
        message = f"{self.logical_clock}:{self.machine_id}"
        
        # System time for logging
        system_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        
        # Send to each target
        for port in target_ports:
            if port in self.peer_connections:
                try:
                    self.peer_connections[port].sendall(message.encode('utf-8'))
                    self.logger.info(f"SEND - System Time: {system_time}, Logical Clock: {self.logical_clock}, To: Machine on port {port}")
                except Exception as e:
                    self.logger.error(f"Error sending message to port {port}: {e}")
            else:
                self.logger.warning(f"No connection to port {port}")

    def process_event(self):
        """
        Process one event cycle according to the specification:
        - If there's a message in the queue, process it
        - Otherwise, generate a random event
        """
        # Check if there's a message in the queue
        if not self.message_queue.empty():
            # Process one message
            received_clock, sender_id = self.message_queue.get()
            
            # Update logical clock
            self.logical_clock = max(self.logical_clock, received_clock) + 1
            
            # Get system time and queue length for logging
            system_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            queue_length = self.message_queue.qsize()
            
            # Log the receive event
            self.logger.info(
                f"RECEIVE - System Time: {system_time}, Logical Clock: {self.logical_clock}, "
                f"Queue Length: {queue_length}, From: Machine {sender_id}"
            )
        else:
            sorted_peers = sorted(self.peer_ports)
            # Generate random event (1-10)
            event = random.randint(1, 10)
            
            # System time for logging
            system_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            
            if event == 1:
                # Send to a random peer
                if self.peer_ports:
                    random_peer = random.choice(self.peer_ports)
                    self.send_message([random_peer])
            elif event == 2:
                # Send to a different random peer
                if self.peer_ports:
                    random_peer = random.choice(self.peer_ports)
                    self.send_message([random_peer])
            elif event == 3:
                # Send to all peers
                self.send_message(self.peer_ports)
            else:
                # Internal event (4-10)
                self.logical_clock += 1
                self.logger.info(f"INTERNAL - System Time: {system_time}, Logical Clock: {self.logical_clock}")

    def run(self):
        """
        Run the virtual machine's main loop.
        This will process events at the machine's clock rate.
        """
        self.running = True
        
        if not self.initialized:
            self.initialize_network()
            
        self.logger.info("Starting main event loop")
        self.logger.info(f"Clock rate: {self.clock_rate} ticks/second")
        
        try:
            while self.running:
                # Process one event
                self.process_event()
                
                # Sleep for one clock cycle
                time.sleep(self.tick_interval)
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            self.logger.info("Main loop terminated")

    def stop(self):
        """
        Stop the virtual machine's execution.
        """
        self.logger.info("Stopping virtual machine")
        self.running = False
        
        # Close all connections
        for port, conn in list(self.peer_connections.items()):
            try:
                conn.close()
                self.logger.info(f"Closed connection to port {port}")
            except Exception as e:
                self.logger.error(f"Error closing connection to port {port}: {e}")
                
        # Clear connections
        self.peer_connections.clear()
                
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
                self.logger.info("Closed server socket")
            except Exception as e:
                self.logger.error(f"Error closing server socket: {e}")
            
        self.logger.info("Virtual machine stopped")
