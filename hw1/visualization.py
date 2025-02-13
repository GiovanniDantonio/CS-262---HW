#!/usr/bin/env python3

import matplotlib.pyplot as plt

# Data from your results
iterations = [100, 1000, 10000, 100000]
json_times = [0.0042, 0.0383, 0.8517, 5.5591]
custom_times = [0.0059, 0.0684, 0.7982, 5.9629]

# Create a new figure
plt.figure(figsize=(8, 5))

# Plot JSON times
plt.plot(iterations, json_times, marker='o', label='JSON')

# Plot Custom times
plt.plot(iterations, custom_times, marker='o', label='Custom')

# Label the axes
plt.xlabel('Number of Iterations')
plt.ylabel('Deserialization Time (seconds)')

# Title and legend
plt.title('Deserialization Performance Comparison')
plt.legend()

# (Optional) Use a logarithmic scale for the x-axis if desired
plt.xscale('log')

# Show the plot
plt.show()
