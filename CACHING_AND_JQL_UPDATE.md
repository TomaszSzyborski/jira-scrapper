# Caching & JQL Update - Summary

## Overview

Major updates to data fetching and caching:
1. **Removed date filters from JQL** - Now fetches ALL bugs and test executions from project
2. **Added Polish bug type** - Includes "Błąd w programie" in bug queries
3. **Implemented local caching** - Saves fetched data to avoid re-fetching
4. **Added --force-fetch flag** - Forces fresh data fetch even when cache exists

## Key Changes

### 1. ✅ JQL Query Updates

**File**: `src/jira_scraper/jql_queries.py`

**Before**:
```python
BUGS_CREATED = 'project = "{project}" AND type = Bug AND created >= "{start_date}" AND created <= "{end_date}"'
TEST_EXECUTIONS = 'project = "{project}" AND type = "Test Execution" AND created >= "{start_date}" AND created <= "{end_date}"'
```

**After**:
```python
# Fetch ALL bugs (no date filter)
BUGS_ALL = 'project = "{project}" AND type in (Bug, "Błąd w programie") ORDER BY created DESC'
BUGS_ALL_WITH_LABEL = 'project = "{project}" AND type in (Bug, "Błąd w programie") AND labels = "{label}" ORDER BY created DESC'

# Fetch ALL test executions (no date filter)
TEST_EXECUTIONS = 'project = "{project}" AND type = "Test Execution" ORDER BY created DESC'
TEST_EXECUTIONS_WITH_LABEL = 'project = "{project}" AND type = "Test Execution" AND labels = "{label}" ORDER BY created DESC'
```

**Key differences**:
- ❌ Removed `created >= "{start_date}" AND created <= "{end_date}"`
- ✅ Added Polish bug type: `"Błąd w programie"`
- ✅ Changed from `type = Bug` to `type in (Bug, "Błąd w programie")`
- ✅ Added `ORDER BY created DESC` for consistent ordering

### 2. ✅ Scraper Method Updates

**File**: `src/jira_scraper/scraper.py`

**Before**:
```python
def get_bugs(
    self,
    project_key: str,
    start_date: str,  # Required
    end_date: str,    # Required
    label: Optional[str] = None,
    batch_size: int = 1000,
) -> List[Dict[str, Any]]:
```

**After**:
```python
def get_bugs(
    self,
    project_key: str,
    label: Optional[str] = None,  # No date parameters!
    batch_size: int = 1000,
) -> List[Dict[str, Any]]:
    """Fetch ALL bugs for a project (no date filter)."""
```

Similar changes for `get_test_executions()` - removed `start_date` and `end_date` parameters.

### 3. ✅ Local Data Caching System

**File**: `src/jira_scraper/cache.py` (NEW)

Complete caching implementation with:

**Features**:
- Saves fetched data to `.jira_cache/` directory
- Generates unique cache keys based on project, data type, and label
- Stores metadata (cached_at, count)
- Automatic cache loading/saving

**Key Methods**:
```python
class DataCache:
    def save(project_key, data_type, data, label=None) -> str
        """Save data to cache file."""

    def load(project_key, data_type, label=None) -> List[Dict]
        """Load data from cache file."""

    def exists(project_key, data_type, label=None) -> bool
        """Check if cache exists."""

    def get_cache_info(project_key, data_type, label=None) -> Dict
        """Get cache metadata."""

    def clear_cache(project_key=None)
        """Clear cache files."""
```

**Cache File Format**:
```json
{
  "project_key": "PROJ",
  "data_type": "bugs",
  "label": "Sprint-1",
  "cached_at": "2025-10-29T15:30:00",
  "count": 150,
  "data": [
    {
      "key": "PROJ-123",
      "summary": "Bug description",
      ...
    }
  ]
}
```

**Cache Files**:
- `.jira_cache/PROJ_bugs_12ab34cd.json`
- `.jira_cache/PROJ_bugs_Sprint-1_56ef78gh.json`
- `.jira_cache/PROJ_test_executions_90ij12kl.json`

### 4. ✅ Updated main.py

**New Workflow**:
```python
# 1. Check if cache exists
if not force_fetch and cache.exists(project, "bugs", label):
    bugs = cache.load(project, "bugs", label)  # Load from cache
else:
    bugs = scraper.get_bugs(project, label)    # Fetch from Jira
    cache.save(project, "bugs", bugs, label)   # Save to cache
```

**New Command Line Flags**:
- `--force-fetch` / `-f` - Force fetch from Jira (ignore cache)
- `--clear-cache` - Clear cached data and exit

**Updated Help Text**:
```
--start-date: Report start date (for filtering in report, not for data fetching)
--end-date: Report end date (for filtering in report, not for data fetching)
```

**Note**: Dates are now ONLY used for filtering in the report generation, NOT for data fetching!

## Usage Examples

### First Run (Fetch from Jira):
```bash
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23
```
Output:
```
Initializing Jira connection...
Fetching project info for PROJ...

[1/2] Fetching ALL bugs from Jira...
Fetching bugs with JQL: project = "PROJ" AND type in (Bug, "Błąd w programie") ORDER BY created DESC
Total bugs fetched: 150
✓ Saved 150 bugs to cache: .jira_cache/PROJ_bugs_a1b2c3d4.json

[2/2] Fetching ALL test executions from Jira...
Total test executions fetched: 45
✓ Saved 45 test_executions to cache: .jira_cache/PROJ_test_executions_e5f6g7h8.json
```

### Second Run (Load from Cache):
```bash
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23
```
Output:
```
Initializing Jira connection...

[1/2] Loading bugs from cache...
✓ Loaded 150 bugs from cache (cached at: 2025-10-29T15:30:00)
Total bugs available: 150

[2/2] Loading test executions from cache...
✓ Loaded 45 test_executions from cache (cached at: 2025-10-29T15:30:00)
Total test executions available: 45

Generating HTML report...
```

### Force Fetch (Ignore Cache):
```bash
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --force-fetch
```
Always fetches fresh data from Jira, updates cache.

### Clear Cache:
```bash
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --clear-cache
```
Output:
```
Clearing cache for project PROJ...
✓ Removed 2 cache file(s)
```

### With Label Filtering:
```bash
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --label Sprint-1
```
Creates separate cache for labeled data.

## Date Range Behavior

**Important**: Dates are now ONLY for report filtering, NOT data fetching!

### Before:
```
--start-date 2024-01-01 --end-date 2024-10-23
→ Fetches ONLY bugs created between 2024-01-01 and 2024-10-23
→ Report shows those bugs
```

### After:
```
--start-date 2024-01-01 --end-date 2024-10-23
→ Fetches ALL bugs from entire project history
→ Report filters and displays bugs within 2024-01-01 to 2024-10-23
```

**Why this is better**:
- ✅ One-time fetch of all data
- ✅ Can generate multiple reports for different date ranges without re-fetching
- ✅ Faster subsequent runs (uses cache)
- ✅ Complete historical data available for analysis

## Performance Comparison

### Before (No Cache):
```
Run 1: Fetch 150 bugs (30 seconds) → Generate report
Run 2: Fetch 150 bugs (30 seconds) → Generate report
Run 3: Fetch 150 bugs (30 seconds) → Generate report
Total: 90 seconds for 3 reports
```

### After (With Cache):
```
Run 1: Fetch 150 bugs (30 seconds) → Save cache → Generate report
Run 2: Load cache (< 1 second) → Generate report
Run 3: Load cache (< 1 second) → Generate report
Total: ~32 seconds for 3 reports (70% faster!)
```

## Polish Bug Type Support

Now correctly fetches both:
- **English**: `type = Bug`
- **Polish**: `type = "Błąd w programie"`

JQL:
```jql
project = "PROJ" AND type in (Bug, "Błąd w programie")
```

This ensures all bug types are captured regardless of Jira language configuration.

## Cache Management

### Cache Directory Structure:
```
.jira_cache/
├── PROJ_bugs_a1b2c3d4.json                    (all bugs, no label)
├── PROJ_bugs_Sprint-1_e5f6g7h8.json          (bugs with label Sprint-1)
├── PROJ_test_executions_i9j0k1l2.json        (all test executions)
└── PROJ_test_executions_Sprint-1_m3n4o5p6.json
```

### Cache Key Generation:
```python
# No label
"PROJ_bugs_a1b2c3d4"  = MD5("PROJ_bugs")[:8]

# With label
"PROJ_bugs_Sprint-1_e5f6g7h8" = MD5("PROJ_bugs_Sprint-1")[:8]
```

### When to Clear Cache:

Clear cache when:
- ✅ New bugs/tests added to Jira
- ✅ Bugs/tests updated in Jira
- ✅ Need fresh data from Jira

**Clear specific project**:
```bash
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --clear-cache
```

**Or manually delete**:
```bash
rm -rf .jira_cache/
```

## Files Modified

1. **`src/jira_scraper/jql_queries.py`**:
   - Renamed `BUGS_CREATED` → `BUGS_ALL`
   - Removed date parameters from queries
   - Added Polish bug type

2. **`src/jira_scraper/scraper.py`**:
   - Updated `get_bugs()` - removed date parameters
   - Updated `get_test_executions()` - removed date parameters

3. **`main.py`**:
   - Added cache loading/saving logic
   - Added `--force-fetch` flag
   - Added `--clear-cache` flag
   - Updated help text for dates

4. **`src/jira_scraper/cache.py`** (NEW):
   - Complete caching implementation

5. **`.gitignore`**:
   - Added `.jira_cache/`

## Benefits

### For Users:
✅ **Much faster** - Subsequent runs use cache (< 1 second vs 30+ seconds)
✅ **No rate limits** - One fetch, multiple reports
✅ **Flexible date ranges** - Change report dates without re-fetching
✅ **Complete data** - All historical bugs/tests available

### For Development:
✅ **Offline work** - Can generate reports without Jira access (after first fetch)
✅ **Testing** - No need to hit Jira API repeatedly
✅ **Debugging** - Consistent data across runs

### For Jira API:
✅ **Fewer requests** - Reduces load on Jira server
✅ **No duplicate fetches** - Cache prevents redundant API calls
✅ **Respect rate limits** - One-time fetch per data set

## Migration Notes

### Breaking Changes:

**Old code (WILL FAIL)**:
```python
bugs = scraper.get_bugs(
    project_key="PROJ",
    start_date="2024-01-01",  # ❌ Parameter removed
    end_date="2024-10-23",     # ❌ Parameter removed
    label=None
)
```

**New code**:
```python
bugs = scraper.get_bugs(
    project_key="PROJ",
    label=None  # ✅ Only project and optional label
)
```

### Workflow Changes:

**Before**: Dates control data fetching
```bash
# Fetches bugs from Jan-Oct 2024
python main.py --start-date 2024-01-01 --end-date 2024-10-23

# Fetches bugs from Jan-Nov 2024 (new fetch!)
python main.py --start-date 2024-01-01 --end-date 2024-11-30
```

**After**: Dates only control report filtering
```bash
# Fetches ALL bugs (or loads from cache)
python main.py --start-date 2024-01-01 --end-date 2024-10-23

# Uses SAME data, different report date range (no fetch!)
python main.py --start-date 2024-01-01 --end-date 2024-11-30
```

## Troubleshooting

### Cache is stale:
```bash
# Option 1: Use --force-fetch
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --force-fetch

# Option 2: Clear cache first
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --clear-cache
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23
```

### Cache file corrupted:
```bash
rm -rf .jira_cache/
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23
```

### Different labels:
Each label combination creates a separate cache file:
```bash
# Cache 1: No label
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23

# Cache 2: Sprint-1 label (separate cache)
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --label Sprint-1

# Cache 3: Sprint-2 label (separate cache)
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --label Sprint-2
```

## Summary

✅ **Removed date filters from JQL** - Fetches complete project history
✅ **Added Polish bug type** - `"Błąd w programie"` support
✅ **Implemented caching** - Fast subsequent runs
✅ **Added --force-fetch** - Force fresh data fetch
✅ **Added --clear-cache** - Easy cache management
✅ **Updated workflow** - Dates now only for report filtering

### Key Takeaway:
**Dates are for REPORT FILTERING, not DATA FETCHING**
- Fetch data once (all history)
- Generate multiple reports with different date ranges
- Much faster with caching!

---

**Date**: 2025-10-29
**Status**: ✅ COMPLETE
**Impact**: Major performance improvement + flexible date filtering
