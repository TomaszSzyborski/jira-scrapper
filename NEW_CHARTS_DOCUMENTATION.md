# New Chart Generation Features

This document describes the new chart generation capabilities added to the Jira Scraper project.

## Overview

Two new chart generation modules have been added:

1. **Issue Trends Charts** - Daily tracking of open, raised, and closed issues with trend lines
2. **Xray Test Execution Progress Charts** - Progress tracking for Xray test executions with coverage metrics

## 1. Issue Trends Charts

### Module: `issue_trends_chart.py`

The `IssueTrendsChart` class generates charts showing daily issue activity with linear trend lines.

#### Features

- **Daily metrics tracking:**
  - Issues raised per day
  - Issues closed per day
  - Total open issues per day

- **Trend line analysis:**
  - Linear regression trend lines for each metric
  - Visual indication of whether issues are increasing or decreasing

- **Multiple chart formats:**
  - Combined chart (all metrics in one view)
  - Separate charts for each metric
  - Summary statistics

#### Usage

```python
from jira_scraper import IssueTrendsChart

# Initialize with ticket data
tickets = [...] # Your ticket data from JiraScraper
trends_chart = IssueTrendsChart(tickets)

# Generate combined chart
combined_html = trends_chart.create_combined_chart(
    start_date="2024-01-01",
    end_date="2024-10-23",
    title="Daily Issue Trends"
)

# Generate separate charts
separate_charts = trends_chart.create_separate_charts(
    start_date="2024-01-01",
    end_date="2024-10-23"
)
# Returns dict with keys: 'raised', 'closed', 'open'

# Get summary statistics
stats = trends_chart.get_summary_statistics(
    start_date="2024-01-01",
    end_date="2024-10-23"
)
```

#### Summary Statistics

The `get_summary_statistics()` method returns:

```python
{
    "total_raised": 150,           # Total issues created in period
    "total_closed": 120,            # Total issues closed in period
    "avg_raised_per_day": 5.2,      # Average issues raised per day
    "avg_closed_per_day": 4.1,      # Average issues closed per day
    "max_open_issues": 80,          # Peak open issues count
    "min_open_issues": 20,          # Minimum open issues count
    "final_open_issues": 30         # Open issues at end of period
}
```

#### Chart Visualizations

All charts are generated using Plotly and include:
- Interactive tooltips on hover
- Zoom and pan capabilities
- Legend toggle
- Dashed trend lines for each metric

**Color scheme:**
- Issues Raised: Blue (#3498db)
- Issues Closed: Green (#2ecc71)
- Open Issues: Red (#e74c3c)

## 2. Xray Test Execution Progress Charts

### Module: `xray_test_chart.py`

The `XrayTestChart` class generates comprehensive test execution progress reports for Xray test executions.

#### Features

- **Test execution status tracking:**
  - Passed tests
  - Failed tests
  - Tests in execution
  - Tests to do
  - Aborted tests

- **Coverage metrics:**
  - Percentage of tests completed
  - Tests remaining for 100% coverage
  - Progress toward release readiness

- **Multiple visualization types:**
  - Pie chart (status distribution)
  - Bar chart (status counts)
  - Gauge chart (coverage percentage)
  - Stacked bar chart (release readiness)
  - Summary table

- **Label filtering:**
  - Filter test executions by specific labels (e.g., "release-1.0")

#### Usage

```python
from jira_scraper import XrayTestChart

# Initialize with test execution data
test_executions = [
    {
        "key": "PROJ-10",
        "issue_type": "Test Execution",
        "status": "PASS",
        "labels": ["release-1.0", "regression"]
    },
    # ... more test executions
]

# Create chart with label filter
xray_chart = XrayTestChart(test_executions, target_label="release-1.0")

# Generate complete report with all charts
complete_report = xray_chart.generate_complete_report()

# Or generate individual charts
pie_chart = xray_chart.create_progress_pie_chart()
bar_chart = xray_chart.create_progress_bar_chart()
gauge_chart = xray_chart.create_coverage_gauge()
readiness_chart = xray_chart.create_release_readiness_chart()
summary_table = xray_chart.create_summary_table_html()

# Get metrics programmatically
metrics = xray_chart.calculate_test_metrics()
```

#### Test Metrics

The `calculate_test_metrics()` method returns:

```python
{
    "total_tests": 100,              # Total test executions
    "passed": 60,                    # Tests that passed
    "failed": 10,                    # Tests that failed
    "executing": 5,                  # Tests currently executing
    "todo": 20,                      # Tests not yet executed
    "aborted": 5,                    # Tests aborted
    "completed": 70,                 # Passed + Failed
    "coverage_percent": 70.0,        # (Completed / Total) * 100
    "progress_percent": 75.0,        # (Completed + Executing / Total) * 100
    "remaining_for_100_percent": 20  # Tests still to do
}
```

#### Supported Xray Statuses

The module recognizes these Xray test execution statuses:
- `PASS` / `Passed`
- `FAIL` / `Failed`
- `EXECUTING` / `Executing`
- `TODO` / `To Do`
- `ABORTED` / `Aborted`

#### Chart Visualizations

**Pie Chart:**
- Shows distribution of test statuses
- Interactive hover with counts and percentages
- Color-coded by status

**Bar Chart:**
- Horizontal bars showing test counts per status
- Color-coded bars
- Count labels on bars

**Gauge Chart:**
- Shows test coverage (completed tests) as percentage
- Color zones:
  - Red (0-50%): Low coverage
  - Orange (50-80%): Medium coverage
  - Green (80-100%): Good coverage

**Release Readiness Chart:**
- Stacked bar showing:
  - Completed tests (green)
  - In progress tests (blue)
  - Remaining tests (gray)
  - Aborted tests (orange)

**Summary Table:**
- Styled HTML table with all metrics
- Color-coded rows by status type

## 3. Integration with Report Generator

Both new chart types are automatically integrated into the main report when you pass the `tickets` parameter.

### Updated Report Generator Usage

```python
from jira_scraper import ReportGenerator, JiraAnalyzer

# Analyze your data
analyzer = JiraAnalyzer(tickets)
analyzer.build_dataframes()

summary_stats = analyzer.get_summary_statistics()
flow_metrics = analyzer.calculate_flow_metrics()
cycle_metrics = analyzer.calculate_cycle_metrics()
temporal_trends = analyzer.calculate_temporal_trends(
    start_date="2024-01-01",
    end_date="2024-10-23"
)

# Generate report with new charts
report_gen = ReportGenerator(
    project_name="PROJ",
    start_date="2024-01-01",
    end_date="2024-10-23"
)

report_gen.generate_html_report(
    summary_stats=summary_stats,
    flow_metrics=flow_metrics,
    cycle_metrics=cycle_metrics,
    temporal_trends=temporal_trends,
    tickets=tickets,              # Pass raw tickets to enable new charts
    xray_label="release-1.0",     # Optional: filter Xray tests by label
    output_file="comprehensive_report.html"
)
```

### Report Structure

When `tickets` are provided, the report includes these sections (in order):

1. **Executive Summary** - Key metrics overview
2. **Daily Issue Trends** - New! Open/Raised/Closed charts with trend lines
3. **Xray Test Execution Progress** - New! If test executions exist
4. **Flow Analysis** - Status transition analysis
5. **Temporal Trends** - Original cumulative trends
6. **Cycle Metrics** - Lead time and cycle time
7. **Status Distribution** - Current status breakdown

## 4. Updated Analyzer Methods

New methods added to `JiraAnalyzer`:

### `calculate_daily_issue_metrics(start_date, end_date)`

Calculates daily aggregated metrics for issues.

```python
analyzer = JiraAnalyzer(tickets)
analyzer.build_dataframes()

daily_metrics = analyzer.calculate_daily_issue_metrics(
    start_date="2024-01-01",
    end_date="2024-10-23"
)
```

Returns Polars DataFrame with columns:
- `date`: Date
- `issues_raised`: Count of issues created on this date
- `issues_closed`: Count of issues resolved on this date
- `open_issues`: Total open issues at end of this date

### `get_xray_test_executions(label_filter=None)`

Extracts Xray test execution issues from tickets.

```python
analyzer = JiraAnalyzer(tickets)

# Get all test executions
all_tests = analyzer.get_xray_test_executions()

# Get test executions with specific label
release_tests = analyzer.get_xray_test_executions(label_filter="release-1.0")
```

## 5. Dependencies

The new modules require these dependencies (already in requirements.txt):

```
plotly>=5.14.0
numpy>=1.24.0
polars>=0.20.0
```

## 6. Examples

See `examples/generate_charts_example.py` for complete working examples:

```bash
# Run the examples
python examples/generate_charts_example.py
```

This will generate:
- `issue_trends_combined.html` - Combined issue trends chart
- `issue_trends_raised.html` - Issues raised chart
- `issue_trends_closed.html` - Issues closed chart
- `issue_trends_open.html` - Open issues chart
- `xray_test_report.html` - Complete Xray test report
- `integrated_report_with_new_charts.html` - Full integrated report

## 7. Best Practices

### Issue Trends Charts

1. **Date Range Selection:**
   - Use meaningful date ranges (at least 1 week for trends)
   - Ensure tickets exist in the date range
   - Trend lines are more meaningful with longer periods

2. **Interpreting Trends:**
   - Upward trend in "Raised": More work coming in
   - Upward trend in "Closed": Team is completing work
   - Upward trend in "Open": Backlog growing (raised > closed)
   - Compare trends to identify bottlenecks

### Xray Test Execution Charts

1. **Label Filtering:**
   - Use labels to track specific releases or milestones
   - Filter by sprint labels for sprint-specific reports
   - Combine multiple labels for comprehensive tracking

2. **Coverage Targets:**
   - Aim for >80% coverage (green zone) before release
   - Monitor "Remaining for 100%" to plan testing effort
   - Track "Failed" tests to identify quality issues

3. **Release Readiness:**
   - Green bar (completed) should be >80% for release
   - Gray bar (remaining) shows remaining test effort
   - Orange bar (aborted) may indicate test environment issues

## 8. Troubleshooting

### Issue Trends Charts

**Problem:** Empty charts or no data
- **Solution:** Ensure tickets have `created` and `resolved` dates in ISO format
- **Solution:** Check that date range overlaps with ticket creation dates

**Problem:** Trend lines are flat
- **Solution:** Need more data points (longer date range)
- **Solution:** Check if all issues created/resolved on same day

### Xray Test Execution Charts

**Problem:** No test executions found
- **Solution:** Ensure issue_type is "Test Execution" or "Test"
- **Solution:** Check that tickets have the correct issue_type field

**Problem:** Wrong tests included when using label filter
- **Solution:** Verify label names (case-sensitive)
- **Solution:** Check that labels array exists in ticket data

**Problem:** Coverage not reaching 100%
- **Solution:** This is normal - coverage = (Passed + Failed) / Total
- **Solution:** "To Do" and "Executing" tests don't count toward coverage

## 9. API Reference

### IssueTrendsChart

```python
class IssueTrendsChart:
    def __init__(self, tickets: List[Dict[str, Any]]) -> None
    def build_dataframe(self) -> pl.DataFrame
    def calculate_daily_metrics(self, start_date: str, end_date: str) -> pl.DataFrame
    def calculate_trend_line(dates: List[datetime], values: List[float]) -> List[float]
    def create_combined_chart(self, start_date: str, end_date: str, title: str) -> str
    def create_separate_charts(self, start_date: str, end_date: str) -> Dict[str, str]
    def get_summary_statistics(self, start_date: str, end_date: str) -> Dict[str, Any]
```

### XrayTestChart

```python
class XrayTestChart:
    def __init__(self, test_executions: List[Dict[str, Any]], target_label: Optional[str]) -> None
    def calculate_test_metrics(self) -> Dict[str, Any]
    def create_progress_pie_chart(self, title: str) -> str
    def create_progress_bar_chart(self, title: str) -> str
    def create_coverage_gauge(self) -> str
    def create_release_readiness_chart(self) -> str
    def create_summary_table_html(self) -> str
    def generate_complete_report(self) -> str
```

## 10. Contributing

To extend these modules:

1. **Adding new metrics:**
   - Update `calculate_daily_metrics()` or `calculate_test_metrics()`
   - Add corresponding visualization methods

2. **Adding new chart types:**
   - Use Plotly for interactive charts
   - Follow existing color scheme for consistency
   - Add helper method to chart class

3. **Supporting new test statuses:**
   - Update `XrayTestChart.XRAY_STATUSES` dictionary
   - Add corresponding color in `STATUS_COLORS`

## 11. Performance Considerations

- Issue trends calculations are O(n*d) where n=tickets, d=days
- For large datasets (>10,000 tickets), consider:
  - Using weekly granularity instead of daily
  - Filtering tickets by date before passing to chart generators
  - Pre-filtering test executions by label at query time

## 12. Future Enhancements

Potential improvements:
- [ ] Add moving average trend lines (7-day, 30-day)
- [ ] Export charts as PNG/PDF
- [ ] Add test execution timeline (when tests were executed)
- [ ] Add burn-down chart for test execution progress
- [ ] Support custom test statuses beyond Xray defaults
- [ ] Add comparison between multiple labels/sprints
- [ ] Add velocity tracking (issues closed per week)
- [ ] Add forecast based on trend lines
