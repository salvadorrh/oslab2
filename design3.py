#!/usr/bin/env python3

import time
import os
import random

def read_file_in_chunks(filepath, chunk_size=1024*1024):
    """Read a file in chunks and return the time taken."""
    start_time = time.time()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
    return time.time() - start_time

def test_repeated_access(filepath, num_reads=5):
    """Test repeated access to the same file."""
    results = []
    print(f"\nTesting repeated access for: {filepath}")
    print("=" * 50)
    
    # First read (might be slower as it loads into cache)
    first_time = read_file_in_chunks(filepath)
    print(f"First read (caching): {first_time:.3f} seconds")
    
    # Immediate repeated reads
    for i in range(num_reads):
        time_taken = read_file_in_chunks(filepath)
        results.append(time_taken)
        print(f"Quick read {i+1}: {time_taken:.3f} seconds")
        # Add a very small delay to prevent overwhelming the system
        time.sleep(0.1)
    
    return results

def main():
    # Use a more reasonable file size (100MB)
    iterations = 5
    fuse_path = '/users/salvador/netfs_mount/testfile4'
    nfs_path = '/users/salvador/nfs_testfile4'
    
    print("Starting Optimized Read Performance Test")
    print("Testing repeated quick reads of the same file")
    
    print("\nTesting FUSE filesystem...")
    fuse_times = test_repeated_access(fuse_path, iterations)
    
    print("\nTesting NFS filesystem...")
    nfs_times = test_repeated_access(nfs_path, iterations)
    
    # Calculate and display results
    print("\nResults Summary")
    print("=" * 50)
    print(f"FUSE Average (excluding first read): {sum(fuse_times)/len(fuse_times):.3f} seconds")
    print(f"NFS Average (excluding first read): {sum(nfs_times)/len(nfs_times):.3f} seconds")

if __name__ == "__main__":
    main()