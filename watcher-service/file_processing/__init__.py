"""
File processing
"""

from .hash_calculator import calculate_file_hash
from .metadata import extract_metadata, validate_metadata
from .file_mover import move_file_to_processed, copy_file_to_processed

__all__ = [
    'calculate_file_hash',
    'extract_metadata',
    'validate_metadata',
    'move_file_to_processed',
    'copy_file_to_processed'
]