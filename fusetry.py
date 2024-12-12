#!/usr/bin/env python3

import os
import sys
import errno
import stat
from fuse import FUSE, FuseOSError, Operations
import subprocess
from pathlib import Path
import logging
import time
import pwd

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NetworkedFS(Operations):
    def __init__(self, remote_host, remote_path, ssh_port=22):
        # Initialize basic filesystem settings
        self.remote_host = remote_host
        self.remote_path = os.path.abspath(remote_path)
        self.ssh_port = ssh_port
        self.cache_dir = '/tmp/netfs_cache'
        
        # Track open files and their modifications
        self.open_files = {}
        self.modified_files = set()
        
        # Set up SSH authentication using the user's key
        sudo_user = os.environ.get('SUDO_USER', os.environ.get('USER'))
        user_info = pwd.getpwnam(sudo_user)
        self.user_home = user_info.pw_dir
        self.identity_file = os.path.join(self.user_home, '.ssh/id_rsa')
        
        # Create cache directory
        Path(self.cache_dir).mkdir(exist_ok=True)
        
        # Log initialization details
        logger.info(f"Initialized NetworkedFS with:")
        logger.info(f"  Remote Host: {remote_host}")
        logger.info(f"  Remote Path: {self.remote_path}")
        logger.info(f"  SSH Port: {ssh_port}")
        logger.info(f"  Cache Dir: {self.cache_dir}")
        logger.info(f"  Using identity file: {self.identity_file}")
        
        self._verify_remote_setup()

    def _fetch_file(self, path):
        """Fetch file from remote server to cache"""
        remote_path = self._get_remote_path(path)
        cache_path = os.path.join(self.cache_dir, path.lstrip('/'))
        
        # Create cache directory structure if needed
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        try:
            cmd = [
                'scp',
                '-P', str(self.ssh_port),
                '-i', self.identity_file,
                f'{self.remote_host}:{remote_path}',
                cache_path
            ]
            logger.debug(f"Fetching file: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            logger.info(f"Successfully fetched '{path}' to cache")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to fetch '{path}': {e}")
            return False
        
    def _check_remote_dir_exists(self, path):
        """Check if a directory exists on the remote server"""
        remote_path = self._get_remote_path(path)
        cmd = f"test -d '{remote_path}' && echo 'exists'"
        result = self._run_ssh_command(cmd)
        exists = result == 'exists'
        logger.debug(f"Remote directory check: path='{remote_path}' exists={exists}")
        return exists

    def create(self, path, mode, fi=None):
        """Create a new file"""
        logger.debug(f"create called for path: {path}")
        cache_path = os.path.join(self.cache_dir, path.lstrip('/'))
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        # Create the file locally
        open(cache_path, 'a').close()
        os.chmod(cache_path, mode)
        
        # Track this as a modified file
        self.modified_files.add(path)
        
        return 0

    def open(self, path, flags):
        """Open a file and return a file handle"""
        logger.debug(f"open called for path: {path}")
        cache_path = os.path.join(self.cache_dir, path.lstrip('/'))
        
        # If file doesn't exist in cache, fetch it
        if not os.path.exists(cache_path) and self._check_remote_file_exists(path):
            self._fetch_file(path)
        
        # Generate a unique file handle
        fh = len(self.open_files)
        self.open_files[fh] = {'path': path, 'flags': flags}
        
        return fh

    def write(self, path, data, offset, fh):
        """Write data to a file"""
        logger.debug(f"write called for path: {path}, offset: {offset}, length: {len(data)}")
        cache_path = os.path.join(self.cache_dir, path.lstrip('/'))
        
        # Make sure the cache directory exists
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        # Write the data to the cached file
        with open(cache_path, 'rb+') as f:
            f.seek(offset)
            f.write(data)
        
        # Mark the file as modified
        self.modified_files.add(path)
        
        return len(data)

    def release(self, path, fh):
        """Called when a file is closed"""
        logger.debug(f"release called for path: {path}")
        
        # If the file was modified, sync it back to the remote server
        if path in self.modified_files:
            self._sync_to_remote(path)
            self.modified_files.remove(path)
        
        # Clean up our file handle tracking
        if fh in self.open_files:
            del self.open_files[fh]
        
        return 0

    def _sync_to_remote(self, path):
        """Sync a modified file back to the remote server"""
        logger.debug(f"Syncing {path} back to remote server")
        cache_path = os.path.join(self.cache_dir, path.lstrip('/'))
        remote_path = self._get_remote_path(path)
        
        if os.path.exists(cache_path):
            try:
                cmd = [
                    'scp',
                    '-P', str(self.ssh_port),
                    '-i', self.identity_file,
                    cache_path,
                    f'{self.remote_host}:{remote_path}'
                ]
                logger.debug(f"Running sync command: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                logger.info(f"Successfully synced {path} to remote server")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to sync {path} to remote: {e}")
                return False
        return False

    def truncate(self, path, length, fh=None):
        """Truncate a file to a specified length"""
        logger.debug(f"truncate called for path: {path}, length: {length}")
        cache_path = os.path.join(self.cache_dir, path.lstrip('/'))
        
        # If file doesn't exist in cache but exists remotely, fetch it
        if not os.path.exists(cache_path) and self._check_remote_file_exists(path):
            self._fetch_file(path)
        
        # Truncate the cached file
        with open(cache_path, 'r+b') as f:
            f.truncate(length)
        
        # Mark the file as modified
        self.modified_files.add(path)
        
        return 0
    
    def _run_ssh_command(self, command):
        """Run a command over SSH with proper authentication"""
        full_command = [
            'ssh',
            '-p', str(self.ssh_port),
            '-i', self.identity_file,
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no',
            self.remote_host,
            command
        ]
        logger.debug(f"Running SSH command: {' '.join(full_command)}")
        try:
            result = subprocess.run(full_command, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"SSH command failed: {result.stderr}")
                return None
        except subprocess.CalledProcessError as e:
            logger.error(f"SSH command error: {e}")
            return None

    def _get_remote_file_size(self, remote_path):
        """Get file size using ls -l instead of stat"""
        cmd = f"ls -l '{remote_path}' | awk '{{print $5}}'"
        size_str = self._run_ssh_command(cmd)
        try:
            return int(size_str) if size_str else 0
        except (ValueError, TypeError):
            logger.error(f"Could not get size for {remote_path}")
            return 0

    def _verify_remote_setup(self):
        """Verify remote directory exists and is accessible"""
        test_cmd = f"test -d '{self.remote_path}' && echo 'Directory exists'"
        result = self._run_ssh_command(test_cmd)
        
        if result != 'Directory exists':
            logger.error(f"Remote directory {self.remote_path} is not accessible")
            raise RuntimeError("Could not access remote directory")
        
        ls_cmd = f"ls -la '{self.remote_path}'"
        listing = self._run_ssh_command(ls_cmd)
        if listing:
            logger.info("Remote directory contents:")
            logger.info(listing)
        else:
            raise RuntimeError("Could not list remote directory")

    def getattr(self, path, fh=None):
        """Get file attributes"""
        logger.debug(f"getattr called for path: {path}")
        
        # Handle root directory
        if path == '/':
            return {
                'st_mode': (stat.S_IFDIR | 0o755),
                'st_nlink': 2,
                'st_size': 4096,
                'st_ctime': time.time(),
                'st_mtime': time.time(),
                'st_atime': time.time(),
                'st_uid': os.getuid(),
                'st_gid': os.getgid()
            }

        # Check if it's a directory
        if self._check_remote_dir_exists(path):
            return {
                'st_mode': (stat.S_IFDIR | 0o755),
                'st_nlink': 2,
                'st_size': 4096,
                'st_ctime': time.time(),
                'st_mtime': time.time(),
                'st_atime': time.time(),
                'st_uid': os.getuid(),
                'st_gid': os.getgid()
            }

        # Check if it's a regular file
        if self._check_remote_file_exists(path):
            remote_path = self._get_remote_path(path)
            size = self._get_remote_file_size(remote_path)
            
            return {
                'st_mode': (stat.S_IFREG | 0o644),
                'st_nlink': 1,
                'st_size': size,
                'st_ctime': time.time(),
                'st_mtime': time.time(),
                'st_atime': time.time(),
                'st_uid': os.getuid(),
                'st_gid': os.getgid()
            }

        raise FuseOSError(errno.ENOENT)

    def _check_remote_file_exists(self, path):
        """Check if a file exists on the remote server"""
        remote_path = self._get_remote_path(path)
        cmd = f"test -f '{remote_path}' && echo 'exists'"
        result = self._run_ssh_command(cmd)
        exists = result == 'exists'
        logger.debug(f"Remote file check: path='{remote_path}' exists={exists}")
        return exists

    def read(self, path, size, offset, fh):
        """Read data from file"""
        logger.debug(f"read called for path: {path}")
        remote_path = self._get_remote_path(path)
        cache_path = os.path.join(self.cache_dir, path.lstrip('/'))
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        # Fetch file if not in cache
        if not os.path.exists(cache_path):
            scp_cmd = [
                'scp',
                '-P', str(self.ssh_port),
                '-i', self.identity_file,
                f'{self.remote_host}:{remote_path}',
                cache_path
            ]
            logger.debug(f"Fetching file: {' '.join(scp_cmd)}")
            try:
                subprocess.run(scp_cmd, check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to fetch file: {e}")
                raise FuseOSError(errno.EIO)
        
        with open(cache_path, 'rb') as f:
            f.seek(offset)
            return f.read(size)

    def readdir(self, path, fh):
        """List directory contents"""
        logger.debug(f"readdir called for path: {path}")
        dirents = ['.', '..']
        
        remote_path = self._get_remote_path(path)
        # Use -1a to get a simple listing including hidden files
        ls_cmd = f"ls -1a '{remote_path}'"
        result = self._run_ssh_command(ls_cmd)
        
        if result:
            entries = result.split('\n')
            for entry in entries:
                entry = entry.strip()
                if entry and entry not in ['.', '..']:
                    dirents.append(entry)
        
        logger.debug(f"Directory entries for {path}: {dirents}")
        return dirents

    def _get_remote_path(self, path):
        """Convert local path to remote path"""
        clean_path = path.lstrip('/')
        remote_path = os.path.join(self.remote_path, clean_path)
        logger.debug(f"Path translation: local='{path}' → remote='{remote_path}'")
        return remote_path

def main(remote_host, remote_path, mount_point, ssh_port=22):
    FUSE(NetworkedFS(remote_host, remote_path, ssh_port), mount_point, nothreads=True, foreground=True)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(f'Usage: {sys.argv[0]} <remote_host> <remote_path> <mount_point> [ssh_port]')
        sys.exit(1)
    
    remote_host = sys.argv[1]
    remote_path = sys.argv[2]
    mount_point = sys.argv[3]
    ssh_port = int(sys.argv[4]) if len(sys.argv) > 4 else 22
    
    main(remote_host, remote_path, mount_point, ssh_port)