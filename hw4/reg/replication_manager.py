"""Replication Manager for handling fault tolerance and persistence."""
import json
import logging
import os
import threading
import time
import grpc
import sqlite3
from concurrent import futures
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReplicationManager:
    def __init__(self, replica_id):
        self.replica_id = replica_id
        self.config = self._load_config()
        self.is_leader = False
        self.current_leader = None
        self.last_heartbeat = {}
        self.lock = threading.Lock()
        self.replicas = {replica['id']: replica for replica in self.config['replicas']}
        self.leader_check_interval = self.config.get('leader_check_interval', 3)
        self.client_connections = {}
        
        # Initialize heartbeat for self
        with self.lock:
            self.last_heartbeat[self.replica_id] = time.time()
        
        # Start leader election and heartbeat threads
        self.stop_threads = False
        self.election_thread = threading.Thread(target=self._run_leader_election)
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeats)
        self.election_thread.start()
        self.heartbeat_thread.start()

    def _load_config(self):
        """Load replication configuration."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "replicated_config.json")
        with open(config_path, 'r') as f:
            return json.load(f)

    def _notify_clients_of_leader_change(self, new_leader_id):
        """Notify connected clients about the new leader."""
        new_leader_info = self.replicas[new_leader_id]
        new_leader_addr = f"{new_leader_info['host']}:{new_leader_info['port']}"
        
        # Send leader update through gRPC stream
        for client_id, stream_context in self.client_connections.items():
            try:
                # Send leader update through existing stream
                update = chat_pb2.ServerUpdate(
                    type="LEADER_CHANGE",
                    new_leader_address=new_leader_addr
                )
                stream_context.send(update)
            except Exception as e:
                logger.error(f"Failed to notify client {client_id} of leader change: {e}")

    def _run_leader_election(self):
        """Run leader election process."""
        while not self.stop_threads:
            with self.lock:
                current_time = time.time()
                
                # Check if current leader is alive
                if self.current_leader is not None:
                    last_seen = self.last_heartbeat.get(self.current_leader, 0)
                    if current_time - last_seen > self.leader_check_interval * 2:
                        # Leader is considered dead, start election
                        self._elect_new_leader()
                
                # If no leader, start election
                if self.current_leader is None:
                    self._elect_new_leader()
            
            time.sleep(self.leader_check_interval)

    def _elect_new_leader(self):
        """Elect a new leader based on replica ID."""
        # Find the replica with lowest ID that's still alive
        current_time = time.time()
        alive_replicas = [
            rid for rid in self.replicas.keys()
            if current_time - self.last_heartbeat.get(rid, 0) <= self.leader_check_interval * 2
        ]
        
        if alive_replicas:
            new_leader = min(alive_replicas)
            if new_leader != self.current_leader:
                old_leader = self.current_leader
                self.current_leader = new_leader
                self.is_leader = (new_leader == self.replica_id)
                
                if self.is_leader:
                    logger.info(f"Replica {self.replica_id} becoming new leader")
                    # Notify clients of leader change
                    self._notify_clients_of_leader_change(new_leader)
                    
                    # Sync data from old leader if possible
                    if old_leader is not None:
                        self._sync_data_from_old_leader(old_leader)
        else:
            logger.error("No alive replicas found for leader election")

    def register_client_connection(self, client_id, stream_context):
        """Register a client's stream context for updates."""
        with self.lock:
            self.client_connections[client_id] = stream_context
            
    def unregister_client_connection(self, client_id):
        """Unregister a client's stream context."""
        with self.lock:
            self.client_connections.pop(client_id, None)

    def _send_heartbeats(self):
        """Send heartbeats to other replicas."""
        while not self.stop_threads:
            # Always update own heartbeat
            with self.lock:
                self.last_heartbeat[self.replica_id] = time.time()
                
            if self.is_leader:
                for replica_id in self.replicas:
                    if replica_id != self.replica_id:
                        try:
                            # In a real implementation, we would use gRPC to send heartbeats
                            # For now, we just update the timestamp locally
                            logger.debug(f"Leader {self.replica_id} sending heartbeat")
                        except Exception as e:
                            logger.error(f"Failed to send heartbeat to replica {replica_id}: {e}")
            time.sleep(1)

    def replicate_data(self, query, params=()):
        """Replicate data to other replicas."""
        if not self.is_leader:
            return False

        success = True
        for replica_id, replica in self.replicas.items():
            if replica_id != self.replica_id:
                try:
                    conn = sqlite3.connect(replica['db_path'])
                    c = conn.cursor()
                    c.execute(query, params)
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"Failed to replicate to {replica_id}: {e}")
                    success = False

        return success

    def stop(self):
        """Stop replication manager threads."""
        self.stop_threads = True
        self.election_thread.join()
        self.heartbeat_thread.join()

    def get_replica_info(self):
        """Get current replica's configuration."""
        return self.replicas[self.replica_id]

    @property
    def is_replica_active(self):
        """Check if this replica should be active."""
        return True  # In a real implementation, we would check cluster health

    def _sync_data_from_old_leader(self, old_leader_id):
        """Sync data from old leader."""
        # This method is not implemented in the provided code
        pass
