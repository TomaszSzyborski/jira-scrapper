# Jira Scraper Restructuring Summary

## Changes Completed

### 1. ✅ Created JQL Queries Module (`jql_queries.py`)
- Centralized all JQL query templates
- Added common queries for:
  - Project tickets
  - Status tracking ("was in progress on date")
  - Bug queries
  - Test execution queries
  - Test case queries (separate from test executions)
- Includes helper functions for building complex queries
- Field configuration constants (STANDARD_FIELDS, EXTENDED_FIELDS, XRAY_FIELDS)

### 2. ✅ Removed "Open Issues" from Daily Issue Trends
- Modified `issue_trends_chart.py`:
  - Removed `open_issues` calculation from `calculate_daily_metrics()`
  - Updated `create_combined_chart()` to only show "Raised" and "Closed"
  - Removed "Open Issues" chart from `create_separate_charts()`
  - Updated summary statistics to remove open issues metrics
  - Added `net_change` statistic (raised - closed)

### 3. ✅ Created "In Progress" Tracking Chart
- New module: `in_progress_tracking_chart.py`
- Tracks issues that were in "In Progress" status on each date
- Features:
  - Uses status history from changelog to determine historical status
  - Configurable IN_PROGRESS_STATUSES list
  - Heuristic detection for custom status names
  - Daily chart with trend line
  - Drilldown showing which issues were in progress on each date
  - Summary statistics (avg, max, min, current)

### 4. ✅ Removed Open Issues Status Category Chart
- Removed `open_issues_status_chart.py` from report generator
- Replaced with `in_progress_tracking_chart.py`
- Updated `__init__.py` exports

### 5. ✅ Updated Report Structure
New report order:
1. Executive Summary
2. Daily Issue Trends (Raised vs Closed only)
3. **In Progress Tracking** (replaces Open Issues)
4. Bug Tracking
5. Test Execution Progress
6. Xray Test Execution (Legacy)
7. Flow Analysis
8. Temporal Trends
9. Cycle Metrics
10. Status Distribution

## Changes Still Needed

### 1. ⚠️ Test Execution Counting - NEEDS CLARIFICATION

**Current Implementation:**
- `test_execution_cumulative_chart.py` counts "Test Execution" issue type tickets
- Each Test Execution ticket represents a test run/execution session

**User Requirement:**
> "test execution progress should state all tests to be executed cumulatively, same for release readiness chart - i need tests to be executed number and not test executions type ticket number"

**Questions:**
1. Should we count **Test** type issues (test cases) instead of **Test Execution** tickets?
2. Are Test issues linked to Test Execution issues via issue links?
3. How do we determine if a Test (test case) has been executed?
   - Via linked Test Execution tickets?
   - Via custom fields on the Test issue?
   - Via status of the Test issue?

**Proposed Solution:**
- Query for "Test" type issues (not "Test Execution")
- For each Test issue, check if it has been executed by:
  - Finding linked Test Execution issues
  - Checking execution date
  - Getting test result status (Passed/Failed/etc)
- Show cumulative count of unique tests executed over time

### 2. ⚠️ Test Coverage Chart - NEEDS CLARIFICATION

**User Statement:**
> "test coverage chart is not needed as well"

**Question:**
- Which chart is the "test coverage chart"?
  - Is it the Xray Test Chart (`xray_test_chart.py`)?
  - Is it part of the Test Execution Cumulative Chart?
  - Is it a separate chart that doesn't exist yet?

**Current Charts with "Coverage":**
- `TestExecutionCumulativeChart.get_current_status_summary()` returns `coverage_percent`
- This is displayed in the report as "Test Coverage %"

**Action Needed:**
- Clarify which chart/metric to remove
- Update report generator accordingly

### 3. 📊 Additional Statistics - NEEDS SPECIFICATION

**User Request:**
> "propose more statistics as well"

**Current Statistics by Chart:**

**Issue Trends:**
- Total raised
- Total closed  
- Avg raised per day
- Avg closed per day
- Net change (NEW)

**In Progress:**
- Avg in progress
- Max in progress
- Min in progress
- Currently in progress

**Bug Tracking:**
- Total bugs created
- Total bugs closed
- Avg created per day
- Avg closed per day
- Max open bugs
- Currently open bugs

**Test Execution:**
- Total tests
- Passed count
- Failed count
- Executing count
- To Do count
- Aborted count
- Coverage percent
- Remaining tests

**Proposed Additional Statistics:**

1. **Velocity Metrics:**
   - Issues completed per week
   - Story points completed per sprint (if available)
   - Throughput trend (increasing/decreasing)

2. **Quality Metrics:**
   - Bug-to-feature ratio
   - Bug reopen rate
   - Average bug resolution time
   - Test pass rate trend

3. **Cycle Time Metrics:**
   - Average time in each status
   - Percentile breakdown (P50, P75, P90, P95)
   - Cycle time by issue type
   - Cycle time by priority

4. **Work Distribution:**
   - Issues by priority breakdown
   - Issues by assignee
   - Issues by component/label
   - Work load balance

5. **Predictive Metrics:**
   - Estimated completion date (based on trend)
   - Backlog burndown projection
   - Risk indicators (high WIP, old bugs, etc.)

**Question:** Which of these (or others) should be added?

## Implementation Notes

### Status History Requirement

The In Progress Tracking Chart requires `status_history` in ticket data:

```python
{
    "key": "PROJ-123",
    "status": "Done",
    "status_history": [
        {
            "from_status": "To Do",
            "to_status": "In Progress",
            "changed_at": "2024-01-15T10:00:00+00:00"
        },
        {
            "from_status": "In Progress",
            "to_status": "Done",
            "changed_at": "2024-01-20T15:30:00+00:00"
        }
    ]
}
```

This should be extracted from the Jira changelog by the scraper.

### JQL Query Usage

The JQL queries can now be imported and used:

```python
from jira_scraper.jql_queries import JQLQueries

# Get issues in progress on a specific date
jql = JQLQueries.format_query(
    JQLQueries.ISSUES_IN_PROGRESS_ON_DATE,
    project="PROJ",
    date="2024-01-15"
)
# Result: 'project = "PROJ" AND status was "In Progress" ON "2024-01-15"'
```

### Test vs Test Execution Clarification

**Current Understanding:**
- **Test Execution** (issue type): A test run session that contains multiple test cases
- **Test** (issue type): An individual test case definition
- **Test Result**: The outcome of running a Test within a Test Execution

**Xray/Zephyr Structure:**
```
Test Execution (PROJ-100)
  ├─ Test Case 1 (PROJ-50) → Result: PASSED
  ├─ Test Case 2 (PROJ-51) → Result: FAILED
  └─ Test Case 3 (PROJ-52) → Result: PASSED
```

**For Cumulative Chart:**
- Should count: 3 tests executed (PROJ-50, PROJ-51, PROJ-52)
- Currently counts: 1 test execution (PROJ-100)

## Files Modified

1. ✅ `src/jira_scraper/jql_queries.py` - NEW
2. ✅ `src/jira_scraper/issue_trends_chart.py` - MODIFIED
3. ✅ `src/jira_scraper/in_progress_tracking_chart.py` - NEW
4. ✅ `src/jira_scraper/report_generator.py` - MODIFIED
5. ✅ `src/jira_scraper/__init__.py` - MODIFIED
6. ⚠️ `src/jira_scraper/test_execution_cumulative_chart.py` - NEEDS UPDATE
7. ❌ `src/jira_scraper/open_issues_status_chart.py` - CAN BE DELETED

## Next Steps

### Immediate Actions:
1. **Clarify Test Counting Requirements**
   - Confirm: Count Test issues or Test Execution issues?
   - Specify: How to determine if a Test has been executed?
   - Decide: Which relationships/fields to use?

2. **Clarify Test Coverage Chart**
   - Identify which chart to remove
   - Update report generator

3. **Specify Additional Statistics**
   - Choose from proposed list or specify others
   - Determine where to display them
   - Implement calculations

### Future Enhancements:
1. Add status history extraction to scraper
2. Implement JQL-based "was in status on date" queries
3. Add more granular test tracking (test cases vs executions)
4. Create release readiness dashboard
5. Add sprint/iteration tracking

## Migration Guide

### For Users:

**Old Behavior:**
- Daily Issue Trends showed: Raised, Closed, Open
- Open Issues chart showed: In Progress, Open, Blocked categories

**New Behavior:**
- Daily Issue Trends shows: Raised, Closed only
- In Progress Tracking shows: Issues in "in progress" statuses day by day

**Benefits:**
- More accurate "in progress" tracking using status history
- Clearer separation of concerns
- JQL queries documented and reusable
- Better drilldown capabilities

### For Developers:

**Using JQL Queries:**
```python
from jira_scraper.jql_queries import JQLQueries

# Simple query
jql = JQLQueries.PROJECT_TICKETS.format(
    project="PROJ",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Or use format_query helper
jql = JQLQueries.format_query(
    JQLQueries.BUGS_CREATED,
    project="PROJ",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Complex query
jql = build_jql_for_date_range(
    project="PROJ",
    start_date="2024-01-01",
    end_date="2024-12-31",
    issue_types=["Bug", "Defect"],
    labels=["urgent"]
)
```

**Accessing Charts:**
```python
from jira_scraper import (
    IssueTrendsChart,           # Raised vs Closed
    InProgressTrackingChart,    # In Progress tracking
    BugTrackingChart,           # Bug trends
    TestExecutionCumulativeChart # Test execution
)
```

## Summary

### Completed:
✅ Centralized JQL queries
✅ Removed "open issues" from daily trends  
✅ Created "in progress" tracking chart
✅ Updated report structure
✅ Removed open issues status chart

### Needs Clarification:
⚠️ How to count tests (Test vs Test Execution)
⚠️ Which test coverage chart to remove
⚠️ What additional statistics to add

### Pending:
📋 Update test execution counting logic
📋 Add more statistics to reports
📋 Update documentation
📋 Add status history extraction to scraper
