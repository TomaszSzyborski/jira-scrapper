# Timezone DateTime Comparison Fix

## Issue

When using Polars with timezone-aware datetimes, you may encounter an error like:

```
schema error: could not evaluate '<=' between series 'created' of dtype datetime[us,UTC]
and series 'literal' of datetime[us]
```

This occurs when comparing timezone-aware datetime columns (from Jira API with UTC timestamps) with timezone-naive datetime literals.

## Root Cause

The Jira API returns timestamps with timezone information (e.g., `2024-01-01T10:00:00+00:00`). When these are parsed and stored in a Polars DataFrame, they become timezone-aware (`datetime[us,UTC]`).

However, when creating datetime objects from strings like `"2024-01-01"` using `datetime.fromisoformat()`, they are timezone-naive by default.

Polars cannot compare timezone-aware columns with timezone-naive literals, hence the error.

## Solution

### For analyzer.py

Updated `calculate_temporal_trends()` and `calculate_daily_issue_metrics()`:

**Before:**
```python
start = datetime.fromisoformat(start_date)
end = datetime.fromisoformat(end_date)
date_range = pl.datetime_range(start, end, interval="1d", eager=True)
```

**After:**
```python
from datetime import timezone

# Create timezone-aware datetimes
start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

# Generate date range with timezone
date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")
```

### For issue_trends_chart.py

Updated `calculate_daily_metrics()` with the same fix:

```python
from datetime import timezone

# Create timezone-aware datetimes to match DataFrame columns
start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

# Generate date range with timezone
date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")
```

## Files Modified

1. `src/jira_scraper/analyzer.py`:
   - `calculate_temporal_trends()` method
   - `calculate_daily_issue_metrics()` method

2. `src/jira_scraper/issue_trends_chart.py`:
   - `calculate_daily_metrics()` method

## Testing

To verify the fix works:

```python
from jira_scraper import JiraScraper, JiraAnalyzer, IssueTrendsChart

# Fetch tickets
scraper = JiraScraper()
tickets = scraper.get_project_tickets("PROJ", "2024-01-01", "2024-10-23")

# Test analyzer
analyzer = JiraAnalyzer(tickets)
analyzer.build_dataframes()
temporal_trends = analyzer.calculate_temporal_trends("2024-01-01", "2024-10-23")
daily_metrics = analyzer.calculate_daily_issue_metrics("2024-01-01", "2024-10-23")

print("✓ Analyzer methods work")

# Test issue trends chart
trends_chart = IssueTrendsChart(tickets)
chart_metrics = trends_chart.calculate_daily_metrics("2024-01-01", "2024-10-23")

print("✓ Issue trends chart works")
```

## Why This Works

1. **Timezone-aware datetime creation**: `.replace(tzinfo=timezone.utc)` makes the datetime timezone-aware
2. **Consistent timezone in date_range**: `time_zone="UTC"` ensures the generated date range uses UTC
3. **Matching types**: Both DataFrame columns and comparison literals are now `datetime[us,UTC]`

## Alternative Solutions

### Option 1: Convert DataFrame to timezone-naive (NOT recommended)

You could strip timezone from DataFrame columns, but this loses timezone information:

```python
self.df = self.df.with_columns([
    pl.col("created").dt.replace_time_zone(None),
    pl.col("updated").dt.replace_time_zone(None),
    pl.col("resolved").dt.replace_time_zone(None),
])
```

### Option 2: Use Polars expressions (More complex)

Instead of comparing with Python datetime objects, use Polars expressions:

```python
import polars as pl

start_pl = pl.lit(datetime.fromisoformat(start_date)).dt.replace_time_zone("UTC")
self.df.filter(pl.col("created") <= start_pl)
```

### Why We Chose the Current Solution

- ✅ Simple and clear
- ✅ Preserves timezone information
- ✅ Consistent with Jira API data
- ✅ Works with existing code structure
- ✅ No DataFrame modifications needed

## Best Practices

When working with datetime comparisons in Polars:

1. **Always match timezone awareness**: If DataFrame has timezone-aware columns, use timezone-aware comparisons
2. **Use UTC consistently**: Jira API uses UTC, so stick with UTC throughout
3. **Create timezone-aware datetime literals**: Use `.replace(tzinfo=timezone.utc)`
4. **Specify timezone in date_range**: Use `time_zone="UTC"` parameter

## Common Errors and Fixes

### Error: "schema error: could not evaluate..."

**Cause**: Timezone mismatch between DataFrame and comparison literal

**Fix**: Make comparison literal timezone-aware:
```python
from datetime import timezone
dt = datetime.fromisoformat("2024-01-01").replace(tzinfo=timezone.utc)
```

### Error: "time_zone parameter not recognized"

**Cause**: Old Polars version

**Fix**: Upgrade Polars:
```bash
pip install --upgrade polars>=0.20.0
```

### Warning: "Comparing timezone-aware with timezone-naive"

**Cause**: Mixing timezone-aware and naive datetimes

**Fix**: Ensure all datetimes in the comparison have the same timezone status

## Related Documentation

- Polars datetime documentation: https://pola-rs.github.io/polars/py-polars/html/reference/expressions/api/polars.Expr.dt.html
- Python timezone documentation: https://docs.python.org/3/library/datetime.html#timezone-objects

## Quick Reference

```python
# Always use this pattern for Jira datetime comparisons:
from datetime import datetime, timezone

# Create timezone-aware datetime
dt = datetime.fromisoformat("2024-01-01").replace(tzinfo=timezone.utc)

# Create timezone-aware date range
date_range = pl.datetime_range(
    start,
    end,
    interval="1d",
    eager=True,
    time_zone="UTC"
)
```

## Status

✅ **Fixed** - All datetime comparison methods now use timezone-aware datetimes consistently.
