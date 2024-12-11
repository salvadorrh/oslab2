#!/usr/bin/env python3

import time
import os
import multiprocessing
import numpy as np

def process_file_segment(args):
    """Simulate complex processing on a file segment"""
    filepath, start_pos, size = args
    total = 0
    with open(filepath, 'rb') as f:
        f.seek(start_pos)
        data = f.read(size)
        # Perform some actual computation to prevent optimization
        total = sum(data)
    return total

def run_concurrent_test(filepath, num_processes=4, chunk_size=1024*1024):
    """Test concurrent access to the same file from multiple processes"""
    file_size = os.path.getsize(filepath)
    
    # Create segments for each process to work on
    segments = []
    for i in range(num_processes):
        start = (i * file_size) // num_processes
        end = ((i + 1) * file_size) // num_processes
        size = end - start
        segments.append((filepath, start, size))
    
    # Time the concurrent processing
    start_time = time.time()
    
    # Use process pool to run concurrent operations
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(process_file_segment, segments)
    
    end_time = time.time()
    return end_time - start_time

def main():
    print("Starting Concurrent Access Performance Test")
    iterations = 3
    num_processes = 8  # Number of concurrent processes
    
    fuse_path = '/users/salvador/netfs_mount/concurrent_file'
    nfs_path = '/users/salvador/concurrent_file'
    
    print("\nRunning concurrent access tests...")
    print("Using 8 concurrent processes to simulate heavy load")
    
    fuse_times = []
    nfs_times = []
    
    for i in range(iterations):
        print(f"\nIteration {i+1}/{iterations}")
        print("-" * 50)
        
        print("Testing FUSE filesystem...")
        fuse_time = run_concurrent_test(fuse_path, num_processes)
        fuse_times.append(fuse_time)
        print(f"FUSE Time: {fuse_time:.3f} seconds")
        
        print("\nTesting NFS filesystem...")
        nfs_time = run_concurrent_test(nfs_path, num_processes)
        nfs_times.append(nfs_time)
        print(f"NFS Time: {nfs_time:.3f} seconds")
        
        # Small delay between iterations
        time.sleep(1)
    
    print("\nResults Summary")
    print("=" * 50)
    print(f"FUSE Average: {np.mean(fuse_times):.3f} seconds (stddev: {np.std(fuse_times):.3f})")
    print(f"NFS Average: {np.mean(nfs_times):.3f} seconds (stddev: {np.std(nfs_times):.3f})")

if __name__ == "__main__":
    main()