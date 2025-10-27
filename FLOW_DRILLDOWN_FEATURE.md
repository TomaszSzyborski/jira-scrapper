# Flow Pattern Drilldown Feature

## Overview

The flow analysis section now includes interactive drilldown capability, allowing you to click on any flow pattern to see the complete list of tickets that followed that pattern, with links to view them in Jira.

## Features

### 1. **Interactive Pattern Rows**
Each flow pattern is displayed as a clickable row showing:
- The flow pattern (e.g., "To Do → In Progress → Done")
- The count of tickets following this pattern
- An expandable arrow indicator

### 2. **Ticket Details Table**
When you click on a pattern, you'll see a detailed table with:
- **Key**: Ticket number (clickable link to Jira)
- **Summary**: Ticket title/description
- **Status**: Current status
- **Priority**: Ticket priority
- **Assignee**: Person assigned to the ticket

### 3. **Direct Links to Jira**
Each ticket key is a hyperlink that opens the ticket directly in your Jira instance (opens in new tab).

## Usage

### Basic Usage

```python
from jira_scraper import JiraScraper, JiraAnalyzer, ReportGenerator

# Fetch tickets
scraper = JiraScraper()
tickets = scraper.get_project_tickets("PROJ", "2024-01-01", "2024-10-23")

# Analyze with Jira URL for link generation
analyzer = JiraAnalyzer(tickets, jira_url=scraper.jira_url)
analyzer.build_dataframes()

# Generate report with Jira URL
report_gen = ReportGenerator(
    project_name="PROJ",
    start_date="2024-01-01",
    end_date="2024-10-23",
    jira_url=scraper.jira_url  # Important: pass the Jira URL!
)

report_gen.generate_html_report(
    summary_stats=analyzer.get_summary_statistics(),
    flow_metrics=analyzer.calculate_flow_metrics(),
    cycle_metrics=analyzer.calculate_cycle_metrics(),
    temporal_trends=analyzer.calculate_temporal_trends("2024-01-01", "2024-10-23"),
    output_file="report_with_drilldown.html"
)
```

### With Environment Variables

The scraper automatically reads `JIRA_URL` from your `.env` file:

```python
# .env file
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your_username
JIRA_PASSWORD=your_password

# Python code - Jira URL is automatically used
scraper = JiraScraper()
analyzer = JiraAnalyzer(tickets, jira_url=scraper.jira_url)
report_gen = ReportGenerator("PROJ", "2024-01-01", "2024-10-23", jira_url=scraper.jira_url)
```

## Visual Example

### Collapsed State
```
▶ To Do → In Progress → Done                                    [15 tickets]
▶ To Do → In Progress → To Test → Done                         [8 tickets]
▶ To Do → In Progress → To Test → In Progress → Done           [3 tickets]
```

### Expanded State (after clicking)
```
▼ To Do → In Progress → Done                                    [15 tickets]

  Tickets following pattern: To Do → In Progress → Done (15 tickets)

  | Key      | Summary                        | Status | Priority | Assignee    |
  |----------|--------------------------------|--------|----------|-------------|
  | PROJ-123 | Implement login functionality  | Done   | High     | John Doe    |
  | PROJ-124 | Fix navigation bug             | Done   | Medium   | Jane Smith  |
  | PROJ-125 | Update documentation           | Done   | Low      | John Doe    |
  ...
```

## Configuration

### Passing Jira URL

The Jira URL is required for generating ticket links. You have three options:

#### Option 1: Pass explicitly

```python
scraper = JiraScraper(jira_url="https://company.atlassian.net")
analyzer = JiraAnalyzer(tickets, jira_url="https://company.atlassian.net")
report_gen = ReportGenerator("PROJ", "2024-01-01", "2024-10-23",
                            jira_url="https://company.atlassian.net")
```

#### Option 2: Use scraper's URL

```python
scraper = JiraScraper()  # Reads from JIRA_URL env var
analyzer = JiraAnalyzer(tickets, jira_url=scraper.jira_url)
report_gen = ReportGenerator("PROJ", "2024-01-01", "2024-10-23",
                            jira_url=scraper.jira_url)
```

#### Option 3: Without Jira URL (links won't work)

```python
# Works but ticket keys won't be clickable links
analyzer = JiraAnalyzer(tickets)
report_gen = ReportGenerator("PROJ", "2024-01-01", "2024-10-23")
```

## Implementation Details

### Files Modified

1. **`analyzer.py`**
   - Updated `JiraAnalyzer.__init__()` to accept `jira_url` parameter
   - Modified `_find_flow_patterns()` to include ticket details with each pattern
   - Returns pattern with associated tickets: `{"pattern": "...", "count": N, "tickets": [...]}`

2. **`report_generator.py`**
   - Updated `ReportGenerator.__init__()` to accept `jira_url` parameter
   - Enhanced `_build_flow_analysis()` to generate interactive drilldown HTML
   - Added CSS styles for pattern rows, expandable sections, and ticket tables
   - Added JavaScript `togglePattern()` function for expand/collapse functionality

### Data Structure

The flow pattern data now includes ticket details:

```python
{
    "pattern": "To Do → In Progress → Done",
    "count": 15,
    "tickets": [
        {
            "key": "PROJ-123",
            "summary": "Implement login functionality",
            "status": "Done",
            "priority": "High",
            "assignee": "John Doe"
        },
        # ... more tickets
    ]
}
```

### HTML Structure

```html
<div class="pattern-row">
    <div class="pattern-header" onclick="togglePattern('pattern-0')">
        <span class="pattern-arrow">▶</span>
        <span class="pattern-text">To Do → In Progress → Done</span>
        <span class="pattern-count">15 tickets</span>
    </div>
    <div id="pattern-0" class="pattern-details" style="display: none;">
        <div class="ticket-list">
            <h4>Tickets following pattern...</h4>
            <table class="ticket-table">
                <tr>
                    <th>Key</th><th>Summary</th><th>Status</th>
                    <th>Priority</th><th>Assignee</th>
                </tr>
                <tr>
                    <td><a href="https://jira.../browse/PROJ-123">PROJ-123</a></td>
                    <td>Implement login functionality</td>
                    <td>Done</td>
                    <td>High</td>
                    <td>John Doe</td>
                </tr>
                ...
            </table>
        </div>
    </div>
</div>
```

## Styling

### CSS Classes

- `.pattern-row` - Container for each pattern
- `.pattern-header` - Clickable header showing pattern and count
- `.pattern-arrow` - Expandable arrow (▶/▼)
- `.pattern-text` - The flow pattern text
- `.pattern-count` - Badge showing ticket count
- `.pattern-details` - Expandable section containing tickets
- `.ticket-list` - Container for ticket table
- `.ticket-table` - Styled table for ticket details
- `.ticket-link` - Styled links to Jira tickets

### Colors

- Primary color: `#667eea` (purple-blue)
- Hover color: `#764ba2` (darker purple)
- Background: `#f8f9fa` (light gray)
- Border: `#e0e0e0` (medium gray)

## Benefits

### 1. **Quick Pattern Analysis**
- Instantly see which tickets followed problematic patterns
- Identify common workflow issues

### 2. **Direct Investigation**
- Click through to specific tickets in Jira
- No need to manually search for ticket numbers

### 3. **Comprehensive Context**
- See ticket summary, status, priority, and assignee
- Understand the full context of flow patterns

### 4. **Team Collaboration**
- Share reports with clickable links
- Team members can directly access relevant tickets

## Examples

### Example 1: Finding Bounced Tickets

If you see a pattern like "In Progress → To Test → In Progress → Done" with 5 tickets:

1. Click on the pattern row
2. Review the 5 tickets that bounced back
3. Click on a ticket link to open in Jira
4. Investigate why it bounced back to In Progress

### Example 2: Analyzing Successful Flows

For the pattern "To Do → In Progress → Done" with 50 tickets:

1. Click to expand
2. See all 50 tickets that followed this ideal flow
3. Identify team members who consistently follow this pattern
4. Use as examples for process improvement

### Example 3: Identifying Bottlenecks

For "In Progress → Blocked → In Progress → Done":

1. Expand to see affected tickets
2. Check assignees and priorities
3. Click through to understand blocking reasons
4. Plan improvements to reduce blocking

## Troubleshooting

### Links Don't Work

**Problem**: Ticket keys are not clickable or don't link to Jira

**Solution**: Ensure you pass the `jira_url` parameter:
```python
scraper = JiraScraper()
analyzer = JiraAnalyzer(tickets, jira_url=scraper.jira_url)
report_gen = ReportGenerator("PROJ", dates..., jira_url=scraper.jira_url)
```

### No Tickets Shown

**Problem**: Pattern expands but shows "0 tickets"

**Cause**: Tickets with no transitions (created and immediately closed) won't have patterns

**Solution**: This is expected - these tickets never went through a flow

### Wrong Jira URL

**Problem**: Links go to wrong Jira instance

**Solution**: Check your `JIRA_URL` in `.env` or pass correct URL explicitly

### JavaScript Not Working

**Problem**: Click doesn't expand/collapse

**Solution**: Check browser console for errors. Ensure JavaScript is enabled.

## Performance

- **Minimal overhead**: Ticket details are collected during pattern analysis
- **No additional API calls**: Uses already-fetched ticket data
- **Responsive UI**: Smooth expand/collapse animations
- **Scalable**: Handles hundreds of patterns and thousands of tickets

## Future Enhancements

Potential improvements:
- [ ] Filter tickets by assignee, priority, or status
- [ ] Export ticket lists to CSV
- [ ] Add ticket creation/resolution dates
- [ ] Show ticket age and cycle time
- [ ] Add search/filter within ticket lists
- [ ] Sort columns in ticket table
- [ ] Add pagination for large ticket lists

## Summary

The flow drilldown feature provides:
- ✅ **Interactive exploration** of flow patterns
- ✅ **Direct links** to Jira tickets
- ✅ **Complete ticket context** (summary, status, priority, assignee)
- ✅ **Professional UI** with smooth animations
- ✅ **Zero configuration** (if using environment variables)

This makes it easy to investigate workflow patterns and take action on specific tickets directly from your analysis reports!
