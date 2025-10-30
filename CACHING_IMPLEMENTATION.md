# Caching Implementation Summary

## Overview

This document describes the caching functionality added to the Jira scraper to avoid constant API fetching and improve performance.

## Key Changes

### 1. Data Fetching Strategy

**Before:**
- Tickets were fetched with date filters in JQL queries
- Each date range required a new API call
- Bugs were filtered by creation date

**After:**
- **All tickets are fetched regardless of date** (more efficient for caching)
- **Date filtering is applied during the analysis phase** (not during fetch)
- **Bugs are filtered by issue type** (`Bug` or `Błąd w programie`) instead of date
- Same cached data can be reused for different date range analyses

### 2. Caching Mechanism

#### Cache Directory
- Default location: `.jira_cache/` (added to `.gitignore`)
- Automatically created when scraper is initialized

#### Cache Files
- Format: JSON files
- Naming: MD5 hash of query parameters (project, query type, label)
- Structure:
  ```json
  {
    "cached_at": "2024-01-15T10:30:00",
    "metadata": {
      "project_key": "PROJ",
      "start_date": null,
      "end_date": null,
      "label": "Sprint-1",
      "total_count": 150
    },
    "data": [...]
  }
  ```

#### Cache Key Generation
Cache keys are based on:
- Project key
- Query type (`tickets`, `bugs`, `test_executions`)
- Label (optional)

**Note:** Dates are NOT included in cache keys since we fetch all data regardless of date.

### 3. Updated JQL Queries

#### Project Tickets
```jql
# Old (date-filtered)
project = "PROJ" AND created >= "2024-01-01" AND created <= "2024-12-31" ORDER BY created ASC

# New (fetch all)
project = "PROJ" ORDER BY created ASC
```

#### Bugs
```jql
# Old (date-filtered)
project = "PROJ" AND type = Bug AND created >= "2024-01-01" AND created <= "2024-12-31"

# New (type-filtered)
project = "PROJ" AND (type = Bug OR type = "Błąd w programie") ORDER BY created ASC
```

#### Test Executions
```jql
# Old (date-filtered)
project = "PROJ" AND type = "Test Execution" AND created >= "2024-01-01" AND created <= "2024-12-31"

# New (fetch all)
project = "PROJ" AND type = "Test Execution" ORDER BY created ASC
```

### 4. CLI Changes

#### New Argument
```bash
--force-fetch, -f    Force fetching data from API, ignoring cache
```

#### Updated Behavior
```bash
# First run - fetches from API and caches
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31

# Second run - uses cached data
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31

# Different date range - still uses same cache (filters during analysis)
python main.py --project PROJ --start-date 2024-06-01 --end-date 2024-12-31

# Force refresh from API
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31 --force-fetch
```

## Implementation Details

### Scraper Changes (`src/jira_scraper/scraper.py`)

1. **Added cache configuration to `__init__`:**
   - `cache_dir` parameter (default: `.jira_cache`)
   - Creates cache directory if it doesn't exist

2. **New methods:**
   - `_generate_cache_key()` - Generate unique cache key from parameters (project, type, label)
   - `_get_cache_path()` - Get full path for cache file
   - `_save_to_cache()` - Save data to JSON cache file with metadata
   - `_load_from_cache()` - Load data from cache file if it exists

3. **Updated methods:**
   - `get_project_tickets()` - Added `force_fetch` parameter, checks cache before API call. **start_date/end_date are now deprecated** (kept for backwards compatibility)
   - `get_bugs()` - Added `force_fetch` parameter, uses type-based filtering (Bug or "Błąd w programie"). **start_date/end_date are now deprecated**
   - `get_test_executions()` - Added `force_fetch` parameter, fetches all executions. **start_date/end_date are now deprecated**

### Query Changes (`src/jira_scraper/jql_queries.py`)

1. **Updated query templates:**
   - `PROJECT_TICKETS` - Removed date filtering
   - `PROJECT_TICKETS_WITH_LABEL` - Removed date filtering
   - `BUGS_ALL` - New query using type filter with Polish support (Bug OR "Błąd w programie")
   - `BUGS_ALL_WITH_LABEL` - New query with label support
   - `TEST_EXECUTIONS` - Removed date filtering
   - `TEST_EXECUTIONS_WITH_LABEL` - Removed date filtering

2. **Updated COMMON_QUERIES dictionary:**
   - Changed `"bugs_in_period": JQLQueries.BUGS_CREATED` to `"bugs_all": JQLQueries.BUGS_ALL`

### Main Script Changes (`main.py`)

1. **Updated help text:**
   - Explains caching behavior
   - Notes that date filtering is analysis-time only
   - Documents bug filtering by type

2. **Updated user messages:**
   - Shows that all tickets are being fetched
   - Indicates when date filtering will be applied (during analysis)

## Benefits

1. **Performance:**
   - Avoid repeated API calls for same project data
   - Faster subsequent runs (no network latency)
   - Reduced load on Jira server

2. **Flexibility:**
   - Same cached data can be used for different date range analyses
   - No need to re-fetch when analyzing different time periods

3. **Efficiency:**
   - Rate limiting only affects initial fetch
   - Offline analysis possible after initial fetch

4. **User Control:**
   - `--force-fetch` flag for manual cache refresh
   - Clear messages about cache usage

## Important Notes

### Method Signatures
- The `start_date` and `end_date` parameters in `get_project_tickets()`, `get_bugs()`, and `get_test_executions()` are **deprecated** but kept for backwards compatibility
- These parameters are now `Optional[str] = None` instead of required
- They are not used in JQL queries or cache key generation
- Date filtering should be done during the analysis phase

### Report Generation
- `report_generator.py` does **NOT** call `get_bugs()` or `get_test_executions()` directly
- It receives all tickets from `get_project_tickets()` and filters them internally:
  - Bugs: Filtered by `issue_type` in ["bug", "defect"] or == "Błąd w programie"
  - Test Executions: Filtered by `issue_type` in ["Test Execution", "Test"]
- Charts do their own filtering based on the full ticket list

### Cache Management
- Cache files are stored in `.jira_cache/` which is git-ignored
- Each cache file includes timestamp and metadata for transparency
- Failed cache operations (read/write) show warnings but don't stop execution
- Cache invalidation is manual (use `--force-fetch` or delete cache directory)
- Cache keys are based on: project_key + query_type + label (NOT dates)
