#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np

# Use non-interactive backend
plt.switch_backend('Agg')

# Benchmark results
iterations = [100, 1000, 10000]

# Performance data (in seconds)
grpc_serialize = [0.0021, 0.0202, 0.2040]
json_serialize = [0.0009, 0.0089, 0.0921]
grpc_deserialize = [0.0000, 0.0005, 0.0046]
json_deserialize = [0.0003, 0.0025, 0.0253]

# Message size data (in bytes)
grpc_size = 56
json_size = 231

def create_performance_plot():
    """Create performance comparison plots"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    x = np.arange(len(iterations))
    width = 0.35
    
    # Serialization plot
    ax1.bar(x - width/2, grpc_serialize, width, label='gRPC', color='#2ecc71')
    ax1.bar(x + width/2, json_serialize, width, label='JSON', color='#3498db')
    ax1.set_ylabel('Time (seconds)')
    ax1.set_xlabel('Number of Iterations')
    ax1.set_title('Serialization Performance')
    ax1.set_xticks(x)
    ax1.set_xticklabels(iterations)
    ax1.legend()
    
    # Add value labels
    for i, v in enumerate(grpc_serialize):
        ax1.text(i - width/2, v, f'{v:.4f}s', ha='center', va='bottom')
    for i, v in enumerate(json_serialize):
        ax1.text(i + width/2, v, f'{v:.4f}s', ha='center', va='bottom')
    
    # Deserialization plot
    ax2.bar(x - width/2, grpc_deserialize, width, label='gRPC', color='#2ecc71')
    ax2.bar(x + width/2, json_deserialize, width, label='JSON', color='#3498db')
    ax2.set_ylabel('Time (seconds)')
    ax2.set_xlabel('Number of Iterations')
    ax2.set_title('Deserialization Performance')
    ax2.set_xticks(x)
    ax2.set_xticklabels(iterations)
    ax2.legend()
    
    # Add value labels
    for i, v in enumerate(grpc_deserialize):
        ax2.text(i - width/2, v, f'{v:.4f}s', ha='center', va='bottom')
    for i, v in enumerate(json_deserialize):
        ax2.text(i + width/2, v, f'{v:.4f}s', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_size_comparison():
    """Create message size comparison plot"""
    plt.figure(figsize=(8, 6))
    
    sizes = [grpc_size, json_size]
    labels = ['gRPC', 'JSON']
    colors = ['#2ecc71', '#3498db']
    
    plt.bar(labels, sizes, color=colors)
    plt.ylabel('Size (bytes)')
    plt.title('Message Size Comparison')
    
    # Add value labels
    for i, v in enumerate(sizes):
        plt.text(i, v, f'{v} bytes', ha='center', va='bottom')
    
    plt.savefig('size_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    print("Creating visualization plots...")
    
    # Create performance comparison plots
    create_performance_plot()
    print("- Created performance_comparison.png")
    
    # Create size comparison plot
    create_size_comparison()
    print("- Created size_comparison.png")
    
    print("Done! The plots have been saved to the current directory.")
