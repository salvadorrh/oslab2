#!/usr/bin/env python3

import time
import os
import random

def scan_file_contents(filepath, pattern_size=1024):
    """Simulate searching through a file for specific patterns"""
    total_time = 0
    num_searches = 10  # Number of pattern searches to perform
    
    with open(filepath, 'rb') as f:
        file_content = f.read()  # Read entire file once
        file_size = len(file_content)
        
        # Simulate multiple pattern searches through the file
        for _ in range(num_searches):
            start_time = time.time()
            # Simulate pattern matching by reading chunks throughout the file
            for pos in range(0, file_size - pattern_size, pattern_size):
                chunk = file_content[pos:pos + pattern_size]
                # Do something with the chunk to prevent optimization
                _ = sum(chunk)
            total_time += time.time() - start_time
            
    return total_time

def run_pattern_search_test(filepath):
    """Run multiple pattern searches on the same file"""
    print(f"\nTesting pattern search for: {filepath}")
    print("=" * 50)
    
    # First do one scan to ensure file is cached
    print("Initial scan (caching)...")
    first_time = scan_file_contents(filepath)
    print(f"First scan: {first_time:.3f} seconds")
    
    # Now do rapid repeated scans
    times = []
    num_scans = 3
    print("\nPerforming repeated scans...")
    for i in range(num_scans):
        time_taken = scan_file_contents(filepath)
        times.append(time_taken)
        print(f"Scan {i+1}: {time_taken:.3f} seconds")
    
    return times

def main():
    print("Starting Pattern Search Performance Test")
    print("Testing repeated full-file pattern searching")
    
    # Use smaller files (10MB) for this test
    fuse_path = '/users/salvador/netfs_mount/searchfile'
    nfs_path = '/users/salvador/searchfile'
    
    print("\nTesting FUSE filesystem...")
    fuse_times = run_pattern_search_test(fuse_path)
    
    print("\nTesting NFS filesystem...")
    nfs_times = run_pattern_search_test(nfs_path)
    
    print("\nResults Summary")
    print("=" * 50)
    avg_fuse = sum(fuse_times) / len(fuse_times)
    avg_nfs = sum(nfs_times) / len(nfs_times)
    print(f"FUSE Average Search Time: {avg_fuse:.3f} seconds")
    print(f"NFS Average Search Time: {avg_nfs:.3f} seconds")

if __name__ == "__main__":
    main()