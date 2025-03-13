"""
Fault tolerance test script for the chat system.
Tests the system's ability to handle node failures and maintain consistency.
"""
import argparse
import logging
import os
import signal
import subprocess
import sys
import time
import random
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.client import ChatClient
from proto import chat_pb2

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fault_tolerance_test")

class ServerProcess:
    """Manages a server process for testing."""
    
    def __init__(self, server_id: str, port: int, data_dir: str, join_address: str = None):
        """
        Initialize a server process.
        
        Args:
            server_id: Unique ID for the server
            port: Port to run the server on
            data_dir: Directory for persistent data
            join_address: Optional address of a server to join
        """
        self.server_id = server_id
        self.port = port
        self.data_dir = data_dir
        self.join_address = join_address
        self.process = None
        self.address = f"localhost:{port}"
        
    def start(self) -> bool:
        """
        Start the server process.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.process:
            logger.warning(f"Server {self.server_id} already running")
            return True
            
        cmd = [
            "python3", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "run_server.py"),
            "--id", self.server_id,
            "--port", str(self.port),
            "--data-dir", self.data_dir
        ]
        
        if self.join_address:
            cmd.extend(["--join", self.join_address])
            
        try:
            # Start the process
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's still running
            if self.process.poll() is None:
                logger.info(f"Started server {self.server_id} on port {self.port}")
                return True
            else:
                stdout, stderr = self.process.communicate()
                logger.error(f"Server {self.server_id} failed to start: {stderr}")
                self.process = None
                return False
                
        except Exception as e:
            logger.error(f"Error starting server {self.server_id}: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the server process."""
        if not self.process:
            return
            
        logger.info(f"Stopping server {self.server_id}...")
        
        try:
            # Send termination signal
            self.process.terminate()
            
            # Wait for process to terminate
            self.process.wait(timeout=5)
            
            logger.info(f"Server {self.server_id} stopped")
            
        except subprocess.TimeoutExpired:
            # Force kill if it didn't terminate
            logger.warning(f"Server {self.server_id} not responding, force killing...")
            self.process.kill()
            
        except Exception as e:
            logger.error(f"Error stopping server {self.server_id}: {e}")
            
        finally:
            self.process = None
    
    def is_running(self) -> bool:
        """Check if the server process is running."""
        return self.process is not None and self.process.poll() is None
    
    def get_address(self) -> str:
        """Get the server address."""
        return self.address

class FaultToleranceTest:
    """Test harness for fault tolerance testing."""
    
    def __init__(self, num_servers: int = 5, base_port: int = 8001):
        """
        Initialize the test harness.
        
        Args:
            num_servers: Number of servers to run
            base_port: Starting port number
        """
        self.num_servers = num_servers
        self.base_port = base_port
        self.servers: Dict[str, ServerProcess] = {}
        self.clients: List[ChatClient] = []
        
        # Test data
        self.test_users = [
            ("user1", "password1"),
            ("user2", "password2"),
            ("user3", "password3")
        ]
        
        # Create data directory
        os.makedirs("./test_data", exist_ok=True)
        
    def setup_cluster(self) -> bool:
        """
        Set up a server cluster for testing.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Start the first server (leader)
            server_id = f"server1"
            port = self.base_port
            data_dir = f"./test_data/{server_id}"
            os.makedirs(data_dir, exist_ok=True)
            
            server = ServerProcess(server_id, port, data_dir)
            if not server.start():
                return False
                
            self.servers[server_id] = server
            leader_address = server.get_address()
            
            # Start additional servers
            for i in range(2, self.num_servers + 1):
                server_id = f"server{i}"
                port = self.base_port + i - 1
                data_dir = f"./test_data/{server_id}"
                os.makedirs(data_dir, exist_ok=True)
                
                server = ServerProcess(server_id, port, data_dir, leader_address)
                if not server.start():
                    self.teardown_cluster()
                    return False
                    
                self.servers[server_id] = server
                
                # Give it time to join the cluster
                time.sleep(1)
            
            # Create client
            server_addresses = [s.get_address() for s in self.servers.values()]
            self.client = ChatClient(server_addresses)
            
            # Wait for cluster to stabilize
            time.sleep(5)
            
            logger.info(f"Cluster of {self.num_servers} servers set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up cluster: {e}")
            self.teardown_cluster()
            return False
    
    def teardown_cluster(self) -> None:
        """Tear down the server cluster."""
        logger.info("Tearing down cluster...")
        
        # Stop all servers
        for server in self.servers.values():
            server.stop()
            
        self.servers.clear()
        self.client = None
    
    def register_users(self) -> bool:
        """
        Register test users.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            for username, password in self.test_users:
                response = self.client.register(username, password)
                if not response.success:
                    logger.error(f"Failed to register user {username}: {response.message}")
                    return False
                    
            logger.info("All test users registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error registering users: {e}")
            return False
    
    def test_basic_functionality(self) -> bool:
        """
        Test basic functionality with all servers running.
        
        Returns:
            True if tests pass, False otherwise
        """
        try:
            # Login as first user
            username, password = self.test_users[0]
            response = self.client.login(username, password)
            if not response.success:
                logger.error(f"Failed to login as {username}: {response.message}")
                return False
            
            # Send a test message
            message = f"Test message at {time.time()}"
            recipient = self.test_users[1][0]
            response = self.client.send_message(recipient, message)
            if not response.success:
                logger.error(f"Failed to send message: {response.message}")
                return False
                
            logger.info("Basic functionality test passed")
            return True
            
        except Exception as e:
            logger.error(f"Error in basic functionality test: {e}")
            return False
    
    def test_leader_failure(self) -> bool:
        """
        Test system behavior when the leader fails.
        
        Returns:
            True if tests pass, False otherwise
        """
        try:
            # Get cluster status to find the leader
            status = self.client.get_cluster_status()
            if not status:
                logger.error("Failed to get cluster status")
                return False
                
            leader_id = status.leader_id
            if not leader_id:
                logger.error("No leader found in cluster")
                return False
                
            # Find a follower server to ensure we can connect after leader fails
            follower_address = None
            for server_id, info in status.servers.items():
                if server_id != leader_id:
                    follower_address = info.address
                    break
                    
            if not follower_address:
                logger.error("No follower server found")
                return False
                
            # Create a client connected to the follower
            follower_client = ChatClient([follower_address])
            
            # Make sure we can login
            username, password = self.test_users[0]
            response = follower_client.login(username, password)
            if not response.success:
                logger.error(f"Failed to login to follower as {username}")
                return False
            
            # Kill the leader
            for server_id, server in self.servers.items():
                if server_id == leader_id:
                    logger.info(f"Stopping leader server {server_id}...")
                    server.stop()
                    break
            
            # Give time for a new leader to be elected
            time.sleep(5)
            
            # Check if a new leader was elected
            new_status = follower_client.get_cluster_status()
            if not new_status:
                logger.error("Failed to get cluster status after leader failure")
                return False
                
            if not new_status.leader_id:
                logger.error("No new leader elected after leader failure")
                return False
                
            if new_status.leader_id == leader_id:
                logger.error("Leader did not change after failure")
                return False
                
            # Try sending a message via the new leader
            message = f"Message after leader failure at {time.time()}"
            recipient = self.test_users[1][0]
            response = follower_client.send_message(recipient, message)
            if not response.success:
                logger.error(f"Failed to send message after leader failure: {response.message}")
                return False
                
            logger.info(f"Leader failure test passed: New leader {new_status.leader_id} elected")
            return True
            
        except Exception as e:
            logger.error(f"Error in leader failure test: {e}")
            return False
    
    def test_multiple_server_failure(self) -> bool:
        """
        Test system behavior when multiple servers fail.
        
        Returns:
            True if tests pass, False otherwise
        """
        try:
            # Get cluster status
            status = self.client.get_cluster_status()
            if not status:
                logger.error("Failed to get cluster status")
                return False
                
            # We need at least 3 servers for this test
            if len(status.servers) < 3:
                logger.error("Not enough servers for multiple failure test")
                return False
                
            # Kill two non-leader servers
            leader_id = status.leader_id
            killed_servers = []
            
            count = 0
            for server_id, server in self.servers.items():
                if server_id != leader_id and server.is_running() and count < 2:
                    logger.info(f"Stopping server {server_id}...")
                    server.stop()
                    killed_servers.append(server_id)
                    count += 1
            
            if count < 2:
                logger.error("Could not find 2 non-leader servers to kill")
                return False
                
            # Give time for the cluster to stabilize
            time.sleep(3)
            
            # Check if leader is still there
            new_status = self.client.get_cluster_status()
            if not new_status:
                logger.error("Failed to get cluster status after multiple failures")
                return False
                
            if not new_status.leader_id:
                logger.error("No leader found after multiple failures")
                return False
            
            # Try sending a message
            username, password = self.test_users[0]
            login_response = self.client.login(username, password)
            if not login_response.success:
                logger.error(f"Failed to login after multiple failures: {login_response.message}")
                return False
                
            message = f"Message after multiple failures at {time.time()}"
            recipient = self.test_users[1][0]
            response = self.client.send_message(recipient, message)
            if not response.success:
                logger.error(f"Failed to send message after multiple failures: {response.message}")
                return False
                
            logger.info("Multiple server failure test passed")
            return True
            
        except Exception as e:
            logger.error(f"Error in multiple server failure test: {e}")
            return False
    
    def test_quorum_loss(self) -> bool:
        """
        Test system behavior when quorum is lost.
        
        Returns:
            True if tests correctly detect quorum loss, False otherwise
        """
        try:
            # Get total number of servers
            status = self.client.get_cluster_status()
            if not status:
                logger.error("Failed to get cluster status")
                return False
                
            # Calculate majority
            total_servers = len(status.servers)
            majority = (total_servers // 2) + 1
            
            # Need to kill enough servers to break quorum
            servers_to_kill = majority
            
            # Kill servers
            killed = 0
            for server_id, server in self.servers.items():
                if server.is_running() and killed < servers_to_kill:
                    logger.info(f"Stopping server {server_id}...")
                    server.stop()
                    killed += 1
            
            # Give time for the cluster to recognize the failure
            time.sleep(5)
            
            # Try to perform an operation - it should fail or timeout
            username, password = self.test_users[0]
            try:
                # Set a short timeout since we expect this to fail
                channel = self.client.channel
                if channel:
                    old_timeout = channel.get_state(try_to_connect=False)
                    channel._channel.connectivity_watch.update_connectivity_state(
                        grpc.ChannelConnectivity.IDLE, None
                    )
                
                self.client.login(username, password, timeout=3)
                
                # If we got here, the test failed - operations shouldn't succeed without quorum
                logger.error("Operation succeeded despite quorum loss")
                return False
                
            except Exception as e:
                # We expect an error here
                logger.info(f"Operation correctly failed after quorum loss: {e}")
                return True
                
        except Exception as e:
            logger.error(f"Error in quorum loss test: {e}")
            return False
    
    def test_persistence(self) -> bool:
        """
        Test that data persists when servers restart.
        
        Returns:
            True if tests pass, False otherwise
        """
        try:
            # Login and send a unique message
            username, password = self.test_users[0]
            response = self.client.login(username, password)
            if not response.success:
                logger.error(f"Failed to login as {username}: {response.message}")
                return False
                
            unique_msg = f"Persistence test message {random.randint(10000, 99999)}"
            recipient = self.test_users[1][0]
            response = self.client.send_message(recipient, unique_msg)
            if not response.success:
                logger.error(f"Failed to send test message: {response.message}")
                return False
                
            # Restart all servers
            logger.info("Restarting all servers...")
            
            # Get current addresses before stopping
            addresses = [server.get_address() for server in self.servers.values()]
            
            # Stop all servers
            for server in self.servers.values():
                server.stop()
                
            # Wait a moment
            time.sleep(2)
            
            # Restart all servers
            for server_id, server in self.servers.items():
                # Data directories are preserved, so the state should be recovered
                server.process = None  # Reset process reference
                server.start()
                time.sleep(1)
                
            # Wait for cluster to stabilize
            time.sleep(5)
            
            # Create a new client
            new_client = ChatClient(addresses)
            
            # Login as the second user to check messages
            recipient_user, recipient_pwd = self.test_users[1]
            response = new_client.login(recipient_user, recipient_pwd)
            if not response.success:
                logger.error(f"Failed to login as recipient after restart: {response.message}")
                return False
                
            # Fetch messages
            messages = new_client.get_messages()
            
            # Check if our unique message is present
            found = False
            for msg in messages:
                if msg.content == unique_msg:
                    found = True
                    break
                    
            if not found:
                logger.error("Persistence test failed: Message not found after server restart")
                return False
                
            logger.info("Persistence test passed: Message found after server restart")
            return True
            
        except Exception as e:
            logger.error(f"Error in persistence test: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """
        Run all fault tolerance tests.
        
        Returns:
            Dictionary mapping test names to results
        """
        logger.info("Starting fault tolerance test suite...")
        
        results = {}
        
        try:
            # Setup
            if not self.setup_cluster():
                logger.error("Failed to set up test cluster")
                return {"setup": False}
                
            results["setup"] = True
            
            # Register test users
            if not self.register_users():
                logger.error("Failed to register test users")
                results["register_users"] = False
                self.teardown_cluster()
                return results
                
            results["register_users"] = True
            
            # Basic functionality test
            results["basic_functionality"] = self.test_basic_functionality()
            
            # Leader failure test
            results["leader_failure"] = self.test_leader_failure()
            
            # Multiple server failure test
            results["multiple_server_failure"] = self.test_multiple_server_failure()
            
            # Restart with new instances to test persistence
            self.teardown_cluster()
            if not self.setup_cluster():
                logger.error("Failed to set up cluster for persistence test")
                results["persistence"] = False
            else:
                results["persistence"] = self.test_persistence()
            
            # Quorum loss test - do this last as it breaks the cluster
            results["quorum_loss"] = self.test_quorum_loss()
            
        finally:
            # Cleanup
            self.teardown_cluster()
            
        # Print summary
        logger.info("Test results:")
        for test, result in results.items():
            logger.info(f"  {test}: {'PASS' if result else 'FAIL'}")
            
        return results

def main():
    """Main entry point for fault tolerance tests."""
    parser = argparse.ArgumentParser(description="Run fault tolerance tests")
    parser.add_argument('--servers', type=int, default=5, help='Number of servers in test cluster')
    parser.add_argument('--base-port', type=int, default=8001, help='Base port for servers')
    
    args = parser.parse_args()
    
    # Create and run tests
    test = FaultToleranceTest(num_servers=args.servers, base_port=args.base_port)
    results = test.run_all_tests()
    
    # Determine exit code based on test results
    failed_tests = [test for test, result in results.items() if not result]
    if failed_tests:
        logger.error(f"Failed tests: {', '.join(failed_tests)}")
        sys.exit(1)
    else:
        logger.info("All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
