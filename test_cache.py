#!/usr/bin/env python3
"""Simple test script to verify caching functionality without API calls."""

import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the required modules
class MockJIRA:
    """Mock JIRA client for testing."""
    pass

class MockJIRAError(Exception):
    """Mock JIRA error for testing."""
    pass

# Inject mocks before importing
sys.modules['jira'] = type('jira', (), {'JIRA': MockJIRA})()
sys.modules['jira.exceptions'] = type('jira.exceptions', (), {'JIRAError': MockJIRAError})()

# Now import our scraper
from src.jira_scraper.scraper import JiraScraper

def test_cache_key_generation():
    """Test that cache keys are generated consistently."""
    print("Testing cache key generation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create scraper with temp cache directory
        scraper = JiraScraper.__new__(JiraScraper)
        scraper.cache_dir = Path(tmpdir)
        scraper.cache_dir.mkdir(exist_ok=True)

        # Generate cache keys
        key1 = scraper._generate_cache_key("PROJ", "tickets", "2024-01-01", "2024-12-31", "Sprint-1")
        key2 = scraper._generate_cache_key("PROJ", "tickets", "2024-01-01", "2024-12-31", "Sprint-1")
        key3 = scraper._generate_cache_key("PROJ", "tickets", "2024-01-01", "2024-12-31", "Sprint-2")

        assert key1 == key2, "Same parameters should generate same cache key"
        assert key1 != key3, "Different parameters should generate different cache keys"

        print(f"  ✓ Cache key 1: {key1}")
        print(f"  ✓ Cache key 2: {key2}")
        print(f"  ✓ Cache key 3: {key3} (different label)")

def test_save_and_load_cache():
    """Test saving and loading data from cache."""
    print("\nTesting cache save and load...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create scraper with temp cache directory
        scraper = JiraScraper.__new__(JiraScraper)
        scraper.cache_dir = Path(tmpdir)
        scraper.cache_dir.mkdir(exist_ok=True)

        # Test data
        test_data = [
            {"key": "PROJ-1", "summary": "Test ticket 1"},
            {"key": "PROJ-2", "summary": "Test ticket 2"},
        ]

        test_metadata = {
            "project_key": "PROJ",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }

        # Generate cache key
        cache_key = scraper._generate_cache_key("PROJ", "tickets", "2024-01-01", "2024-12-31", None)

        # Save to cache
        print(f"  Saving data to cache (key: {cache_key})...")
        scraper._save_to_cache(cache_key, test_data, test_metadata)

        # Verify file exists
        cache_path = scraper._get_cache_path(cache_key)
        assert cache_path.exists(), "Cache file should exist"
        print(f"  ✓ Cache file created: {cache_path.name}")

        # Load from cache
        print("  Loading data from cache...")
        loaded_data = scraper._load_from_cache(cache_key)

        assert loaded_data is not None, "Should load cached data"
        assert len(loaded_data) == len(test_data), "Should load same number of items"
        assert loaded_data[0]["key"] == test_data[0]["key"], "Should load same data"
        print(f"  ✓ Loaded {len(loaded_data)} items from cache")

        # Verify cache structure
        with open(cache_path, 'r') as f:
            cache_content = json.load(f)
            assert "cached_at" in cache_content, "Cache should have timestamp"
            assert "metadata" in cache_content, "Cache should have metadata"
            assert "data" in cache_content, "Cache should have data"
            print(f"  ✓ Cache timestamp: {cache_content['cached_at']}")

def test_cache_miss():
    """Test loading from cache when file doesn't exist."""
    print("\nTesting cache miss scenario...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create scraper with temp cache directory
        scraper = JiraScraper.__new__(JiraScraper)
        scraper.cache_dir = Path(tmpdir)
        scraper.cache_dir.mkdir(exist_ok=True)

        # Try to load non-existent cache
        result = scraper._load_from_cache("nonexistent_key")

        assert result is None, "Should return None for cache miss"
        print("  ✓ Cache miss handled correctly")

def test_cache_path():
    """Test cache path generation."""
    print("\nTesting cache path generation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        scraper = JiraScraper.__new__(JiraScraper)
        scraper.cache_dir = Path(tmpdir)

        cache_key = "test_key_123"
        cache_path = scraper._get_cache_path(cache_key)

        assert cache_path.parent == scraper.cache_dir, "Path should be in cache dir"
        assert cache_path.name == f"{cache_key}.json", "Path should have correct filename"
        print(f"  ✓ Cache path: {cache_path}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Jira Scraper Cache Functionality Tests")
    print("=" * 60)

    try:
        test_cache_key_generation()
        test_save_and_load_cache()
        test_cache_miss()
        test_cache_path()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

        print("\nCache functionality is working correctly:")
        print("  • Cache keys are generated consistently")
        print("  • Data can be saved to and loaded from cache")
        print("  • Cache files include timestamps and metadata")
        print("  • Cache misses are handled gracefully")
        print("\nUsage:")
        print("  python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31")
        print("    → First run fetches from API and caches data")
        print("  python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31")
        print("    → Second run uses cached data (no API call)")
        print("  python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31 --force-fetch")
        print("    → Force fetch ignores cache and fetches from API")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
