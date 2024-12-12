#!/usr/bin/env python3

import os
import time
import shutil
from pathlib import Path

def create_many_small_files(directory, num_files=1000, size_bytes=1024):
    """Create many small files in the specified directory"""
    print(f"Creating {num_files} files of {size_bytes} bytes each...")
    
    # Create a small chunk of data to write to each file
    data = b'x' * size_bytes
    
    for i in range(num_files):
        filepath = os.path.join(directory, f'file_{i:04d}.txt')
        with open(filepath, 'wb') as f:
            f.write(data)
            
def read_all_files(directory):
    """Read all files in the directory and return total time taken"""
    start_time = time.time()
    total_bytes = 0
    
    # Read each file in the directory
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                data = f.read()
                total_bytes += len(data)
    
    end_time = time.time()
    return end_time - start_time, total_bytes

def main():
    # Configuration
    num_files = 1000       # Number of small files to create
    file_size = 1024      # Size of each file in bytes (1KB)
    num_trials = 3        # Number of times to repeat the test
    
    # Test paths
    fuse_dir = '/users/salvador/netfs_mount/small_files'
    nfs_dir = '/users/salvador/small_files'
    
    # Create test directories
    os.makedirs(nfs_dir, exist_ok=True)
    os.makedirs(fuse_dir, exist_ok=True)
    
    print(f"Starting small files test with {num_files} files of {file_size} bytes each")
    print("=" * 60)
    
    # Create test files in both locations
    print("\nCreating test files...")
    create_many_small_files(nfs_dir, num_files, file_size)
    create_many_small_files(fuse_dir, num_files, file_size)
    
    # Run the trials
    nfs_times = []
    fuse_times = []
    
    print("\nRunning read trials...")
    for trial in range(num_trials):
        print(f"\nTrial {trial + 1}/{num_trials}")
        print("-" * 40)
        
        # Test NFS
        print("Testing NFS...")
        nfs_time, nfs_bytes = read_all_files(nfs_dir)
        nfs_times.append(nfs_time)
        print(f"NFS Time: {nfs_time:.3f} seconds")
        
        # Test FUSE
        print("\nTesting FUSE...")
        fuse_time, fuse_bytes = read_all_files(fuse_dir)
        fuse_times.append(fuse_time)
        print(f"FUSE Time: {fuse_time:.3f} seconds")
    
    # Calculate and display results
    print("\nFinal Results")
    print("=" * 60)
    print(f"Average NFS Time: {sum(nfs_times)/len(nfs_times):.3f} seconds")
    print(f"Average FUSE Time: {sum(fuse_times)/len(fuse_times):.3f} seconds")
    print(f"Total data processed: {nfs_bytes/1024/1024:.2f} MB")

if __name__ == "__main__":
    main()