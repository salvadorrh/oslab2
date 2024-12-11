#!#!/usr/bin/env python3

import time
import os
import matplotlib.pyplot as plt
import numpy as np

def read_file_with_timing(filepath):
    """Read a file completely and return the time taken in seconds."""
    start_time = time.time()
    with open(filepath, 'rb') as f:
        # Read the entire file in chunks to handle large files efficiently
        chunk_size = 1024 * 1024  # 1MB chunks
        while f.read(chunk_size):
            pass
    end_time = time.time()
    return end_time - start_time

def run_benchmark(filepath, iterations=5):
    """Run multiple iterations of reading a file and collect timing data."""
    results = []
    print(f"\nTesting file: {filepath}")
    print("=" * 50)
    
    for i in range(iterations):
        # Clear system cache between runs for more accurate measurements
        os.system("sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'")
        
        time_taken = read_file_with_timing(filepath)
        results.append(time_taken)
        print(f"Iteration {i+1}: {time_taken:.3f} seconds")
    
    return results

def plot_results(fuse_times, nfs_times, output_file='filesystem_comparison.png'):
    """Create a comparison plot of FUSE vs NFS performance."""
    iterations = range(1, len(fuse_times) + 1)
    
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, fuse_times, 'b-o', label='FUSE Filesystem')
    plt.plot(iterations, nfs_times, 'r-o', label='NFS')
    
    plt.title('Filesystem Read Performance Comparison')
    plt.xlabel('Iteration Number')
    plt.ylabel('Time (seconds)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig(output_file)
    print(f"\nPlot saved as {output_file}")

def main():
    # Configuration
    iterations = 5
    fuse_path = '/users/salvador/netfs_mount/testfile'
    nfs_path = '/users/salvador/nfs_testfile'
    
    print("Starting Filesystem Performance Comparison")
    print("Testing repeated reads of the same file")
    print(f"Number of iterations: {iterations}")
    
    # Run benchmarks
    print("\nTesting FUSE filesystem...")
    fuse_times = run_benchmark(fuse_path, iterations)
    
    print("\nTesting NFS filesystem...")
    nfs_times = run_benchmark(nfs_path, iterations)
    
    # Calculate and display statistics
    print("\nResults Summary")
    print("=" * 50)
    print(f"FUSE Average: {np.mean(fuse_times):.3f} seconds")
    print(f"NFS Average: {np.mean(nfs_times):.3f} seconds")
    print(f"FUSE First Read: {fuse_times[0]:.3f} seconds")
    print(f"NFS First Read: {nfs_times[0]:.3f} seconds")
    print(f"FUSE Subsequent Reads Average: {np.mean(fuse_times[1:]):.3f} seconds")
    print(f"NFS Subsequent Reads Average: {np.mean(nfs_times[1:]):.3f} seconds")
    
    # Create visualization
    plot_results(fuse_times, nfs_times)

if __name__ == "__main__":
    main()