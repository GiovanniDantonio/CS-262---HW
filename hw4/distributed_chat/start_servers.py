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
    
    # Create log file
    log_file = open(f"server_{node_id}.log", "a")
    
    return subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        preexec_fn=os.setpgrp  # Create new process group
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
        time.sleep(2)
    
    print("\nAll servers started!")
    print("Available servers:")
    for server in servers:
        print(f"  - {server}")
    print("\nPress Ctrl+C to stop all servers")
    
    try:
        # Monitor server processes
        while True:
            for node_id, proc in list(processes.items()):
                if proc.poll() is not None:
                    print(f"\nServer {node_id} died! Check server_{node_id}.log for details")
                    print("Restarting...")
                    port = BASE_PORT + int(node_id) - 1
                    processes[node_id] = start_server(node_id, port, servers)
                    time.sleep(2)  # Wait for restart
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all servers...")
        for proc in processes.values():
            try:
                # Kill entire process group
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=5)
            except:
                # Force kill if it doesn't respond
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except:
                    pass

if __name__ == "__main__":
    main()
