"""
Service statistics management
"""

from datetime import datetime, timezone
from pathlib import Path


class Stats:
    """Class for storing service statistics"""

    def __init__(self):
        self.total_processed = 0
        self.today_processed = 0
        self.failed = 0
        self.last_reset = datetime.now(timezone.utc).date()

    def increment_processed(self):
        """Increments the counter for successfully processed files"""
        self._check_date_reset()
        self.total_processed += 1
        self.today_processed += 1

    def increment_failed(self):
        """Increments the counter for failed files"""
        self._check_date_reset()
        self.failed += 1

    def _check_date_reset(self):
        """Resets daily statistics if the date has changed"""
        today = datetime.now(timezone.utc).date()
        if today != self.last_reset:
            self.today_processed = 0
            self.last_reset = today

    def get_success_rate(self):
        """
        Calculates the percentage of successfully processed files

        Returns:
            float: Success rate (0–100)
        """
        total = self.total_processed + self.failed
        if total == 0:
            return 100.0
        return round((self.total_processed / total) * 100, 1)

    def get_pending_count(self, config):
        """
        Counts the number of pending files in the watch directory

        Args:
            config (dict): Application configuration

        Returns:
            int: Number of pending files
        """
        watched_dir = Path(config['watcher']['watch_directory'])
        if not watched_dir.exists():
            return 0

        ignored_patterns = {'.gitkeep', '.gitignore', '.DS_Store', 'Thumbs.db'}
        pending_count = sum(
            1 for f in watched_dir.glob('*')
            if f.is_file() and f.name not in ignored_patterns
        ) if watched_dir.exists() else 0

        return pending_count  # len(list(watched_dir.glob('*')))

    def to_dict(self, config=None):
        """
        Returns statistics as a dictionary

        Args:
            config (dict, optional): Configuration for calculating pending files

        Returns:
            dict: Statistics
        """
        result = {
            'total_processed': self.total_processed,
            'today_processed': self.today_processed,
            'failed': self.failed,
            'success_rate': self.get_success_rate()
        }

        if config:
            result['pending_files'] = self.get_pending_count(config)

        return result


# Global instance of Stats
stats = Stats()
