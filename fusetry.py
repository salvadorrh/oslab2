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
        self.remote_path = remote_path
        self.ssh_port = ssh_port
        self.cache_dir = '/tmp/netfs_cache'
        Path(self.cache_dir).mkdir(exist_ok=True)
        logger.info(f"Initialized NetworkedFS with remote_host={remote_host}, remote_path={remote_path}, port={ssh_port}")
        
    def _get_remote_path(self, path):
        """Convert local path to remote path"""
        # Remove leading slash and join with remote path
        clean_path = path.lstrip('/')
        remote_path = os.path.join(self.remote_path, clean_path)
        logger.debug(f"Converted local path '{path}' to remote path '{remote_path}'")
        return remote_path
        
    def _get_cache_path(self, path):
        """Get the local cache path for a file"""
        clean_path = path.lstrip('/')
        cache_path = os.path.join(self.cache_dir, clean_path)
        logger.debug(f"Cache path for '{path}' is '{cache_path}'")
        return cache_path

    def _check_remote_file_exists(self, path):
        """Check if a file exists on the remote server"""
        remote_path = self._get_remote_path(path)
        cmd = [
            'ssh',
            '-p', str(self.ssh_port),
            self.remote_host,
            f'test -f "{remote_path}" && echo "exists"'
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            exists = result.stdout.strip() == "exists"
            logger.debug(f"Remote file check for '{path}': {'exists' if exists else 'does not exist'}")
            return exists
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking remote file: {e}")
            return False

    def _fetch_file(self, path):
        """Fetch file from remote server to cache"""
        if not self._check_remote_file_exists(path):
            logger.error(f"Remote file '{path}' does not exist")
            return False

        remote_path = self._get_remote_path(path)
        cache_path = self._get_cache_path(path)
        
        # Create cache directory structure if needed
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        try:
            cmd = [
                'scp',
                '-P', str(self.ssh_port),
                f'{self.remote_host}:{remote_path}',
                cache_path
            ]
            logger.debug(f"Fetching file with command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            logger.info(f"Successfully fetched '{path}' to cache")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to fetch '{path}': {e}")
            return False

    def getattr(self, path, fh=None):
        """Get file attributes"""
        logger.debug(f"getattr called for path: {path}")
        
        # Special case for root directory
        if path == '/':
            st = os.stat(self.cache_dir)
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                       'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

        # Check if file exists in cache, if not try to fetch it
        cache_path = self._get_cache_path(path)
        if not os.path.exists(cache_path):
            if self._check_remote_file_exists(path):
                self._fetch_file(path)
            else:
                raise FuseOSError(errno.ENOENT)

        if os.path.exists(cache_path):
            st = os.lstat(cache_path)
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                       'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        
        raise FuseOSError(errno.ENOENT)

    def read(self, path, size, offset, fh):
        """Read data from file"""
        logger.debug(f"read called for path: {path}, size: {size}, offset: {offset}")
        cache_path = self._get_cache_path(path)
        
        if not os.path.exists(cache_path):
            if not self._fetch_file(path):
                raise FuseOSError(errno.ENOENT)
        
        with open(cache_path, 'rb') as f:
            f.seek(offset)
            return f.read(size)

    def readdir(self, path, fh):
        """List directory contents"""
        logger.debug(f"readdir called for path: {path}")
        remote_path = self._get_remote_path(path)
        
        # Basic directory entries that should always be present
        dirents = ['.', '..']
        
        # Get remote directory listing
        cmd = [
            'ssh',
            '-p', str(self.ssh_port),
            self.remote_host,
            f'ls -1 "{remote_path}"'
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                dirents.extend(result.stdout.splitlines())
        except subprocess.CalledProcessError as e:
            logger.error(f"Error listing remote directory: {e}")
        
        return dirents

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