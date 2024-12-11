#!/usr/bin/env python3

import os
import sys
import errno
import stat
from fuse import FUSE, FuseOSError, Operations
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NetworkedFS(Operations):
    def __init__(self, remote_host, remote_path, ssh_port=22):
        self.remote_host = remote_host
        # Ensure remote_path is absolute and clean
        self.remote_path = os.path.abspath(remote_path)
        self.ssh_port = ssh_port
        self.cache_dir = '/tmp/netfs_cache'
        Path(self.cache_dir).mkdir(exist_ok=True)
        logger.info(f"Initialized NetworkedFS with:")
        logger.info(f"  Remote Host: {remote_host}")
        logger.info(f"  Remote Path: {self.remote_path}")
        logger.info(f"  SSH Port: {ssh_port}")
        logger.info(f"  Cache Dir: {self.cache_dir}")
        
        # Verify remote directory exists
        self._verify_remote_setup()

    def _verify_remote_setup(self):
        """Verify remote directory exists and is accessible"""
        cmd = [
            'ssh',
            '-p', str(self.ssh_port),
            self.remote_host,
            f'ls -ld "{self.remote_path}"'
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            logger.info(f"Remote directory check result: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to verify remote directory: {e}")
            raise RuntimeError("Could not access remote directory")

    def _get_remote_path(self, path):
        """Convert local path to remote path"""
        # Remove leading slash and join with remote path
        clean_path = path.lstrip('/')
        remote_path = os.path.join(self.remote_path, clean_path)
        logger.debug(f"Path translation: local='{path}' → remote='{remote_path}'")
        return remote_path

    def _list_remote_dir(self, path):
        """List contents of remote directory"""
        remote_path = self._get_remote_path(path)
        cmd = [
            'ssh',
            '-p', str(self.ssh_port),
            self.remote_host,
            f'ls -la "{remote_path}"'
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            logger.debug(f"Remote directory listing for {remote_path}:")
            logger.debug(result.stdout)
            return result.stdout.splitlines()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list remote directory: {e}")
            return []

    def _check_remote_file_exists(self, path):
        """Check if a file exists on the remote server"""
        remote_path = self._get_remote_path(path)
        cmd = [
            'ssh',
            '-p', str(self.ssh_port),
            self.remote_host,
            f'test -f "{remote_path}" && echo "exists" || echo "not found"'
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            exists = "exists" in result.stdout
            logger.debug(f"Remote file check: path='{remote_path}' exists={exists}")
            return exists
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking remote file: {e}")
            return False

    def getattr(self, path, fh=None):
        """Get file attributes"""
        logger.debug(f"getattr called for path: {path}")
        
        # Special case for root directory
        if path == '/':
            mode = stat.S_IFDIR | 0o755
            return {
                'st_mode': mode,
                'st_nlink': 2,
                'st_size': 4096,
                'st_ctime': os.path.getctime(self.cache_dir),
                'st_mtime': os.path.getmtime(self.cache_dir),
                'st_atime': os.path.getatime(self.cache_dir),
                'st_uid': os.getuid(),
                'st_gid': os.getgid()
            }

        # Check if file exists remotely
        if self._check_remote_file_exists(path):
            mode = stat.S_IFREG | 0o644
            remote_path = self._get_remote_path(path)
            # Get file size from remote
            try:
                cmd = ['ssh', '-p', str(self.ssh_port), self.remote_host, f'stat -f %z "{remote_path}"']
                result = subprocess.run(cmd, capture_output=True, text=True)
                size = int(result.stdout.strip())
            except:
                size = 0
                
            return {
                'st_mode': mode,
                'st_nlink': 1,
                'st_size': size,
                'st_ctime': os.time(),
                'st_mtime': os.time(),
                'st_atime': os.time(),
                'st_uid': os.getuid(),
                'st_gid': os.getgid()
            }

        raise FuseOSError(errno.ENOENT)

    def readdir(self, path, fh):
        """List directory contents"""
        logger.debug(f"readdir called for path: {path}")
        dirents = ['.', '..']
        
        # Get remote directory listing
        remote_entries = self._list_remote_dir(path)
        for line in remote_entries[1:]:  # Skip total line
            if line.strip():
                parts = line.split()
                if len(parts) >= 9:
                    name = ' '.join(parts[8:])
                    if name not in ['.', '..']:
                        dirents.append(name)
        
        logger.debug(f"Directory entries: {dirents}")
        return dirents

    def read(self, path, size, offset, fh):
        """Read data from file"""
        logger.debug(f"read called for path: {path}, size: {size}, offset: {offset}")
        remote_path = self._get_remote_path(path)
        cache_path = os.path.join(self.cache_dir, path.lstrip('/'))
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        # Fetch file if not in cache
        if not os.path.exists(cache_path):
            cmd = [
                'scp',
                '-P', str(self.ssh_port),
                f'{self.remote_host}:{remote_path}',
                cache_path
            ]
            logger.debug(f"Fetching file: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
        
        # Read from cache
        with open(cache_path, 'rb') as f:
            f.seek(offset)
            return f.read(size)

    def getxattr(self, path, name, position=0):
        """Handle extended attributes - return ENODATA for any request"""
        return ''

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