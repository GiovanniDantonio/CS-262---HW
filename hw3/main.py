import time
import multiprocessing
import argparse
import os
from virtual_machine import VirtualMachine

def run_virtual_machine(machine_id, port, peer_ports):
    """
    Function to run a virtual machine in a separate process.
    
    Args:
        machine_id: ID of the virtual machine
        port: Port for this machine to listen on
        peer_ports: Ports of peer machines
    """
    try:
        vm = VirtualMachine(machine_id, port, peer_ports)
        vm.run()
    except KeyboardInterrupt:
        print(f"VM {machine_id} interrupted")
    finally:
        if 'vm' in locals():
            vm.stop()

def main():
    """
    Main function to set up and run the distributed system model.
    """
    parser = argparse.ArgumentParser(description="Run a distributed system model with logical clocks")
    parser.add_argument("--duration", type=int, default=60, help="Duration to run the simulation in seconds (default: 60)")
    parser.add_argument("--base-port", type=int, default=10000, help="Base port number for virtual machines (default: 10000)")
    args = parser.parse_args()
    
    # Define ports for the virtual machines
    base_port = args.base_port
    ports = [base_port, base_port + 1, base_port + 2]
    
    # Create log directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Create processes for each virtual machine
    processes = []
    for i in range(3):
        machine_id = i + 1
        port = ports[i]
        peer_ports = [p for p in ports if p != port]
        
        process = multiprocessing.Process(
            target=run_virtual_machine,
            args=(machine_id, port, peer_ports)
        )
        processes.append(process)
    
    try:
        # Start all processes
        print(f"Starting {len(processes)} virtual machines...")
        for p in processes:
            p.start()
            # Small delay to ensure machines start in order
            time.sleep(0.5)
        
        # Run for specified duration
        print(f"Running simulation for {args.duration} seconds...")
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("Simulation interrupted by user")
    finally:
        # Terminate all processes
        print("Terminating virtual machines...")
        for p in processes:
            if p.is_alive():
                p.terminate()
        
        # Wait for all processes to terminate
        for p in processes:
            p.join()
        
        print("Simulation complete. Check the log files in logs/ directory for results.")

if __name__ == "__main__":
    main()
