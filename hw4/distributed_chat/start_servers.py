#!/usr/bin/env python3
"""
Script to start multiple chat server nodes.
"""
import os
import sys
import time
import signal
import subprocess
from typing import List, Dict

# Number of server nodes to start
NUM_SERVERS = 3

# Base port for servers
BASE_PORT = 50051

def start_server(node_id: str, port: int, peers: List[str]) -> subprocess.Popen:
    """
    Start a chat server node.
    
    Args:
        node_id: Node identifier
        port: Port to listen on
        peers: List of peer addresses
        
    Returns:
        subprocess.Popen: Server process
    """
    cmd = [
        sys.executable,
        "server.py",
        "--node-id", node_id,
        "--port", str(port),
        "--peers"
    ] + peers
    
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

def main():
    """Start multiple server nodes."""
    # Create list of server addresses
    servers = [f"localhost:{BASE_PORT + i}" for i in range(NUM_SERVERS)]
    
    # Start each server
    processes = {}
    for i in range(NUM_SERVERS):
        node_id = str(i + 1)
        port = BASE_PORT + i
        
        print(f"Starting server {node_id} on port {port}...")
        proc = start_server(node_id, port, servers)
        processes[node_id] = proc
        
        # Wait a bit to let server initialize
        time.sleep(1)
    
    print("\nAll servers started!")
    print("Available servers:")
    for server in servers:
        print(f"  - {server}")
    
    print("\nPress Ctrl+C to stop all servers")
    
    try:
        # Monitor server processes
        while True:
            for node_id, proc in processes.items():
                if proc.poll() is not None:
                    print(f"\nServer {node_id} died! Restarting...")
                    port = BASE_PORT + int(node_id) - 1
                    processes[node_id] = start_server(node_id, port, servers)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all servers...")
        for proc in processes.values():
            if proc.poll() is None:
                proc.terminate()
                proc.wait()

if __name__ == "__main__":
    main()
