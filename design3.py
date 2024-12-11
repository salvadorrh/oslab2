#!/usr/bin/env python3

import time
import os
import random
import subprocess

def add_network_delay():
    """Add a small network delay to simulate real conditions"""
    subprocess.run(['sudo', 'tc', 'qdisc', 'add', 'dev', 'eth0', 'root', 'netem', 'delay', '50ms'])

def remove_network_delay():
    """Remove the network delay"""
    subprocess.run(['sudo', 'tc', 'qdisc', 'del', 'dev', 'eth0', 'root'])

def read_random_chunks(filepath, chunk_size=1024*1024, num_chunks=50):
    """Read random chunks from the file"""
    file_size = os.path.getsize(filepath)
    total_time = 0
    
    with open(filepath, 'rb') as f:
        for _ in range(num_chunks):
            pos = random.randint(0, max(0, file_size - chunk_size))
            start_time = time.time()
            f.seek(pos)
            f.read(chunk_size)
            total_time += time.time() - start_time
    
    return total_time

def run_test(filepath, iterations=5):
    results = []
    print(f"\nTesting file: {filepath}")
    print("=" * 50)
    
    # Initial read to cache
    print("Initial complete read to cache...")
    with open(filepath, 'rb') as f:
        f.read()
    
    for i in range(iterations):
        time_taken = read_random_chunks(filepath)
        results.append(time_taken)
        print(f"Random access test {i+1}: {time_taken:.3f} seconds")
    
    return results

def main():
    fuse_path = '/users/salvador/netfs_mount/testfile3'
    nfs_path = '/users/salvador/nfs_testfile3'
    
    print("Adding network delay to simulate real conditions...")
    add_network_delay()
    
    print("\nTesting FUSE filesystem...")
    fuse_times = run_test(fuse_path)
    
    print("\nTesting NFS filesystem...")
    nfs_times = run_test(nfs_path)
    
    print("\nRemoving network delay...")
    remove_network_delay()
    
    print("\nResults Summary")
    print("=" * 50)
    print(f"FUSE Average: {sum(fuse_times)/len(fuse_times):.3f} seconds")
    print(f"NFS Average: {sum(nfs_times)/len(nfs_times):.3f} seconds")

if __name__ == "__main__":
    main()