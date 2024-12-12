#!/usr/bin/env python3

import os
import time

def read_all_files(directory, max_files=50):  # Limit to 50 files for testing
    """Read all files in the directory and return total time taken"""
    start_time = time.time()
    total_bytes = 0
    files_read = 0
    
    # Get list of files first
    try:
        all_files = sorted(os.listdir(directory))[:max_files]  # Limit number of files
        
        for filename in all_files:
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                with open(filepath, 'rb') as f:
                    data = f.read()
                    total_bytes += len(data)
                    files_read += 1
                    print(f"Read file: {filename}")  # Add progress indicator
    except Exception as e:
        print(f"Error reading directory {directory}: {e}")
    
    end_time = time.time()
    return end_time - start_time, total_bytes, files_read

def main():
    num_trials = 3
    
    # Define the paths
    fuse_dir = '/users/salvador/netfs_mount/small_files'
    nfs_dir = '/users/salvador/small_files'
    
    print("Starting small files read test")
    print("=" * 60)
    
    # Store results
    nfs_times = []
    fuse_times = []
    
    print("\nRunning read trials...")
    for trial in range(num_trials):
        print(f"\nTrial {trial + 1}/{num_trials}")
        print("-" * 40)
        
        print("Testing NFS...")
        nfs_time, nfs_bytes, nfs_count = read_all_files(nfs_dir)
        nfs_times.append(nfs_time)
        print(f"NFS Time: {nfs_time:.3f} seconds")
        print(f"Files read: {nfs_count}")
        
        print("\nTesting FUSE...")
        fuse_time, fuse_bytes, fuse_count = read_all_files(fuse_dir)
        fuse_times.append(fuse_time)
        print(f"FUSE Time: {fuse_time:.3f} seconds")
        print(f"Files read: {fuse_count}")
    
    # Show results
    print("\nFinal Results")
    print("=" * 60)
    print(f"Average NFS Time: {sum(nfs_times)/len(nfs_times):.3f} seconds")
    print(f"Average FUSE Time: {sum(fuse_times)/len(fuse_times):.3f} seconds")
    print(f"Files processed: {fuse_count}")

if __name__ == "__main__":
    main()