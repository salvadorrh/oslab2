#!/usr/bin/env python3

import os
import sys
import errno
import stat
import time
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
        
    def _get_remote_path(self, path):
        """Convert local path to remote path"""
        return os.path.join(self.remote_path, path.lstrip('/'))
        
    def _get_cache_path(self, path):
        """Get the local cache path for a file"""
        return os.path.join(self.cache_dir, path.lstrip('/'))
        
    def _fetch_file(self, path):
        """Fetch file from remote server to cache"""
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
            subprocess.run(cmd, check=True)
            logger.debug(f"Fetched {path} to cache")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to fetch {path}: {e}")
            return False
            
    def _push_file(self, path):
        """Push modified file back to remote server"""
        remote_path = self._get_remote_path(path)
        cache_path = self._get_cache_path(path)
        
        try:
            cmd = [
                'scp',
                '-P', str(self.ssh_port),
                cache_path,
                f'{self.remote_host}:{remote_path}'
            ]
            subprocess.run(cmd, check=True)
            logger.debug(f"Pushed {path} to remote")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push {path}: {e}")
            return False

    def getattr(self, path, fh=None):
        """Get file attributes"""
        cache_path = self._get_cache_path(path)
        
        if os.path.exists(cache_path):
            st = os.lstat(cache_path)
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                       'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        
        raise FuseOSError(errno.ENOENT)

    def read(self, path, size, offset, fh):
        """Read data from file"""
        cache_path = self._get_cache_path(path)
        
        if not os.path.exists(cache_path):
            if not self._fetch_file(path):
                raise FuseOSError(errno.ENOENT)
        
        with open(cache_path, 'rb') as f:
            f.seek(offset)
            return f.read(size)

    def write(self, path, data, offset, fh):
        """Write data to file"""
        cache_path = self._get_cache_path(path)
        
        with open(cache_path, 'r+b') as f:
            f.seek(offset)
            f.write(data)
        return len(data)

    def release(self, path, fh):
        """Called when a file is closed - push changes back to remote"""
        cache_path = self._get_cache_path(path)
        if os.path.exists(cache_path):
            self._push_file(path)
        return 0

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