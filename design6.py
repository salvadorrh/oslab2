#!/usr/bin/env python3

import os
import time

def read_all_files(directory):
    """Read all files in the directory and return total time taken"""
    # Keep track of both time and amount of data read
    start_time = time.time()
    total_bytes = 0
    files_read = 0
    
    # Read each file in the directory sequentially
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):  # Make sure we're only reading files, not directories
            with open(filepath, 'rb') as f:
                data = f.read()
                total_bytes += len(data)
                files_read += 1
    
    end_time = time.time()
    return end_time - start_time, total_bytes, files_read

def main():
    # Set up our test parameters
    num_trials = 3  # Number of times to repeat the test for reliable results
    
    # Define the paths where we'll find our test files
    fuse_dir = '/users/salvador/netfs_mount/small_files'
    nfs_dir = '/users/salvador/small_files'
    
    print("Starting small files read test")
    print("=" * 60)
    
    # Store our timing results
    nfs_times = []
    fuse_times = []
    
    print("\nRunning read trials...")
    for trial in range(num_trials):
        print(f"\nTrial {trial + 1}/{num_trials}")
        print("-" * 40)
        
        # Test NFS performance
        print("Testing NFS...")
        nfs_time, nfs_bytes, nfs_count = read_all_files(nfs_dir)
        nfs_times.append(nfs_time)
        print(f"NFS Time: {nfs_time:.3f} seconds")
        print(f"Files read: {nfs_count}")
        
        # Test FUSE performance
        print("\nTesting FUSE...")
        fuse_time, fuse_bytes, fuse_count = read_all_files(fuse_dir)
        fuse_times.append(fuse_time)
        print(f"FUSE Time: {fuse_time:.3f} seconds")
        print(f"Files read: {fuse_count}")
    
    # Calculate and display final results
    print("\nFinal Results")
    print("=" * 60)
    print(f"Average NFS Time: {sum(nfs_times)/len(nfs_times):.3f} seconds")
    print(f"Average FUSE Time: {sum(fuse_times)/len(fuse_times):.3f} seconds")
    print(f"Total data processed: {nfs_bytes/1024/1024:.2f} MB")
    print(f"Total files processed: {nfs_count}")

if __name__ == "__main__":
    main()