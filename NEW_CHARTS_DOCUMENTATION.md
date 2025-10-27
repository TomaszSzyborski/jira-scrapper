# New Chart Features Documentation

## Overview

Three new interactive chart modules have been added to the Jira scraper project, providing comprehensive tracking and visualization capabilities for:

1. **Bug Tracking** - Daily bug creation and resolution trends
2. **Test Execution Progress** - Cumulative test execution tracking with status breakdown
3. **Open Issues Status** - Open issues categorized by workflow status

All charts include:
- Interactive Plotly visualizations
- Drilldown functionality with expandable ticket lists
- Direct links to Jira tickets
- Trend line calculations
- Summary statistics

## Quick Start

### CLI Usage

```bash
# Basic usage - generates all charts
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23

# With test label filter
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --test-label "Sprint-1"
```

### Report Structure

The generated HTML report now includes:

1. Executive Summary
2. Daily Issue Trends
3. **Open Issues Tracking** ⭐ NEW
4. **Bug Tracking** ⭐ NEW
5. **Test Execution Progress** ⭐ NEW
6. Flow Analysis
7. Temporal Trends
8. Cycle Metrics
9. Status Distribution

## 1. Bug Tracking Chart

### Purpose
Track bugs created and closed daily, identify trends, and drill down into specific bugs.

### Features
- Filters only "Bug" and "Defect" issue types
- Grouped bar chart comparing bugs created vs closed per day
- Linear trend lines for both created and closed bugs
- Interactive drilldown by date showing bug details

### Usage Example

```python
from jira_scraper import BugTrackingChart

bug_chart = BugTrackingChart(tickets, jira_url="https://jira.company.com")

# Generate chart
chart_html = bug_chart.create_bug_tracking_chart(
    start_date="2024-01-01",
    end_date="2024-10-23",
    title="Daily Bug Tracking"
)

# Get summary statistics
stats = bug_chart.get_summary_statistics("2024-01-01", "2024-10-23")
print(f"Total bugs created: {stats['total_created']}")
print(f"Currently open: {stats['final_open_bugs']}")
```

### Summary Statistics

- `total_created`: Total bugs created in period
- `total_closed`: Total bugs closed in period
- `avg_created_per_day`: Average bugs created per day
- `avg_closed_per_day`: Average bugs closed per day
- `max_open_bugs`: Maximum open bugs during period
- `final_open_bugs`: Open bugs at end date

## 2. Test Execution Cumulative Chart

### Purpose
Track cumulative test execution progress over time with status breakdown.

### Features
- Filters test executions by optional label
- Stacked area chart showing cumulative progress
- Status normalization for both Cloud and On-Premise Xray
- Interactive drilldown by date
- Coverage percentage calculation

### Usage Example

```python
from jira_scraper import TestExecutionCumulativeChart

test_executions = [t for t in tickets if t.get("issue_type") == "Test Execution"]

test_chart = TestExecutionCumulativeChart(
    test_executions,
    jira_url="https://jira.company.com",
    target_label="Sprint-1"  # Optional filter
)

# Generate chart
chart_html = test_chart.create_cumulative_chart(
    start_date="2024-01-01",
    end_date="2024-10-23"
)

# Get current status
summary = test_chart.get_current_status_summary("2024-10-23")
print(f"Coverage: {summary['coverage_percent']}%")
```

### Test Statuses

The chart tracks five status categories:
- **Passed** (Green): Tests that passed
- **Failed** (Red): Tests that failed
- **Executing** (Blue): Tests in progress
- **To Do** (Gray): Tests not started
- **Aborted** (Orange): Tests blocked/aborted

### Label Filtering

Use `target_label` to filter test executions:

```python
test_chart = TestExecutionCumulativeChart(
    test_executions,
    jira_url=jira_url,
    target_label="Sprint-1"
)
```

## 3. Open Issues Status Chart

### Purpose
Track open issues day by day, categorized by workflow status.

### Features
- Categorizes all statuses into In Progress, Open, or Blocked
- Stacked area chart showing distribution over time
- Trend line for total open issues
- Filters out Test Execution issue types

### Usage Example

```python
from jira_scraper import OpenIssuesStatusChart

issues_chart = OpenIssuesStatusChart(tickets, jira_url="https://jira.company.com")

# Generate chart
chart_html = issues_chart.create_open_issues_chart(
    start_date="2024-01-01",
    end_date="2024-10-23"
)

# Get statistics
stats = issues_chart.get_summary_statistics("2024-01-01", "2024-10-23")
print(f"Average open: {stats['avg_open']:.1f}")
```

### Status Categories

| Category | Statuses |
|----------|----------|
| **In Progress** | In Progress, In Development, In Review, Testing, QA |
| **Open** | Open, To Do, Backlog, New, Reopened |
| **Blocked** | Blocked, On Hold, Waiting |

## CLI Parameters

```bash
python main.py [options]

Required:
  --project, -p       Jira project key (e.g., PROJ)
  --start-date, -s    Start date (YYYY-MM-DD)
  --end-date, -e      End date (YYYY-MM-DD)

Optional:
  --test-label, -t    Filter test executions by label
  --output, -o        Output HTML file (default: jira_report.html)
  --granularity, -g   Temporal granularity: daily or weekly
  --batch-size, -b    API batch size (default: 100)
```

### Examples

```bash
# Basic report
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23

# With test label filter
python main.py -p PROJ -s 2024-01-01 -e 2024-10-23 -t "Sprint-1"

# Custom output file
python main.py -p PROJ -s 2024-01-01 -e 2024-10-23 -o sprint_report.html
```

## Drilldown Features

All three charts include interactive drilldown:

1. Click on any date/pattern to expand
2. View detailed ticket lists
3. Click ticket keys to open in Jira
4. See ticket summaries, statuses, priorities, assignees

### Drilldown Example

**Bug Tracking Drilldown:**
```
▼ 2024-10-15                    [Created: 3] [Closed: 2]

  Bugs Created on 2024-10-15 (3)
  | Key      | Summary                | Status | Priority | Assignee  |
  |----------|------------------------|--------|----------|-----------|
  | PROJ-123 | Login button not work  | Open   | High     | John Doe  |
  | PROJ-124 | Search crashes on iOS  | Open   | Medium   | Jane Smith|
  ...
```

## Technical Details

### Timezone Handling

All modules use timezone-aware datetimes:

```python
from datetime import timezone
start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
```

### Dependencies

- **Polars**: DataFrame operations
- **Plotly**: Interactive charts
- **NumPy**: Trend line calculations

### Performance

- Efficient DataFrame filtering
- Single-pass processing where possible
- Handles thousands of tickets

## Troubleshooting

### Charts Don't Appear

**Problem**: New charts missing from report

**Solution**: Pass `tickets` parameter:

```python
report_gen.generate_html_report(
    summary_stats=summary_stats,
    flow_metrics=flow_metrics,
    cycle_metrics=cycle_metrics,
    temporal_trends=temporal_trends,
    tickets=tickets,  # Required!
    test_label=args.test_label,
    output_file=args.output
)
```

### Test Label Not Filtering

**Problem**: All tests shown, not filtered by label

**Solution**: Check label exists on test executions:

```python
for test in test_executions:
    print(f"{test['key']}: {test.get('labels', [])}")
```

### Links Don't Work

**Problem**: Ticket links don't open Jira

**Solution**: Ensure jira_url is passed:

```python
analyzer = JiraAnalyzer(tickets, jira_url=scraper.jira_url)
report_gen = ReportGenerator("PROJ", "2024-01-01", "2024-10-23", jira_url=scraper.jira_url)
```

## Complete Example

```python
from jira_scraper import JiraScraper, JiraAnalyzer, ReportGenerator

# Fetch data
scraper = JiraScraper()
tickets = scraper.get_project_tickets("PROJ", "2024-01-01", "2024-10-23")

# Analyze
analyzer = JiraAnalyzer(tickets, jira_url=scraper.jira_url)
analyzer.build_dataframes()
summary_stats = analyzer.get_summary_statistics()
flow_metrics = analyzer.calculate_flow_metrics()
cycle_metrics = analyzer.calculate_cycle_metrics()
temporal_trends = analyzer.calculate_temporal_trends("2024-01-01", "2024-10-23")

# Generate report with all charts
report_gen = ReportGenerator(
    project_name="PROJ",
    start_date="2024-01-01",
    end_date="2024-10-23",
    jira_url=scraper.jira_url
)

report_gen.generate_html_report(
    summary_stats=summary_stats,
    flow_metrics=flow_metrics,
    cycle_metrics=cycle_metrics,
    temporal_trends=temporal_trends,
    tickets=tickets,
    test_label="Sprint-1",
    output_file="report.html"
)

print("Report generated with bug tracking, test execution, and open issues charts!")
```

## Summary

The three new chart modules provide:

✅ Bug tracking with daily trends and drilldown
✅ Cumulative test execution progress with status breakdown
✅ Open issues tracking by status category
✅ Interactive drilldown with clickable Jira links
✅ Summary statistics and key metrics
✅ CLI integration with test label filtering
✅ Timezone-aware datetime handling
✅ Professional styling consistent with existing charts

These charts give comprehensive visibility into project health, test coverage, and bug trends!
