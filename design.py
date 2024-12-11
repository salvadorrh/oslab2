#!/usr/bin/env python3

import time
import os
import matplotlib.pyplot as plt
import numpy as np

def read_file_with_timing(filepath):
    """Read a file completely and return the time taken in seconds."""
    start_time = time.time()
    with open(filepath, 'rb') as f:
        # Read the entire file in chunks to handle large files efficiently
        chunk_size = 1024 * 1024  # 1MB chunks
        while f.read(chunk_size):
            pass
    end_time = time.time()
    return end_time - start_time