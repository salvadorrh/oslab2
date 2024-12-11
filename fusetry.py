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
        self.remote_host = remote_host
        self.remote_path = os.path.abspath(remote_path)
        self.ssh_port = ssh_port
        self.cache_dir = '/tmp/netfs_cache'
        
        # Get the original user's home directory and SSH key
        sudo_user = os.environ.get('SUDO_USER', os.environ.get('USER'))
        user_info = pwd.getpwnam(sudo_user)
        self.user_home = user_info.pw_dir
        self.identity_file = os.path.join(self.user_home, '.ssh/id_rsa')
        
        Path(self.cache_dir).mkdir(exist_ok=True)
        logger.info(f"Initialized NetworkedFS with:")
        logger.info(f"  Remote Host: {remote_host}")
        logger.info(f"  Remote Path: {self.remote_path}")
        logger.info(f"  SSH Port: {ssh_port}")
        logger.info(f"  Cache Dir: {self.cache_dir}")
        logger.info(f"  Using identity file: {self.identity_file}")
        
        self._verify_remote_setup()

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

    def getxattr(self, path, name, position=0):
        """Handle extended attributes"""
        return bytes()  # Return empty bytes instead of empty string

    def _check_remote_file_exists(self, path):
        """Check if a file exists on the remote server"""
        remote_path = self._get_remote_path(path)
        cmd = f"test -f '{remote_path}' && echo 'exists'"
        result = self._run_ssh_command(cmd)
        exists = result == 'exists'
        logger.debug(f"Remote file check: path='{remote_path}' exists={exists}")
        return exists

    def getattr(self, path, fh=None):
        """Get file attributes"""
        logger.debug(f"getattr called for path: {path}")
        
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

        if self._check_remote_file_exists(path):
            remote_path = self._get_remote_path(path)
            # Get file size
            size_cmd = f"stat -f %z '{remote_path}' || stat --format=%s '{remote_path}'"
            size_str = self._run_ssh_command(size_cmd)
            size = int(size_str) if size_str else 0

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

    def _get_remote_path(self, path):
        """Convert local path to remote path"""
        clean_path = path.lstrip('/')
        remote_path = os.path.join(self.remote_path, clean_path)
        logger.debug(f"Path translation: local='{path}' → remote='{remote_path}'")
        return remote_path

    def readdir(self, path, fh):
        """List directory contents"""
        logger.debug(f"readdir called for path: {path}")
        dirents = ['.', '..']
        
        remote_path = self._get_remote_path(path)
        ls_cmd = f"ls -1a '{remote_path}'"
        result = self._run_ssh_command(ls_cmd)
        
        if result:
            entries = result.split('\n')
            for entry in entries:
                if entry and entry not in ['.', '..']:
                    dirents.append(entry)
        
        logger.debug(f"Directory entries: {dirents}")
        return dirents

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