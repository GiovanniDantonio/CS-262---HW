"""
Configuration management for fault-tolerant chat system.
"""
import json
import os
from typing import Dict, List

class ClusterConfig:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "cluster.json"
        )
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_config()
    
    def get_all_nodes(self) -> List[Dict]:
        """Get list of all nodes in cluster."""
        return self.config["nodes"]
    
    def get_node_by_id(self, node_id: int) -> Dict:
        """Get node configuration by ID."""
        for node in self.config["nodes"]:
            if node["id"] == node_id:
                return node
        raise ValueError(f"No node found with ID {node_id}")
    
    def get_client_retry_interval_ms(self) -> int:
        """Get client retry interval in milliseconds."""
        return self.config.get("client_retry_interval_ms", 1000)
    
    def _create_default_config(self) -> Dict:
        """Create default configuration."""
        config = {
            "nodes": [
                {
                    "id": 1,
                    "host": "localhost",
                    "port": 12345
                },
                {
                    "id": 2,
                    "host": "localhost",
                    "port": 12346
                },
                {
                    "id": 3,
                    "host": "localhost",
                    "port": 12347
                }
            ],
            "client_retry_interval_ms": 1000,
            "election_timeout_min_ms": 150,
            "election_timeout_max_ms": 300,
            "heartbeat_interval_ms": 50
        }
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save config to file
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)
        
        return config
