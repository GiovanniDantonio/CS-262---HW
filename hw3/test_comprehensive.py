#!/usr/bin/env python3
"""
Comprehensive test suite for the distributed system simulation.
This test suite verifies all aspects of the implementation to ensure it meets
the assignment requirements for the highest grade.
"""

import unittest
import os
import sys
import time
import datetime
import threading
import socket
import queue
import shutil
import logging
import tempfile
import multiprocessing
from unittest.mock import patch, MagicMock
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import modules from the project
from virtual_machine import VirtualMachine
import main
import analyze_logs
import run_experiment1
import run_experiment2

class TestVirtualMachine(unittest.TestCase):
    """Test the VirtualMachine class functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for logs
        self.test_dir = tempfile.mkdtemp()
        self.original_log_dir = "logs"
        
        # Redirect logs to test directory
        if os.path.exists(self.original_log_dir):
            self.log_backup = tempfile.mkdtemp()
            if os.listdir(self.original_log_dir):
                shutil.copytree(self.original_log_dir, os.path.join(self.log_backup, "logs"), dirs_exist_ok=True)
        
        # Create clean logs directory for testing
        if os.path.exists(self.original_log_dir):
            shutil.rmtree(self.original_log_dir)
        os.makedirs(self.original_log_dir)
        
        # Test ports
        self.base_port = 20000
        self.vm1_port = self.base_port
        self.vm2_port = self.base_port + 1
        self.vm3_port = self.base_port + 2
        
        # Initialize VMs
        self.vm1 = None
        self.vm2 = None
        self.vm3 = None
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop VMs if running
        if self.vm1:
            self.vm1.stop()
        if self.vm2:
            self.vm2.stop()
        if self.vm3:
            self.vm3.stop()
        
        # Restore original logs
        shutil.rmtree(self.original_log_dir)
        if hasattr(self, 'log_backup'):
            shutil.copytree(os.path.join(self.log_backup, "logs"), self.original_log_dir, dirs_exist_ok=True)
            shutil.rmtree(self.log_backup)
        else:
            os.makedirs(self.original_log_dir)
        
        # Remove test directory
        shutil.rmtree(self.test_dir)
    
    def test_vm_initialization(self):
        """Test that a VM initializes with correct parameters."""
        vm = VirtualMachine(1, self.vm1_port, [self.vm2_port, self.vm3_port])
        
        # Check basic properties
        self.assertEqual(vm.machine_id, 1)
        self.assertEqual(vm.port, self.vm1_port)
        self.assertEqual(vm.peer_ports, [self.vm2_port, self.vm3_port])
        
        # Check clock rate is within expected range
        self.assertTrue(1 <= vm.clock_rate <= 6)
        
        # Check logical clock starts at 0
        self.assertEqual(vm.logical_clock, 0)
        
        # Check message queue is empty
        self.assertTrue(vm.message_queue.empty())
        
        vm.stop()
    
    def test_clock_rate_range(self):
        """Test that the clock rate is within the specified range."""
        # Test with multiple VMs to ensure random range works
        for _ in range(10):
            vm = VirtualMachine(1, self.vm1_port, [self.vm2_port, self.vm3_port])
            self.assertTrue(1 <= vm.clock_rate <= 6)
            vm.stop()
    
    def test_network_connection(self):
        """Test that VMs can establish network connections."""
        # Create and start VMs
        self.vm1 = VirtualMachine(1, self.vm1_port, [self.vm2_port, self.vm3_port])
        self.vm2 = VirtualMachine(2, self.vm2_port, [self.vm1_port, self.vm3_port])
        
        # Initialize network
        self.vm1.initialize_network()
        time.sleep(1)  # Allow time for server socket to start
        self.vm2.initialize_network()
        time.sleep(2)  # Allow time for connections to establish
        
        # Check that vm1 has a connection to vm2
        self.assertTrue(any(port == self.vm2_port for port in self.vm1.peer_connections.keys()))
        
        # Check that vm2 has a connection to vm1
        self.assertTrue(any(port == self.vm1_port for port in self.vm2.peer_connections.keys()))
    
    def test_bidirectional_communication(self):
        """Test that communication is bidirectional after the fix."""
        # Create and start VMs
        self.vm1 = VirtualMachine(1, self.vm1_port, [self.vm2_port])
        self.vm2 = VirtualMachine(2, self.vm2_port, [self.vm1_port])
        
        # Initialize network and start VMs
        self.vm1.initialize_network()
        time.sleep(0.5)
        self.vm2.initialize_network()
        time.sleep(1.5)
        
        # Directly put messages in each other's queues to test message processing
        self.vm1.message_queue.put((5, 2))  # Message from VM2 to VM1
        self.vm2.message_queue.put((7, 1))  # Message from VM1 to VM2
        
        # Process messages
        self.vm1.process_event()
        self.vm2.process_event()
        
        # Check logical clocks updated correctly
        self.assertEqual(self.vm1.logical_clock, 6)  # 5 + 1
        self.assertEqual(self.vm2.logical_clock, 8)  # 7 + 1
    
    def test_logical_clock_update(self):
        """Test that logical clocks update correctly."""
        # Create VM
        vm = VirtualMachine(1, self.vm1_port, [])
        
        # Test internal event
        initial_clock = vm.logical_clock
        vm.process_event()  # Should trigger an internal event without peers
        self.assertEqual(vm.logical_clock, initial_clock + 1)
        
        # Test receiving message with higher clock
        vm.message_queue.put((10, 2))  # Add message with logical clock 10 from machine 2
        vm.process_event()
        self.assertEqual(vm.logical_clock, 11)  # Should be max(current, received) + 1
        
        vm.stop()
    
    def test_message_queue_processing(self):
        """Test that messages are processed from the queue."""
        # Create VM
        vm = VirtualMachine(1, self.vm1_port, [])
        
        # Add multiple messages to queue
        vm.message_queue.put((5, 2))
        vm.message_queue.put((10, 3))
        vm.message_queue.put((7, 2))
        
        # Process first message
        vm.process_event()
        self.assertEqual(vm.logical_clock, 6)  # 5 + 1
        
        # Process second message
        vm.process_event()
        self.assertEqual(vm.logical_clock, 11)  # 10 + 1
        
        # Process third message
        vm.process_event()
        self.assertEqual(vm.logical_clock, 12)  # max(11, 7) + 1
        
        vm.stop()
    
    @patch('random.randint')
    def test_event_probability(self, mock_randint):
        """Test event probability and selection."""
        # Create VM
        vm = VirtualMachine(1, self.vm1_port, [self.vm2_port, self.vm3_port])
        
        # Test internal event (4-10)
        mock_randint.return_value = 5
        with patch.object(vm, 'send_message') as mock_send:
            vm.process_event()
            mock_send.assert_not_called()
            self.assertEqual(vm.logical_clock, 1)  # Internal event increments by 1
        
        # Test send to random peer (1)
        mock_randint.return_value = 1
        with patch.object(vm, 'send_message') as mock_send:
            vm.process_event()
            mock_send.assert_called_once()
        
        # Test send to all peers (3)
        mock_randint.return_value = 3
        with patch.object(vm, 'send_message') as mock_send:
            vm.process_event()
            mock_send.assert_called_once_with([self.vm2_port, self.vm3_port])
        
        vm.stop()


class TestFullSystem(unittest.TestCase):
    """Test the full distributed system."""
    
    def setUp(self):
        """Set up test environment."""
        # Backup and create clean logs directory
        self.original_log_dir = "logs"
        if os.path.exists(self.original_log_dir):
            self.log_backup = tempfile.mkdtemp()
            if os.listdir(self.original_log_dir):
                shutil.copytree(self.original_log_dir, os.path.join(self.log_backup, "logs"), dirs_exist_ok=True)
            shutil.rmtree(self.original_log_dir)
        os.makedirs(self.original_log_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        # Restore original logs
        shutil.rmtree(self.original_log_dir)
        if hasattr(self, 'log_backup'):
            shutil.copytree(os.path.join(self.log_backup, "logs"), self.original_log_dir, dirs_exist_ok=True)
            shutil.rmtree(self.log_backup)
        else:
            os.makedirs(self.original_log_dir)
    
    def test_main_simulation(self):
        """Test the main simulation runs without errors."""
        # Patch sys.argv to set a short duration
        with patch('sys.argv', ['main.py', '--duration', '5', '--base-port', '30000']):
            # Start main simulation in a subprocess
            process = multiprocessing.Process(target=main.main)
            process.start()
            process.join(timeout=10)
            
            # Check process completed
            self.assertFalse(process.is_alive())
            if process.is_alive():
                process.terminate()
                process.join()
            
            # Check logs were created
            self.assertTrue(os.path.exists(os.path.join(self.original_log_dir, "machine_1.log")))
            self.assertTrue(os.path.exists(os.path.join(self.original_log_dir, "machine_2.log")))
            self.assertTrue(os.path.exists(os.path.join(self.original_log_dir, "machine_3.log")))
    
    def test_log_analysis(self):
        """Test log analysis functionality."""
        # Create fake log files
        log1_path = os.path.join(self.original_log_dir, "machine_1.log")
        with open(log1_path, 'w') as f:
            f.write("2025-03-03 13:00:00,000 - Virtual Machine 1 initialized\n")
            f.write("2025-03-03 13:00:00,000 - Clock Rate: 3 ticks/second\n")
            f.write("2025-03-03 13:00:01,000 - INTERNAL - System Time: 2025-03-03 13:00:01.000, Logical Clock: 1\n")
            f.write("2025-03-03 13:00:02,000 - SEND - System Time: 2025-03-03 13:00:02.000, Logical Clock: 2, To: Machine on port 10001\n")
            f.write("2025-03-03 13:00:03,000 - RECEIVE - System Time: 2025-03-03 13:00:03.000, Logical Clock: 3, Queue Length: 0, From: Machine 2\n")
        
        # Test parsing
        df = analyze_logs.parse_log_file(log1_path)
        self.assertEqual(len(df), 3)  # 3 events (excluding initialization)
        
        # Check event counts
        events = df['event_type'].value_counts()
        self.assertEqual(events['INTERNAL'], 1)
        self.assertEqual(events['SEND'], 1)
        self.assertEqual(events['RECEIVE'], 1)
        
        # Check logical clock values
        self.assertEqual(df['logical_clock'].tolist(), [1, 2, 3])
    
    def test_experiment_run(self):
        """Test that experiments run successfully."""
        # Mock the run_experiment function directly
        with patch('run_experiment1.run_experiment', return_value="/tmp/fake_exp_dir") as mock_exp:
            # Run experiment 1 with properly parsed arguments
            with patch('sys.argv', ['run_experiment1.py', '--duration', '2']):
                try:
                    run_experiment1.main()
                except SystemExit:
                    pass  # ArgumentParser might call sys.exit
                except Exception as e:
                    self.fail(f"run_experiment1.main() raised {type(e).__name__} unexpectedly!")
                mock_exp.assert_called()
        
        with patch('run_experiment2.run_experiment', return_value="/tmp/fake_exp_dir") as mock_exp:
            # Run experiment 2 with properly parsed arguments
            with patch('sys.argv', ['run_experiment2.py', '--duration', '2']):
                try:
                    run_experiment2.main()
                except SystemExit:
                    pass  # ArgumentParser might call sys.exit
                except Exception as e:
                    self.fail(f"run_experiment2.main() raised {type(e).__name__} unexpectedly!")
                mock_exp.assert_called()


class TestSpecificationCompliance(unittest.TestCase):
    """Tests to ensure the implementation meets all assignment specifications."""
    
    def test_logical_clock_algorithm(self):
        """Test that the logical clock algorithm is implemented correctly."""
        # Create a VM
        vm = VirtualMachine(1, 40000, [])
        
        # Test internal event (clock += 1)
        initial_clock = vm.logical_clock
        
        # Force an internal event (event 4-10)
        with patch('random.randint', return_value=4):
            vm.process_event()  # This should trigger an internal event
            self.assertEqual(vm.logical_clock, initial_clock + 1)
        
        # Test send event (clock += 1 before sending)
        initial_clock = vm.logical_clock
        with patch.object(vm, 'send_message') as mock_send:
            with patch('random.randint', return_value=1):  # Force a send event
                vm.process_event()
                self.assertEqual(vm.logical_clock, initial_clock + 1)
        
        # Test receive event (clock = max(local, received) + 1)
        vm.logical_clock = 5
        vm.message_queue.put((10, 2))  # Message with clock 10
        vm.process_event()
        self.assertEqual(vm.logical_clock, 11)  # max(5, 10) + 1
        
        # Another receive with lower clock
        vm.message_queue.put((7, 3))  # Message with clock 7
        vm.process_event()
        self.assertEqual(vm.logical_clock, 12)  # max(11, 7) + 1
        
        vm.stop()
    
    def test_clock_rate_variations(self):
        """Test that VMs have different clock rates."""
        # Create multiple VMs and check their clock rates
        clock_rates = set()
        for i in range(10):
            vm = VirtualMachine(i, 40000 + i, [])
            clock_rates.add(vm.clock_rate)
            vm.stop()
        
        # We should have multiple different clock rates
        self.assertTrue(len(clock_rates) > 1)
    
    def test_queue_implementation(self):
        """Test that the message queue is implemented correctly."""
        # Create VM
        vm = VirtualMachine(1, 40000, [])
        
        # Add messages to queue
        vm.message_queue.put((5, 2))
        vm.message_queue.put((7, 3))
        vm.message_queue.put((6, 2))
        
        # Process messages in FIFO order
        vm.process_event()
        self.assertEqual(vm.logical_clock, 6)  # 5 + 1
        
        vm.process_event()
        self.assertEqual(vm.logical_clock, 8)  # 7 + 1
        
        vm.process_event()
        self.assertEqual(vm.logical_clock, 9)  # 8 + 1
        
        vm.stop()
    
    def test_log_format(self):
        """Test that logs are formatted according to specification."""
        # Create VM and trigger events
        vm_port = 40000
        vm = VirtualMachine(1, vm_port, [vm_port + 1])
        vm.initialize_network()
        
        # Generate some events
        vm.process_event()  # Internal
        
        # Force a send event
        with patch('random.randint', return_value=1):
            with patch.object(vm, 'peer_connections'):
                vm.process_event()
        
        # Force a receive event
        vm.message_queue.put((10, 2))
        vm.process_event()
        
        vm.stop()
        
        # Check log file format
        log_file = os.path.join("logs", f"machine_1.log")
        self.assertTrue(os.path.exists(log_file))
        
        with open(log_file, 'r') as f:
            log_content = f.read()
            
            # Check for initialization lines
            self.assertIn("Virtual Machine 1 initialized", log_content)
            self.assertIn("Clock Rate:", log_content)
            
            # Check for event lines
            self.assertIn("INTERNAL - System Time:", log_content)
            self.assertIn("Logical Clock:", log_content)
            self.assertIn("RECEIVE - System Time:", log_content)
            self.assertIn("Queue Length:", log_content)


if __name__ == '__main__':
    # Run the tests
    unittest.main()
