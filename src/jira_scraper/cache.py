"""Local data caching for Jira data."""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


class DataCache:
    """Handles caching of Jira data to local files."""

    def __init__(self, cache_dir: str = ".jira_cache"):
        """
        Initialize cache handler.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_cache_key(self, project_key: str, data_type: str, label: Optional[str] = None) -> str:
        """
        Generate cache key for given parameters.

        Args:
            project_key: Jira project key
            data_type: Type of data (bugs, test_executions)
            label: Optional label filter

        Returns:
            Cache filename
        """
        key_parts = [project_key, data_type]
        if label:
            key_parts.append(label)

        # Create hash for unique identification
        key_string = "_".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]

        return f"{key_string}_{key_hash}.json"

    def save(
        self,
        project_key: str,
        data_type: str,
        data: List[Dict[str, Any]],
        label: Optional[str] = None
    ) -> str:
        """
        Save data to cache.

        Args:
            project_key: Jira project key
            data_type: Type of data (bugs, test_executions)
            data: Data to cache
            label: Optional label filter

        Returns:
            Path to cache file
        """
        cache_key = self._get_cache_key(project_key, data_type, label)
        cache_path = os.path.join(self.cache_dir, cache_key)

        cache_data = {
            "project_key": project_key,
            "data_type": data_type,
            "label": label,
            "cached_at": datetime.now().isoformat(),
            "count": len(data),
            "data": data
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"✓ Saved {len(data)} {data_type} to cache: {cache_path}")
        return cache_path

    def load(
        self,
        project_key: str,
        data_type: str,
        label: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Load data from cache.

        Args:
            project_key: Jira project key
            data_type: Type of data (bugs, test_executions)
            label: Optional label filter

        Returns:
            Cached data or None if not found
        """
        cache_key = self._get_cache_key(project_key, data_type, label)
        cache_path = os.path.join(self.cache_dir, cache_key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            cached_at = cache_data.get("cached_at", "unknown")
            count = cache_data.get("count", 0)
            print(f"✓ Loaded {count} {data_type} from cache (cached at: {cached_at})")

            return cache_data.get("data", [])

        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ Error loading cache: {e}")
            return None

    def exists(
        self,
        project_key: str,
        data_type: str,
        label: Optional[str] = None
    ) -> bool:
        """
        Check if cache exists for given parameters.

        Args:
            project_key: Jira project key
            data_type: Type of data (bugs, test_executions)
            label: Optional label filter

        Returns:
            True if cache file exists
        """
        cache_key = self._get_cache_key(project_key, data_type, label)
        cache_path = os.path.join(self.cache_dir, cache_key)
        return os.path.exists(cache_path)

    def get_cache_info(
        self,
        project_key: str,
        data_type: str,
        label: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cache metadata without loading full data.

        Args:
            project_key: Jira project key
            data_type: Type of data (bugs, test_executions)
            label: Optional label filter

        Returns:
            Cache metadata or None
        """
        cache_key = self._get_cache_key(project_key, data_type, label)
        cache_path = os.path.join(self.cache_dir, cache_key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            return {
                "project_key": cache_data.get("project_key"),
                "data_type": cache_data.get("data_type"),
                "label": cache_data.get("label"),
                "cached_at": cache_data.get("cached_at"),
                "count": cache_data.get("count"),
                "path": cache_path
            }

        except (json.JSONDecodeError, KeyError):
            return None

    def clear_cache(self, project_key: Optional[str] = None):
        """
        Clear cache files.

        Args:
            project_key: If specified, only clear cache for this project
        """
        if not os.path.exists(self.cache_dir):
            return

        files_removed = 0
        for filename in os.listdir(self.cache_dir):
            if project_key and not filename.startswith(project_key):
                continue

            filepath = os.path.join(self.cache_dir, filename)
            try:
                os.remove(filepath)
                files_removed += 1
            except OSError as e:
                print(f"Error removing {filepath}: {e}")

        if files_removed > 0:
            print(f"✓ Removed {files_removed} cache file(s)")
