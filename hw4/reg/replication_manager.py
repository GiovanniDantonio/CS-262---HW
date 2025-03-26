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
        self.replicas = self.config['replicas']
        self.leader_check_interval = self.config.get('leader_check_interval', 3)
        
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

    def _run_leader_election(self):
        """Run leader election process."""
        while not self.stop_threads:
            with self.lock:
                current_time = time.time()
                # Check if current leader is alive
                if self.current_leader is not None:
                    last_beat = self.last_heartbeat.get(self.current_leader, 0)
                    if current_time - last_beat > self.leader_check_interval:
                        self.current_leader = None

                # If no leader, start election
                if self.current_leader is None:
                    # Simple election: highest available ID becomes leader
                    available_replicas = []
                    for replica in self.replicas:
                        if current_time - self.last_heartbeat.get(replica['id'], 0) <= self.leader_check_interval:
                            available_replicas.append(replica['id'])
                    
                    if available_replicas:
                        new_leader = max(available_replicas)
                        if new_leader == self.replica_id:
                            self.is_leader = True
                            logger.info(f"Replica {self.replica_id} became leader")
                        self.current_leader = new_leader

            time.sleep(1)

    def _send_heartbeats(self):
        """Send heartbeats to other replicas."""
        while not self.stop_threads:
            # Always update own heartbeat
            with self.lock:
                self.last_heartbeat[self.replica_id] = time.time()
                
            if self.is_leader:
                for replica in self.replicas:
                    if replica['id'] != self.replica_id:
                        try:
                            # In a real implementation, we would use gRPC to send heartbeats
                            # For now, we just update the timestamp locally
                            logger.debug(f"Leader {self.replica_id} sending heartbeat")
                        except Exception as e:
                            logger.error(f"Failed to send heartbeat to replica {replica['id']}: {e}")
            time.sleep(1)

    def replicate_data(self, query, params=()):
        """Replicate data to other replicas."""
        if not self.is_leader:
            return False

        success = True
        for replica in self.replicas:
            if replica['id'] != self.replica_id:
                try:
                    conn = sqlite3.connect(replica['db_path'])
                    c = conn.cursor()
                    c.execute(query, params)
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"Failed to replicate to {replica['id']}: {e}")
                    success = False

        return success

    def stop(self):
        """Stop replication manager threads."""
        self.stop_threads = True
        self.election_thread.join()
        self.heartbeat_thread.join()

    def get_replica_info(self):
        """Get current replica's configuration."""
        return next(r for r in self.replicas if r['id'] == self.replica_id)

    @property
    def is_replica_active(self):
        """Check if this replica should be active."""
        return True  # In a real implementation, we would check cluster health
