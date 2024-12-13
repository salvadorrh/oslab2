#!/usr/bin/env python3

import time
import os
import random
import numpy as np
import matplotlib.pyplot as plt

def scan_file_contents(filepath, pattern_size=1024):
    """
    Simulate searching through a file for specific patterns.
    This function reads the file in chunks and performs computations
    to simulate real-world pattern matching scenarios.
    """
    total_time = 0
    num_searches = 10  # Number of pattern searches to perform
    
    with open(filepath, 'rb') as f:
        # Read entire file once to simulate loading into memory
        file_content = f.read()
        file_size = len(file_content)
        
        # Perform multiple pattern searches to get meaningful timing data
        for _ in range(num_searches):
            start_time = time.time()
            # Simulate pattern matching by reading chunks throughout the file
            for pos in range(0, file_size - pattern_size, pattern_size):
                chunk = file_content[pos:pos + pattern_size]
                # Perform computation to prevent optimization
                _ = sum(chunk)
            total_time += time.time() - start_time
            
    return total_time

def run_pattern_search_test(filepath, iterations=3):
    """
    Run multiple pattern searches on the same file and collect performance data.
    Returns both initial caching time and subsequent search times.
    """
    print(f"\nTesting pattern search for: {filepath}")
    print("=" * 50)
    
    # Perform initial scan to ensure file is cached
    print("Initial scan (caching)...")
    first_time = scan_file_contents(filepath)
    print(f"Initial scan: {first_time:.3f} seconds")
    
    # Perform repeated scans
    times = []
    print("\nPerforming repeated scans...")
    for i in range(iterations):
        time_taken = scan_file_contents(filepath)
        times.append(time_taken)
        print(f"Scan {i+1}: {time_taken:.3f} seconds")
    
    return first_time, times

def plot_results(fuse_initial, fuse_times, nfs_initial, nfs_times, output_file='pattern_search_comparison.png'):
    """
    Create a detailed visualization comparing FUSE and NFS pattern search performance.
    Shows both initial caching performance and subsequent search performance.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot initial scan times (top subplot)
    initial_times = ['FUSE', 'NFS']
    times = [fuse_initial, nfs_initial]
    bars = ax1.bar(initial_times, times, color=['blue', 'red'])
    ax1.set_title('Initial Pattern Search Times (With Caching)')
    ax1.set_ylabel('Time (seconds)')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on the bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}s',
                ha='center', va='bottom')
    
    # Plot subsequent search times (bottom subplot)
    iterations = range(1, len(fuse_times) + 1)
    ax2.plot(iterations, fuse_times, 'b-o', label='FUSE Filesystem')
    ax2.plot(iterations, nfs_times, 'r-o', label='NFS')
    ax2.set_title('Subsequent Pattern Search Performance')
    ax2.set_xlabel('Search Iteration')
    ax2.set_ylabel('Time (seconds)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Add data point labels
    for i, (fuse_val, nfs_val) in enumerate(zip(fuse_times, nfs_times), 1):
        ax2.text(i, fuse_val, f'{fuse_val:.3f}s', ha='center', va='bottom')
        ax2.text(i, nfs_val, f'{nfs_val:.3f}s', ha='center', va='top')
    
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"\nPlot saved as {output_file}")

def main():
    # Configuration
    iterations = 3
    fuse_path = '/users/salvador/netfs_mount/searchfile'
    nfs_path = '/users/salvador/searchfile'
    
    print("Starting Pattern Search Performance Test")
    print("Testing repeated full-file pattern searching")
    print(f"Number of iterations: {iterations}")
    
    # Run benchmarks
    print("\nTesting FUSE filesystem...")
    fuse_initial, fuse_times = run_pattern_search_test(fuse_path, iterations)
    
    print("\nTesting NFS filesystem...")
    nfs_initial, nfs_times = run_pattern_search_test(nfs_path, iterations)
    
    # Calculate and display detailed statistics
    print("\nResults Summary")
    print("=" * 50)
    print("\nInitial Search Times (with caching):")
    print(f"FUSE Initial: {fuse_initial:.3f} seconds")
    print(f"NFS Initial: {nfs_initial:.3f} seconds")
    
    print("\nSubsequent Search Performance:")
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