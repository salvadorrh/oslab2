#!/usr/bin/env python3

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

def run_rapid_reads_benchmark(filepath, iterations=5):
    """Run multiple reads of a file in rapid succession without clearing cache."""
    results = []
    print(f"\nTesting rapid reads for: {filepath}")
    print("=" * 50)
    
    # First read (caching phase)
    first_time = read_file_with_timing(filepath)
    print(f"Initial read (caching): {first_time:.3f} seconds")
    
    # Perform rapid successive reads
    for i in range(iterations):
        time_taken = read_file_with_timing(filepath)
        results.append(time_taken)
        print(f"Rapid read {i+1}: {time_taken:.3f} seconds")
    
    return first_time, results

def plot_results(fuse_initial, fuse_times, nfs_initial, nfs_times, output_file='rapid_reads_comparison.png'):
    """Create a detailed comparison plot of FUSE vs NFS performance."""
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot initial read times (top subplot)
    initial_times = ['FUSE', 'NFS']
    times = [fuse_initial, nfs_initial]
    ax1.bar(initial_times, times, color=['blue', 'red'])
    ax1.set_title('Initial Read Times (Caching Phase)')
    ax1.set_ylabel('Time (seconds)')
    ax1.grid(True)
    
    # Plot successive read times (bottom subplot)
    iterations = range(1, len(fuse_times) + 1)
    ax2.plot(iterations, fuse_times, 'b-o', label='FUSE Filesystem')
    ax2.plot(iterations, nfs_times, 'r-o', label='NFS')
    ax2.set_title('Successive Read Performance')
    ax2.set_xlabel('Iteration Number')
    ax2.set_ylabel('Time (seconds)')
    ax2.legend()
    ax2.grid(True)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"\nPlot saved as {output_file}")

def main():
    # Configuration
    iterations = 5
    fuse_path = '/users/salvador/netfs_mount/testfile2'
    nfs_path = '/users/salvador/nfs_testfile2'
    
    print("Starting Rapid Read Performance Test")
    print("Testing multiple rapid reads without cache clearing")
    print(f"Number of iterations: {iterations}")
    
    # Run benchmarks
    print("\nTesting FUSE filesystem...")
    fuse_initial, fuse_times = run_rapid_reads_benchmark(fuse_path, iterations)
    
    print("\nTesting NFS filesystem...")
    nfs_initial, nfs_times = run_rapid_reads_benchmark(nfs_path, iterations)
    
    # Calculate and display statistics
    print("\nResults Summary")
    print("=" * 50)
    print("Initial Read Times:")
    print(f"FUSE Initial: {fuse_initial:.3f} seconds")
    print(f"NFS Initial: {nfs_initial:.3f} seconds")
    print("\nSuccessive Reads:")
    print(f"FUSE Average: {np.mean(fuse_times):.3f} seconds")
    print(f"NFS Average: {np.mean(nfs_times):.3f} seconds")
    print(f"FUSE Min: {np.min(fuse_times):.3f} seconds")
    print(f"NFS Min: {np.min(nfs_times):.3f} seconds")
    print(f"FUSE Max: {np.max(fuse_times):.3f} seconds")
    print(f"NFS Max: {np.max(nfs_times):.3f} seconds")
    print(f"FUSE Std Dev: {np.std(fuse_times):.3f} seconds")
    print(f"NFS Std Dev: {np.std(nfs_times):.3f} seconds")
    
    # Create visualization
    plot_results(fuse_initial, fuse_times, nfs_initial, nfs_times)

if __name__ == "__main__":
    main()