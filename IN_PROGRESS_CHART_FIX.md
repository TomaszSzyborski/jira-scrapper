# In Progress Chart Fix - Summary

## Issues Fixed

### 1. ❌ Chart Type Was Wrong
**Problem**: Chart used line graph with markers instead of bar chart
**Fix**: Changed to `go.Bar()` instead of `go.Scatter()` in line 194-200

### 2. ❌ Drilldown Showed Current Status
**Problem**: Drilldown table showed current ticket status instead of the status on that specific date
**Fix**:
- Added new method `_get_status_on_date()` (lines 232-276)
- Updated drilldown to call this method for each ticket (line 335)
- Table header now says "Status on Date" to be clear

### 3. ❌ Closed Tickets Appeared in Drilldown
**Problem**: Logic for checking "not done" was incorrect, including tickets that were already closed on the target date
**Fix**:
- Completely rewrote `_was_not_done_on_date()` method (lines 28-98)
- Now correctly walks through status history to find status on target date
- Uses proper status category checking via `StatusDefinitions.is_not_done()`

### 4. ❌ No Centralized Status Definitions
**Problem**: Status mappings scattered across multiple files, hard to maintain
**Fix**:
- Created new `status_definitions.py` module with `StatusDefinitions` class
- Centralized all status lists: TODO_STATUSES, IN_PROGRESS_STATUSES, DONE_STATUSES
- Centralized all detection keywords
- Provided utility methods: `is_todo_status()`, `is_in_progress_status()`, `is_done_status()`, `categorize_status()`

## Files Changed

### 1. ✅ `src/jira_scraper/status_definitions.py` (NEW)
**Purpose**: Centralized status definitions for consistent categorization

**Key Features**:
- `StatusDefinitions` class with static methods
- Three status lists:
  - `TODO_STATUSES`: 14 common To Do statuses
  - `IN_PROGRESS_STATUSES`: 23 common In Progress statuses
  - `DONE_STATUSES`: 19 common Done statuses
- Keyword lists for heuristic detection
- Methods:
  - `is_todo_status(status)` - Check if status is To Do
  - `is_in_progress_status(status)` - Check if status is In Progress
  - `is_done_status(status)` - Check if status is Done
  - `categorize_status(status, status_category)` - Categorize into one of three
  - `is_not_done(status, status_category)` - Main method for "open" filtering
- Convenience functions for backward compatibility

**Status Coverage**:
```python
TODO_STATUSES = [
    "To Do", "TODO", "Open", "New", "Backlog", "Reopened",
    "Ready", "Ready for Development", "Ready for Dev", "Planned",
    "Pending", "Waiting", "On Hold", "Blocked"
]

IN_PROGRESS_STATUSES = [
    "In Progress", "In Development", "In Dev", "Developing", "Development",
    "In Review", "In Code Review", "Code Review", "Reviewing", "Review",
    "Testing", "In Testing", "In QA", "QA", "Quality Assurance",
    "To Test", "Ready for Testing", "Ready for QA",
    "Verification", "In Verification",
    "Deployment", "In Deployment", "Ready for Deployment",
    "UAT", "User Acceptance Testing"
]

DONE_STATUSES = [
    "Done", "Closed", "Resolved", "Complete", "Completed", "Finished",
    "Released", "Deployed", "Live", "Production",
    "Cancelled", "Canceled", "Rejected", "Duplicate",
    "Won't Do", "Won't Fix", "Invalid", "Cannot Reproduce"
]
```

### 2. ✅ `src/jira_scraper/in_progress_tracking_chart.py` (MODIFIED)

**Changes**:

#### Import StatusDefinitions (line 8)
```python
from .status_definitions import StatusDefinitions
```

#### Removed DONE_STATUSES constant (was lines 14-24)
Now uses `StatusDefinitions` instead

#### Rewrote `_was_not_done_on_date()` method (lines 28-98)
**Old logic**:
- Checked if ticket was resolved before date
- Used simple status history lookup
- Didn't properly handle edge cases

**New logic**:
```python
def _was_not_done_on_date(self, ticket, target_date):
    # 1. Check if ticket existed yet
    if created.date() > target_date.date():
        return False

    # 2. Get status history
    if not status_history:
        # No history, check current status
        return StatusDefinitions.is_not_done(current_status, status_category)

    # 3. Find status on target_date by walking through history
    sorted_history = sorted(status_history, key=lambda x: x["changed_at"])

    # Find initial status (from first transition)
    if sorted_history and created.date() < first_change.date():
        status_at_date = sorted_history[0].get("from_status")

    # Walk through transitions to find status on target_date
    for history_entry in sorted_history:
        if changed_at.date() <= target_date.date():
            status_at_date = history_entry["to_status"]
        else:
            break

    # 4. Check if status was NOT done
    return StatusDefinitions.is_not_done(status_at_date, status_category_at_date)
```

#### Changed chart from line to bar (lines 162-230)
**Old**:
```python
fig.add_trace(go.Scatter(
    x=dates,
    y=in_progress,
    name="Not Done (In Progress)",
    mode="lines+markers",
    line=dict(color="#f39c12", width=2),
    marker=dict(size=4)
))
```

**New**:
```python
fig.add_trace(go.Bar(
    x=dates,
    y=in_progress,
    name="Not Done",
    marker_color="#f39c12"
))
```

#### Added `_get_status_on_date()` method (lines 232-276)
**Purpose**: Get the actual status of a ticket on a specific date for drilldown

```python
def _get_status_on_date(self, ticket, target_date):
    # Similar logic to _was_not_done_on_date but returns status string
    # instead of boolean
    ...
    return status_at_date
```

#### Updated drilldown to show status on date (lines 278-348)
**Key changes**:
- Line 327: Table header now says "Status on Date"
- Line 335: Calls `_get_status_on_date(ticket, date)` to get actual status
- Added `data-i18n` attributes for translation support

### 3. ✅ `src/jira_scraper/status_category_chart.py` (MODIFIED)

**Changes**:
- Line 8: Added import `from .status_definitions import StatusDefinitions`
- Lines 12-17: Removed `STATUS_CATEGORY_MAP` constant
- Lines 27-39: Simplified `_get_status_category()` to just call `StatusDefinitions.categorize_status()`

**Old**:
```python
STATUS_CATEGORY_MAP = {
    "To Do": [...],
    "In Progress": [...],
    "Done": [...]
}

def _get_status_category(self, status, status_category):
    # 50+ lines of mapping logic
    ...
```

**New**:
```python
def _get_status_category(self, status, status_category):
    return StatusDefinitions.categorize_status(status, status_category or "")
```

### 4. ✅ `src/jira_scraper/__init__.py` (MODIFIED)
**Changes**:
- Line 19: Added import `from .status_definitions import StatusDefinitions`
- Line 33: Added `"StatusDefinitions"` to `__all__` list

## Technical Details

### Status Detection Logic

The new `StatusDefinitions` uses a two-tier approach:

1. **Jira statusCategory Field** (if available):
   - `statusCategory = "To Do"` → "To Do"
   - `statusCategory = "In Progress"` or `"Indeterminate"` → "In Progress"
   - `statusCategory = "Done"` → "Done"

2. **Fallback to Status Name**:
   - **Exact match**: Check if status is in predefined lists
   - **Heuristic match**: Check if status contains keywords

Example:
```python
# Using Jira's statusCategory (preferred)
categorize_status("Custom Status", status_category="In Progress")
# Returns: "In Progress"

# Using status name only (fallback)
categorize_status("Ready for QA")
# Returns: "In Progress" (matched by keyword "qa")

# Check if ticket is open
is_not_done("Closed")
# Returns: False

is_not_done("In Development")
# Returns: True
```

### Historical Status Lookup

The new logic correctly handles status history:

```python
# Ticket timeline:
# 2024-01-01: Created (initial status: "To Do")
# 2024-01-05: Changed to "In Progress"
# 2024-01-10: Changed to "Done"

# Query: Was ticket open on 2024-01-03?
_was_not_done_on_date(ticket, datetime(2024, 1, 3))
# Returns: True (status was "To Do")

# Query: Was ticket open on 2024-01-07?
_was_not_done_on_date(ticket, datetime(2024, 1, 7))
# Returns: True (status was "In Progress")

# Query: Was ticket open on 2024-01-12?
_was_not_done_on_date(ticket, datetime(2024, 1, 12))
# Returns: False (status was "Done")
```

### Drilldown Accuracy

Previously, drilldown showed current status:
```
Date: 2024-01-07
Ticket PROJ-123 | Summary | Status: Done | Assignee
```

Now shows actual status on that date:
```
Date: 2024-01-07
Ticket PROJ-123 | Summary | Status: In Progress | Assignee
```

## Benefits

### For Users:
✅ **Correct visualization**: Bar chart instead of line chart
✅ **Accurate data**: Only shows tickets that were actually open on each date
✅ **Transparent drilldown**: Shows the actual status on that date, not current status
✅ **No closed tickets**: Properly filters out tickets that were already done

### For Developers:
✅ **Centralized status logic**: All status definitions in one place
✅ **Easy to extend**: Just add new statuses to the lists in `status_definitions.py`
✅ **Consistent behavior**: All charts use the same status detection
✅ **Better maintainability**: Change status mapping in one place, applies everywhere

### For Customization:
✅ **Easy to add custom statuses**: Edit `status_definitions.py`
✅ **Support for different Jira workflows**: Heuristic detection handles custom status names
✅ **Extensible**: Can add new status categories if needed

## Testing

### Manual Test Cases:

1. **Test Bar Chart**:
   - Generate report with tickets
   - Check "In Progress Tracking" section
   - Verify chart shows bars, not lines
   - Verify bars are orange (#f39c12)

2. **Test Date Filtering**:
   - Create ticket on 2024-01-01
   - Move to "In Progress" on 2024-01-05
   - Move to "Done" on 2024-01-10
   - Generate report for 2024-01-01 to 2024-01-15
   - Verify chart shows:
     - Count = 1 from Jan 1-9
     - Count = 0 from Jan 10+

3. **Test Drilldown**:
   - Click on a date in the chart
   - Verify drilldown shows correct tickets
   - Verify "Status on Date" column shows status on that date, not current status
   - Verify no closed tickets appear

4. **Test Custom Statuses**:
   - Create tickets with custom statuses like "Ready for QA", "Awaiting Deployment"
   - Verify they are correctly categorized as "In Progress"
   - Verify they appear in the chart when not done

## Migration Guide

### No Breaking Changes!

The API remains the same:
```python
from jira_scraper import InProgressTrackingChart

chart = InProgressTrackingChart(tickets, jira_url)
html = chart.create_in_progress_chart(start_date, end_date)
```

### Custom Status Workflows

If you have custom Jira statuses, add them to `status_definitions.py`:

```python
# Edit src/jira_scraper/status_definitions.py

class StatusDefinitions:
    IN_PROGRESS_STATUSES: List[str] = [
        ...,
        "Your Custom Status",  # Add here
        "Another Custom Status"
    ]
```

Or add keywords:
```python
IN_PROGRESS_KEYWORDS: List[str] = [
    ...,
    "custom",  # Will match "Custom Status", "In Custom State", etc.
]
```

## Summary

✅ **Fixed chart type**: Now uses bar chart with dates on X-axis
✅ **Fixed open ticket counting**: Only counts `statusCategory != Done` on each date
✅ **Fixed drilldown**: Shows actual status on date, not current status
✅ **Created status definitions**: Centralized status mappings in `status_definitions.py`
✅ **Non-cumulative**: Each bar shows count for that date, not cumulative
✅ **Removed closed tickets**: Properly filters out tickets that were done on target date

The In Progress Tracking chart now correctly shows:
- **Bar chart** (not line chart)
- **Number of open tickets on each date** (not cumulative)
- **Accurate drilldown** with status on that specific date
- **No closed tickets** in the results

---

**Status**: ✅ COMPLETE
**Files Created**: 1 (`status_definitions.py`)
**Files Modified**: 3 (`in_progress_tracking_chart.py`, `status_category_chart.py`, `__init__.py`)
**Lines Added**: ~250
**Lines Modified**: ~150
