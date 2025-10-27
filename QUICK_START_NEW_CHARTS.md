# Quick Start Guide - New Chart Features

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
pip install plotly>=5.14.0 numpy>=1.24.0 polars>=0.20.0
```

### Step 2: Try the Example

```bash
python examples/generate_charts_example.py
```

This will generate 6 HTML files showing all the new chart types.

### Step 3: Use in Your Code

```python
from jira_scraper import JiraAnalyzer, ReportGenerator

# Your existing code...
analyzer = JiraAnalyzer(tickets)
analyzer.build_dataframes()

# Generate report WITH new charts (just add tickets parameter)
report_gen = ReportGenerator("PROJ", "2024-01-01", "2024-10-23")
report_gen.generate_html_report(
    summary_stats=analyzer.get_summary_statistics(),
    flow_metrics=analyzer.calculate_flow_metrics(),
    cycle_metrics=analyzer.calculate_cycle_metrics(),
    temporal_trends=analyzer.calculate_temporal_trends("2024-01-01", "2024-10-23"),
    tickets=tickets,              # 👈 Add this to enable new charts!
    xray_label="release-1.0",     # 👈 Optional: filter Xray tests
    output_file="report.html"
)
```

## 📊 What You Get

### 1. Daily Issue Trends Chart
Shows day-by-day:
- Issues raised (blue line)
- Issues closed (green line)
- Open issues (red line)
- Trend lines for each metric (dashed)

**Use case:** Track if your backlog is growing or shrinking

### 2. Xray Test Execution Progress
Shows test execution status:
- Passed / Failed / Executing / To Do / Aborted
- Coverage percentage gauge
- Release readiness chart
- Summary table

**Use case:** Track testing progress toward release readiness

## 🎯 Common Use Cases

### Use Case 1: Generate Issue Trends Only

```python
from jira_scraper import IssueTrendsChart

chart = IssueTrendsChart(tickets)
html = chart.create_combined_chart("2024-01-01", "2024-10-23")

# Save to file
with open("trends.html", "w") as f:
    f.write(html)
```

### Use Case 2: Track Test Progress for a Release

```python
from jira_scraper import XrayTestChart

# Filter for your release label
test_chart = XrayTestChart(test_executions, target_label="release-2.0")

# Generate complete report
html = test_chart.generate_complete_report()

# Get metrics
metrics = test_chart.calculate_test_metrics()
print(f"Coverage: {metrics['coverage_percent']}%")
print(f"Remaining: {metrics['remaining_for_100_percent']} tests")
```

### Use Case 3: Get Statistics Only (No Charts)

```python
from jira_scraper import IssueTrendsChart

chart = IssueTrendsChart(tickets)
stats = chart.get_summary_statistics("2024-01-01", "2024-10-23")

print(f"Total raised: {stats['total_raised']}")
print(f"Total closed: {stats['total_closed']}")
print(f"Net change: {stats['total_raised'] - stats['total_closed']}")
```

## 📁 File Structure

```
jira-scrapper/
├── src/jira_scraper/
│   ├── issue_trends_chart.py    # 👈 NEW: Issue trends with trend lines
│   ├── xray_test_chart.py       # 👈 NEW: Xray test progress
│   ├── analyzer.py               # ✏️ UPDATED: New methods added
│   ├── report_generator.py       # ✏️ UPDATED: Integrated new charts
│   └── __init__.py               # ✏️ UPDATED: Export new modules
│
├── examples/
│   └── generate_charts_example.py  # 👈 NEW: Complete examples
│
├── NEW_CHARTS_DOCUMENTATION.md     # 👈 NEW: Detailed docs
├── IMPLEMENTATION_SUMMARY.md       # 👈 NEW: Implementation details
└── QUICK_START_NEW_CHARTS.md      # 👈 This file
```

## 🔍 Key Features

### Issue Trends Charts
✅ Daily aggregation of raised/closed/open issues
✅ Linear trend lines (shows if issues are increasing/decreasing)
✅ Combined or separate charts
✅ Summary statistics

### Xray Test Charts
✅ All test statuses (PASS/FAIL/EXECUTING/TODO/ABORTED)
✅ Coverage percentage with gauge chart
✅ Release readiness visualization
✅ Filter by label (e.g., specific release)
✅ Multiple chart types (pie, bar, gauge, stacked)

## ⚡ Quick Tips

1. **Trend Lines**: Need at least 7 days of data for meaningful trend lines
2. **Xray Labels**: Use consistent labels across test executions for accurate filtering
3. **Coverage**: Coverage = (Passed + Failed) / Total Tests
4. **Date Ranges**: Use YYYY-MM-DD format for all dates
5. **Test Types**: Works with issue_type "Test Execution" or "Test"

## 📚 Learn More

- **Full Documentation**: See `NEW_CHARTS_DOCUMENTATION.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Project Overview**: See `README.md`

## 🐛 Troubleshooting

**Q: Charts are empty?**
- Check that tickets have `created` and `resolved` dates
- Verify date range overlaps with your data

**Q: No test executions found?**
- Ensure issue_type is "Test Execution" or "Test"
- Check label filtering (case-sensitive)

**Q: Trend lines are flat?**
- Need more data points (longer date range)
- Check if all activity happened on same day

## 💡 Examples Output

Running `python examples/generate_charts_example.py` creates:

1. **issue_trends_combined.html** - All metrics in one chart
2. **issue_trends_raised.html** - Issues raised only
3. **issue_trends_closed.html** - Issues closed only
4. **issue_trends_open.html** - Open issues only
5. **xray_test_report.html** - Complete test execution report
6. **integrated_report_with_new_charts.html** - Full report with everything

Open any of these in your browser to see the interactive charts!

## 🎨 Chart Customization

All charts use Plotly and support:
- 🔍 Zoom and pan
- 💬 Interactive tooltips on hover
- 👁️ Toggle legend items
- 📱 Responsive design
- 🎨 Professional color scheme

## ✅ You're Ready!

That's it! You now have powerful new charting capabilities for:
- Tracking daily issue flow with predictive trends
- Monitoring test execution progress toward release readiness
- Generating professional interactive reports

Happy analyzing! 📊
