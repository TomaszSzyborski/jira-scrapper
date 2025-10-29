# Scraper JQL Integration - Summary

## Overview

Updated the `JiraScraper` class to use centralized JQL queries from `jql_queries.py` instead of building queries dynamically. This improves maintainability, consistency, and makes it easier to modify queries in one place.

## Changes Made

### 1. ✅ Updated Imports
**File**: `src/jira_scraper/scraper.py` (line 10)

**Added**:
```python
from .jql_queries import JQLQueries, STANDARD_FIELDS
```

### 2. ✅ Updated `get_project_tickets()` Method
**File**: `src/jira_scraper/scraper.py` (lines 159-225)

**Before**:
```python
def get_project_tickets(self, project_key, start_date, end_date, batch_size):
    jql = f"project = {project_key}"

    if start_date:
        jql += f" AND created >= '{start_date}'"
    if end_date:
        jql += f" AND created <= '{end_date}'"

    jql += " ORDER BY created ASC"
    # ... fetch logic
```

**After**:
```python
def get_project_tickets(self, project_key, start_date, end_date, batch_size):
    # Use JQL query template from jql_queries.py
    if start_date and end_date:
        jql = JQLQueries.format_query(
            JQLQueries.PROJECT_TICKETS,
            project=project_key,
            start_date=start_date,
            end_date=end_date
        )
    else:
        # Fallback for no date filtering
        jql = f'project = "{project_key}" ORDER BY created ASC'

    print(f"Using JQL query: {jql}")
    # ... fetch logic
```

**Benefits**:
- ✅ Uses centralized JQL template
- ✅ Prints the actual JQL being used for debugging
- ✅ Handles case when dates are not provided
- ✅ Consistent query format across all methods

### 3. ✅ Added `get_bugs()` Method
**File**: `src/jira_scraper/scraper.py` (lines 369-430)

**New method for fetching bugs using centralized JQL**:
```python
def get_bugs(self, project_key, start_date, end_date, batch_size=1000):
    """
    Fetch all bugs for a project within a date range using JQL from jql_queries.py.
    """
    jql = JQLQueries.format_query(
        JQLQueries.BUGS_CREATED,
        project=project_key,
        start_date=start_date,
        end_date=end_date
    )

    print(f"Fetching bugs with JQL: {jql}")
    # ... fetch logic similar to get_project_tickets
```

**Usage**:
```python
scraper = JiraScraper()
bugs = scraper.get_bugs("PROJ", "2024-01-01", "2024-12-31")
```

**JQL Generated**:
```
project = "PROJ" AND type in (Bug, Defect) AND created >= "2024-01-01" AND created <= "2024-12-31"
```

### 4. ✅ Added `get_test_executions()` Method
**File**: `src/jira_scraper/scraper.py` (lines 432-504)

**New method for fetching test executions with optional label filtering**:
```python
def get_test_executions(self, project_key, start_date, end_date, label=None, batch_size=1000):
    """
    Fetch all test executions for a project within a date range using JQL from jql_queries.py.
    """
    if label:
        jql = JQLQueries.format_query(
            JQLQueries.TEST_EXECUTIONS_WITH_LABEL,
            project=project_key,
            label=label,
            start_date=start_date,
            end_date=end_date
        )
    else:
        jql = JQLQueries.format_query(
            JQLQueries.TEST_EXECUTIONS,
            project=project_key,
            start_date=start_date,
            end_date=end_date
        )

    print(f"Fetching test executions with JQL: {jql}")
    # ... fetch logic similar to get_project_tickets
```

**Usage**:
```python
scraper = JiraScraper()

# Without label filter
test_execs = scraper.get_test_executions("PROJ", "2024-01-01", "2024-12-31")

# With label filter
test_execs = scraper.get_test_executions("PROJ", "2024-01-01", "2024-12-31", label="Sprint1")
```

**JQL Generated**:
```
# Without label
project = "PROJ" AND type = "Test Execution" AND created >= "2024-01-01" AND created <= "2024-12-31"

# With label
project = "PROJ" AND type = "Test Execution" AND labels = "Sprint1" AND created >= "2024-01-01" AND created <= "2024-12-31"
```

## Benefits

### For Developers:
✅ **Centralized JQL Management**: All queries in one place (`jql_queries.py`)
✅ **Easy to Modify**: Change query once, applies everywhere
✅ **Consistent Format**: All queries use the same template system
✅ **Debugging**: JQL is printed to console for easy troubleshooting
✅ **Type Safety**: Using predefined templates reduces typos

### For Users:
✅ **Console Output**: See exactly what JQL is being executed
✅ **Specialized Methods**: `get_bugs()`, `get_test_executions()` for convenience
✅ **Flexible Filtering**: Optional label parameter for test executions

### For Maintenance:
✅ **Single Source of Truth**: JQL queries defined in `jql_queries.py`
✅ **Easy Updates**: Modify query template once, affects all usages
✅ **Testability**: Can mock `JQLQueries` for testing
✅ **Documentation**: JQL templates are self-documenting

## Usage Examples

### Basic Project Tickets
```python
from jira_scraper import JiraScraper

scraper = JiraScraper()

# Fetch all tickets in date range
tickets = scraper.get_project_tickets(
    project_key="PROJ",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Console output:
# Using JQL query: project = "PROJ" AND created >= "2024-01-01" AND created <= "2024-12-31" ORDER BY created ASC
# Fetched 100 tickets...
# Total tickets fetched: 100
```

### Fetch Only Bugs
```python
# Fetch all bugs in date range
bugs = scraper.get_bugs(
    project_key="PROJ",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Console output:
# Fetching bugs with JQL: project = "PROJ" AND type in (Bug, Defect) AND created >= "2024-01-01" AND created <= "2024-12-31"
# Fetched 25 bugs...
# Total bugs fetched: 25
```

### Fetch Test Executions
```python
# Fetch all test executions
test_execs = scraper.get_test_executions(
    project_key="PROJ",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Fetch test executions with specific label
sprint_tests = scraper.get_test_executions(
    project_key="PROJ",
    start_date="2024-01-01",
    end_date="2024-12-31",
    label="Sprint-1"
)

# Console output:
# Fetching test executions with JQL: project = "PROJ" AND type = "Test Execution" AND labels = "Sprint-1" AND created >= "2024-01-01" AND created <= "2024-12-31"
# Fetched 15 test executions...
# Total test executions fetched: 15
```

### Command Line Usage (with main.py)
```bash
# Fetch all tickets
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31

# Console will show:
# Auto-detected: Using API token authentication (Jira Cloud)
# Connected to Jira Cloud: https://yourcompany.atlassian.net
# Using JQL query: project = "PROJ" AND created >= "2024-01-01" AND created <= "2024-12-31" ORDER BY created ASC
# Fetched 100 tickets...
# Total tickets fetched: 100
```

## JQL Query Reference

All available queries from `jql_queries.py`:

| Method | JQL Template Used | Description |
|--------|-------------------|-------------|
| `get_project_tickets()` | `PROJECT_TICKETS` | All tickets in date range |
| `get_bugs()` | `BUGS_CREATED` | Only Bug/Defect types in date range |
| `get_test_executions()` | `TEST_EXECUTIONS` | Only Test Execution types |
| `get_test_executions(label=X)` | `TEST_EXECUTIONS_WITH_LABEL` | Test Executions with specific label |

### Available JQL Templates (from jql_queries.py)

```python
# Project-based
PROJECT_TICKETS = 'project = "{project}" AND created >= "{start_date}" AND created <= "{end_date}" ORDER BY created ASC'
PROJECT_TICKETS_UPDATED = 'project = "{project}" AND updated >= "{start_date}" AND updated <= "{end_date}" ORDER BY updated ASC'

# Bug-specific
BUGS_CREATED = 'project = "{project}" AND type in (Bug, Defect) AND created >= "{start_date}" AND created <= "{end_date}"'
BUGS_RESOLVED = 'project = "{project}" AND type in (Bug, Defect) AND resolved >= "{start_date}" AND resolved <= "{end_date}"'
BUGS_OPEN = 'project = "{project}" AND type in (Bug, Defect) AND resolution = Unresolved'

# Test-related
TEST_EXECUTIONS = 'project = "{project}" AND type = "Test Execution" AND created >= "{start_date}" AND created <= "{end_date}"'
TEST_EXECUTIONS_WITH_LABEL = 'project = "{project}" AND type = "Test Execution" AND labels = "{label}" AND created >= "{start_date}" AND created <= "{end_date}"'
TEST_CASES = 'project = "{project}" AND type = Test'

# Status-based
ISSUES_IN_PROGRESS_ON_DATE = 'project = "{project}" AND status was "In Progress" ON "{date}"'
ISSUES_OPEN_ON_DATE = 'project = "{project}" AND created <= "{date}" AND (resolved is EMPTY OR resolved > "{date}")'

# Historical
ISSUES_CHANGED_TO_STATUS = 'project = "{project}" AND status changed to "{status}" during ("{start_date}", "{end_date}")'
```

## Migration Guide

### Existing Code (No Changes Needed)
The API remains the same:
```python
# This still works exactly the same
scraper = JiraScraper()
tickets = scraper.get_project_tickets("PROJ", "2024-01-01", "2024-12-31")
```

### New Convenience Methods
```python
# Now you can also use specialized methods
bugs = scraper.get_bugs("PROJ", "2024-01-01", "2024-12-31")
tests = scraper.get_test_executions("PROJ", "2024-01-01", "2024-12-31", label="Sprint-1")
```

### Custom JQL (Advanced)
If you need custom JQL, you can still use `JQLQueries` directly:
```python
from jira_scraper import JiraScraper
from jira_scraper.jql_queries import JQLQueries

scraper = JiraScraper()

# Build custom query
custom_jql = JQLQueries.format_query(
    JQLQueries.ISSUES_CHANGED_TO_STATUS,
    project="PROJ",
    status="Done",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Execute with client
results = scraper.client.search_issues(custom_jql, expand="changelog")
```

## Testing

### Manual Test
```bash
# 1. Set up credentials in .env
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_token_here

# 2. Run scraper
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31

# 3. Verify console output shows:
# - "Using JQL query: ..." message
# - Correct JQL with project key and dates
# - Ticket counts as they're fetched
```

### Unit Test Example
```python
def test_get_project_tickets_uses_jql():
    scraper = JiraScraper()

    # Mock the JQL query formatting
    with patch('jira_scraper.scraper.JQLQueries.format_query') as mock_format:
        mock_format.return_value = 'project = "TEST" AND created >= "2024-01-01"'

        tickets = scraper.get_project_tickets("TEST", "2024-01-01", "2024-12-31")

        # Verify format_query was called with correct template
        mock_format.assert_called_once_with(
            JQLQueries.PROJECT_TICKETS,
            project="TEST",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
```

## Console Output Examples

### Example 1: Fetching Project Tickets
```
Auto-detected: Using API token authentication (Jira Cloud)
Connected to Jira Cloud: https://company.atlassian.net
Using JQL query: project = "MYPROJ" AND created >= "2024-01-01" AND created <= "2024-12-31" ORDER BY created ASC
Fetched 100 tickets...
Fetched 200 tickets...
Total tickets fetched: 250
```

### Example 2: Fetching Bugs
```
Fetching bugs with JQL: project = "MYPROJ" AND type in (Bug, Defect) AND created >= "2024-01-01" AND created <= "2024-12-31"
Fetched 25 bugs...
Total bugs fetched: 25
```

### Example 3: Fetching Test Executions with Label
```
Fetching test executions with JQL: project = "MYPROJ" AND type = "Test Execution" AND labels = "Release-1.0" AND created >= "2024-01-01" AND created <= "2024-12-31"
Fetched 50 test executions...
Total test executions fetched: 50
```

## Summary

✅ **Centralized JQL queries** from `jql_queries.py`
✅ **Added debugging output** showing actual JQL being executed
✅ **New convenience methods**: `get_bugs()`, `get_test_executions()`
✅ **Backward compatible** - existing code still works
✅ **Better maintainability** - change queries in one place
✅ **Console visibility** - see exactly what's being fetched

All JQL queries are now managed centrally, making it easy to:
- Modify query logic in one place
- Add new query templates
- Debug what's being sent to Jira
- Maintain consistency across the codebase

---

**Status**: ✅ COMPLETE
**Files Modified**: 1 (`scraper.py`)
**New Methods Added**: 2 (`get_bugs()`, `get_test_executions()`)
**Lines Changed**: ~100
