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

def run_benchmark(filepath, iterations=5):
    """Run multiple iterations of reading a file and collect timing data."""
    results = []
    print(f"\nTesting file: {filepath}")
    print("=" * 50)
    
    for i in range(iterations):
        # For more accurate measurements
        os.system("sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'")
        
        time_taken = read_file_with_timing(filepath)
        results.append(time_taken)
        print(f"Iteration {i+1}: {time_taken:.3f} seconds")
    
    return results

def main():
    # Configuration
    iterations = 5
    fuse_path = '/users/salvador/netfs_mount/testfile'
    nfs_path = '/users/salvador/nfs_testfile'

if __name__ == "__main__":
    main()