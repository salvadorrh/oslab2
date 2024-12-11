from fuse import FUSE, Operations
import os
import subprocess

class NetworkFileSystem(Operations):
    def __init__(self, remote_server):
        self.remote_server = remote_server
        self.cache_dir = "/tmp"

    def getattr(self, path, fh=None):
        local_path = os.path.join(self.cache_dir, path.lstrip("/"))
        st = os.lstat(local_path)
        return {key: getattr(st, key) for key in ('st_mode', 'st_size', 'st_atime', 'st_mtime', 'st_ctime')}

    def open(self, path, flags):
        remote_path = f"{self.remote_server}:{path.lstrip('/')}"
        local_path = os.path.join(self.cache_dir, path.lstrip("/"))
        if not os.path.exists(local_path):
            subprocess.run(['scp', remote_path, local_path])
        return os.open(local_path, flags)

    def read(self, path, size, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, size)

    def write(self, path, data, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, data)

    def flush(self, path, fh):
        remote_path = f"{self.remote_server}:{path.lstrip('/')}"
        local_path = os.path.join(self.cache_dir, path.lstrip("/"))
        subprocess.run(['scp', local_path, remote_path])

if __name__ == '__main__':
    import sys
    remote_server = sys.argv[1]
    mountpoint = sys.argv[2]
    FUSE(NetworkFileSystem(remote_server), mountpoint, nothreads=True, foreground=True)
