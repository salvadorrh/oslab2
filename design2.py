#!/usr/bin/env python3

import time
import os
import matplotlib.pyplot as plt
import numpy as numpy

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
    
    # First read might be slower as it loads into cache
    first_time = read_file_with_timing(filepath)
    print(f"Initial read (caching): {first_time:.3f} seconds")
    
    # Now do rapid successive reads
    for i in range(iterations):
        time_taken = read_file_with_timing(filepath)
        results.append(time_taken)
        print(f"Rapid read {i+1}: {time_taken:.3f} seconds")
    
    return results

def main():
    # Configuration
    iterations = 5
    fuse_path = '/users/salvador/netfs_mount/testfile2'
    nfs_path = '/users/salvador/nfs_testfile2'
    
    print("Starting Rapid Read Performance Test")
    print("Testing multiple rapid reads without cache clearing")
    
    print("\nTesting FUSE filesystem...")
    fuse_times = run_rapid_reads_benchmark(fuse_path, iterations)
    
    print("\nTesting NFS filesystem...")
    nfs_times = run_rapid_reads_benchmark(nfs_path, iterations)
    
    # Show results
    print("\nResults Summary")
    print("=" * 50)
    print(f"FUSE Average: {numpy.mean(fuse_times):.3f} seconds")
    print(f"NFS Average: {numpy.mean(nfs_times):.3f} seconds")

if __name__ == "__main__":
    main()