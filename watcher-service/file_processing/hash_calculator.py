"""
Calculating file hashes
"""

import hashlib
import logging

logger = logging.getLogger(__name__)

import hashlib
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_file_hash(filepath, algorithm='sha256', max_retries=3, retry_delay=0.5):
    """
    Calculates the file hash with retry logic

    Args:
        filepath (str|Path): Path to the file
        algorithm (str): Hashing algorithm (sha256, md5, sha1)
        max_retries (int): Maximum number of retry attempts
        retry_delay (float): Delay between retries in seconds

    Returns:
        str: File hash in hexadecimal format, or None in case of an error
    """
    for attempt in range(max_retries):
        try:
            # Selecting an algorithm
            if algorithm == 'sha256':
                hash_obj = hashlib.sha256()
            elif algorithm == 'md5':
                hash_obj = hashlib.md5()
            elif algorithm == 'sha1':
                hash_obj = hashlib.sha1()
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")

            # Reading the file in blocks to save memory
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    hash_obj.update(byte_block)

            # Success - return hash
            if attempt > 0:
                logger.info(f"Successfully calculated hash for {filepath} on attempt {attempt + 1}")

            return hash_obj.hexdigest()

        except PermissionError as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Permission denied for {filepath}, "
                    f"retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
            else:
                logger.error(
                    f"Failed to calculate hash for {filepath} after {max_retries} attempts: "
                    f"Permission denied (file may be locked by another process)"
                )
                return None

        except Exception as e:
            logger.error(f"Failed to calculate hash for {filepath}: {e}")
            return None

    return None
