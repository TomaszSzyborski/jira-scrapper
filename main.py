#!/usr/bin/env python3
"""Simple Jira ticket fetcher with caching and parameterizable JQL."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from jira import JIRA
import polars as pl


class JiraFetcher:
    """Simple Jira connector with caching."""

    def __init__(self):
        """Initialize Jira connection from environment variables."""
        load_dotenv()

        self.jira_url = os.getenv("JIRA_URL")
        if not self.jira_url:
            raise ValueError("JIRA_URL not found in environment variables")

        # Auto-detect authentication method
        jira_email = os.getenv("JIRA_EMAIL")
        jira_token = os.getenv("JIRA_API_TOKEN")
        jira_username = os.getenv("JIRA_USERNAME")
        jira_password = os.getenv("JIRA_PASSWORD")

        # Try Cloud authentication (email + token)
        if jira_email and jira_token:
            print(f"Connecting to Jira Cloud: {self.jira_url}")
            self.jira = JIRA(
                server=self.jira_url,
                basic_auth=(jira_email, jira_token)
            )
        # Try On-Premise authentication (username + password)
        elif jira_username and jira_password:
            print(f"Connecting to Jira On-Premise: {self.jira_url}")
            self.jira = JIRA(
                server=self.jira_url,
                basic_auth=(jira_username, jira_password)
            )
        else:
            raise ValueError(
                "Missing credentials. Set either:\n"
                "  - JIRA_EMAIL and JIRA_API_TOKEN (for Cloud), or\n"
                "  - JIRA_USERNAME and JIRA_PASSWORD (for On-Premise)"
            )

    def build_jql(
        self,
        project: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        label: Optional[str] = None,
    ) -> str:
        """
        Build JQL query to fetch bugs only.
        Note: Date filtering is done in Python analysis, not in JQL.

        Args:
            project: Jira project key (e.g., 'PROJ')
            start_date: Not used in JQL (kept for backwards compatibility)
            end_date: Not used in JQL (kept for backwards compatibility)
            label: Optional label to filter by

        Returns:
            JQL query string
        """
        # Fetch only bugs - date filtering happens in Python
        jql_parts = [f'project = "{project}"', 'type in (Bug, "Błąd w programie")']

        if label:
            jql_parts.append(f"labels = '{label}'")

        jql = " AND ".join(jql_parts)
        jql += " ORDER BY created ASC"

        return jql

    def fetch_issues(
        self,
        project: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        label: Optional[str] = None,
        batch_size: int = 100,
    ) -> list:
        """
        Fetch issues from Jira using JQL.

        Args:
            project: Jira project key
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            label: Optional label to filter by
            batch_size: Number of issues to fetch per request

        Returns:
            List of issue dictionaries
        """
        jql = self.build_jql(project, start_date, end_date, label)
        print(f"\nJQL Query: {jql}")

        issues = []
        start_at = 0

        while True:
            print(f"Fetching issues {start_at} to {start_at + batch_size}...")

            batch = self.jira.search_issues(
                jql,
                startAt=start_at,
                maxResults=batch_size,
                expand='changelog',
                fields='*all'
            )

            if not batch:
                break

            # Convert issues to dictionaries
            for issue in batch:
                issues.append(self._issue_to_dict(issue))

            print(f"  Found {len(batch)} issues (total: {len(issues)})")

            if len(batch) < batch_size:
                break

            start_at += batch_size

        return issues

    def _issue_to_dict(self, issue) -> dict:
        """
        Convert Jira issue object to dictionary.

        Args:
            issue: Jira issue object

        Returns:
            Dictionary with issue data
        """
        fields = issue.raw['fields']

        # Extract changelog
        changelog = []
        if hasattr(issue, 'changelog'):
            for history in issue.changelog.histories:
                for item in history.items:
                    if item.field == 'status':
                        changelog.append({
                            'created': history.created,
                            'author': history.author.displayName if hasattr(history.author, 'displayName') else str(history.author),
                            'from_string': item.fromString,
                            'to_string': item.toString,
                        })

        return {
            'key': issue.key,
            'id': issue.id,
            'summary': fields.get('summary', ''),
            'status': fields.get('status', {}).get('name', ''),
            'issue_type': fields.get('issuetype', {}).get('name', ''),
            'priority': fields.get('priority', {}).get('name', '') if fields.get('priority') else '',
            'assignee': fields.get('assignee', {}).get('displayName', '') if fields.get('assignee') else '',
            'reporter': fields.get('reporter', {}).get('displayName', '') if fields.get('reporter') else '',
            'created': fields.get('created', ''),
            'updated': fields.get('updated', ''),
            'resolved': fields.get('resolutiondate', ''),
            'labels': fields.get('labels', []),
            'components': [c['name'] for c in fields.get('components', [])],
            'description': fields.get('description', ''),
            'changelog': changelog,
        }


class FlowAnalyzer:
    """Analyze ticket status flows using Polars."""

    # Status category mappings
    STATUS_CATEGORIES = {
        'NEW': ['new', 'to do'],
        'IN PROGRESS': ['analysis', 'blocked', 'development', 'review',
                        'development done', 'to test', 'in test'],
        'CLOSED': ['rejected', 'closed', 'resolved', 'ready for uat'],
    }

    def __init__(self, issues: list, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Initialize flow analyzer with issues.

        Args:
            issues: List of issue dictionaries
            start_date: Optional start date for filtering (YYYY-MM-DD)
            end_date: Optional end date for filtering (YYYY-MM-DD)
        """
        self.issues = issues
        self.start_date = start_date
        self.end_date = end_date

        # Filter issues by date if provided
        if start_date or end_date:
            self.filtered_issues = self._filter_issues_by_date()
        else:
            self.filtered_issues = issues

    def _filter_issues_by_date(self) -> list:
        """Filter issues by creation date."""
        filtered = []
        for issue in self.issues:
            created = issue.get('created', '')
            if not created:
                continue

            created_date = created.split('T')[0]  # Extract YYYY-MM-DD

            if self.start_date and created_date < self.start_date:
                continue
            if self.end_date and created_date > self.end_date:
                continue

            filtered.append(issue)

        return filtered

    def categorize_status(self, status: str) -> str:
        """Categorize a status into NEW, IN PROGRESS, or CLOSED."""
        if not status:
            return 'UNKNOWN'

        status_lower = status.lower()
        for category, statuses in self.STATUS_CATEGORIES.items():
            if status_lower in statuses:
                return category

        return 'OTHER'

    def build_transitions_dataframe(self) -> pl.DataFrame:
        """
        Build a Polars DataFrame of all status transitions.

        Returns:
            DataFrame with columns: issue_key, from_status, to_status,
                                   from_category, to_category, transition_date,
                                   author, duration_hours
        """
        transitions = []

        for issue in self.filtered_issues:
            issue_key = issue['key']
            current_status = issue['status']
            changelog = issue.get('changelog', [])
            created = issue['created']

            # Build full transition history
            if not changelog:
                # Issue created and never changed status
                transitions.append({
                    'issue_key': issue_key,
                    'from_status': None,
                    'to_status': current_status,
                    'from_category': None,
                    'to_category': self.categorize_status(current_status),
                    'transition_date': created,
                    'author': issue['reporter'],
                    'duration_hours': None,
                })
            else:
                # Add initial creation
                first_change = changelog[0]
                first_status = first_change['from_string']

                transitions.append({
                    'issue_key': issue_key,
                    'from_status': None,
                    'to_status': first_status,
                    'from_category': None,
                    'to_category': self.categorize_status(first_status),
                    'transition_date': created,
                    'author': issue['reporter'],
                    'duration_hours': None,
                })

                # Process all status transitions
                for i, change in enumerate(changelog):
                    from_status = change['from_string']
                    to_status = change['to_string']
                    transition_date = change['created']

                    # Calculate duration in previous status
                    duration_hours = None
                    if i == 0:
                        # Duration from creation to first transition
                        duration_hours = self._calculate_duration(created, transition_date)
                    else:
                        # Duration from previous transition
                        prev_transition = changelog[i-1]['created']
                        duration_hours = self._calculate_duration(prev_transition, transition_date)

                    transitions.append({
                        'issue_key': issue_key,
                        'from_status': from_status,
                        'to_status': to_status,
                        'from_category': self.categorize_status(from_status),
                        'to_category': self.categorize_status(to_status),
                        'transition_date': transition_date,
                        'author': change['author'],
                        'duration_hours': duration_hours,
                    })

        if not transitions:
            return pl.DataFrame()

        df = pl.DataFrame(transitions)
        return df

    def _calculate_duration(self, start: str, end: str) -> float:
        """Calculate duration in hours between two datetime strings."""
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            delta = end_dt - start_dt
            return delta.total_seconds() / 3600  # Convert to hours
        except:
            return None

    def detect_loops(self) -> dict:
        """Detect status loops and rework in ticket flows."""
        loops_data = {
            'total_loops': 0,
            'issues_with_loops': [],
            'common_loops': [],
        }

        issues_with_loops = set()
        loop_patterns = {}

        for issue in self.filtered_issues:
            changelog = issue.get('changelog', [])
            if len(changelog) < 2:
                continue

            # Track status history
            status_history = []
            for change in changelog:
                to_status = change['to_string']
                status_history.append(to_status)

                # Check if this status appeared before (loop detected)
                if to_status in status_history[:-1]:
                    loops_data['total_loops'] += 1
                    issues_with_loops.add(issue['key'])

                    # Find what status it came from
                    from_status = change['from_string']
                    loop_key = f"{to_status} ← {from_status}"
                    loop_patterns[loop_key] = loop_patterns.get(loop_key, 0) + 1

        loops_data['issues_with_loops'] = sorted(list(issues_with_loops))
        loops_data['common_loops'] = [
            {'pattern': k, 'count': v}
            for k, v in sorted(loop_patterns.items(), key=lambda x: x[1], reverse=True)
        ][:10]  # Top 10

        return loops_data

    def calculate_time_in_status(self) -> dict:
        """Calculate average time spent in each status."""
        df = self.build_transitions_dataframe()

        if df.is_empty() or 'duration_hours' not in df.columns:
            return {}

        # Group by from_status and calculate average duration
        time_stats = (
            df.filter(
                (pl.col('from_status').is_not_null()) &
                (pl.col('duration_hours').is_not_null())
            )
            .group_by('from_status')
            .agg([
                pl.col('duration_hours').mean().alias('avg_hours'),
                pl.col('duration_hours').median().alias('median_hours'),
                pl.col('duration_hours').min().alias('min_hours'),
                pl.col('duration_hours').max().alias('max_hours'),
                pl.len().alias('count')
            ])
            .sort('avg_hours', descending=True)
        )

        results = {}
        for row in time_stats.iter_rows(named=True):
            status = row['from_status']
            results[status] = {
                'avg_hours': round(row['avg_hours'], 2),
                'avg_days': round(row['avg_hours'] / 24, 2),
                'median_hours': round(row['median_hours'], 2) if row['median_hours'] else 0,
                'min_hours': round(row['min_hours'], 2) if row['min_hours'] else 0,
                'max_hours': round(row['max_hours'], 2) if row['max_hours'] else 0,
                'count': row['count'],
            }

        return results

    def calculate_timeline_metrics(self) -> dict:
        """Calculate created/closed/open tickets over time."""
        timeline = {}

        # Group issues by date
        daily_stats = {}

        for issue in self.filtered_issues:
            created_date = issue.get('created', '').split('T')[0]
            resolved_date = issue.get('resolved', '')
            if resolved_date:
                resolved_date = resolved_date.split('T')[0]

            if created_date:
                if created_date not in daily_stats:
                    daily_stats[created_date] = {'created': 0, 'closed': 0}
                daily_stats[created_date]['created'] += 1

            if resolved_date:
                if resolved_date not in daily_stats:
                    daily_stats[resolved_date] = {'created': 0, 'closed': 0}
                daily_stats[resolved_date]['closed'] += 1

        # Sort dates and calculate open count
        sorted_dates = sorted(daily_stats.keys())
        cumulative_open = 0

        timeline_data = []
        for date in sorted_dates:
            stats = daily_stats[date]
            created = stats['created']
            closed = stats['closed']
            cumulative_open += created - closed

            timeline_data.append({
                'date': date,
                'created': created,
                'closed': closed,
                'open': max(0, cumulative_open),
            })

        timeline['daily_data'] = timeline_data

        return timeline

    def calculate_flow_metrics(self) -> dict:
        """
        Calculate comprehensive flow metrics.

        Returns:
            Dictionary with flow statistics
        """
        df = self.build_transitions_dataframe()

        if df.is_empty():
            return {
                'total_transitions': 0,
                'unique_statuses': 0,
                'flow_patterns': [],
                'all_statuses': [],
                'loops': {},
                'time_in_status': {},
                'timeline': {},
            }

        # Count transitions between statuses
        flow_counts = (
            df.filter(pl.col('from_status').is_not_null())
            .group_by(['from_status', 'to_status'])
            .agg(pl.len().alias('count'))
            .sort('count', descending=True)
        )

        # Get unique statuses
        all_statuses = set()
        for status in df['from_status'].drop_nulls():
            all_statuses.add(status)
        for status in df['to_status']:
            all_statuses.add(status)

        # Convert to list of flow patterns
        flow_patterns = []
        for row in flow_counts.iter_rows(named=True):
            flow_patterns.append({
                'from': row['from_status'],
                'to': row['to_status'],
                'count': row['count'],
            })

        # Detect loops
        loops = self.detect_loops()

        # Calculate time in status
        time_in_status = self.calculate_time_in_status()

        # Calculate timeline metrics
        timeline = self.calculate_timeline_metrics()

        return {
            'total_transitions': len(df),
            'unique_statuses': len(all_statuses),
            'flow_patterns': flow_patterns,
            'all_statuses': sorted(all_statuses),
            'loops': loops,
            'time_in_status': time_in_status,
            'timeline': timeline,
            'total_issues': len(self.filtered_issues),
        }


class ReportGenerator:
    """Generate HTML reports with Plotly.js visualizations."""

    def __init__(self, metadata: dict, flow_metrics: dict):
        """
        Initialize report generator.

        Args:
            metadata: Project metadata
            flow_metrics: Flow metrics from FlowAnalyzer
        """
        self.metadata = metadata
        self.flow_metrics = flow_metrics

    def _calculate_trend(self, x_values: list, y_values: list) -> list:
        """Calculate simple linear trend line."""
        if len(x_values) < 2:
            return [y_values[0]] * len(y_values) if y_values else []

        n = len(x_values)
        sum_x = sum(range(n))
        sum_y = sum(y_values)
        sum_xy = sum(i * y for i, y in enumerate(y_values))
        sum_x2 = sum(i * i for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        return [slope * i + intercept for i in range(n)]

    def generate_html(self, output_file: str = 'jira_flow_report.html'):
        """
        Generate comprehensive HTML report with multiple visualizations.

        Args:
            output_file: Output HTML file path

        Returns:
            Path to generated report
        """
        # Prepare data
        flow_patterns = self.flow_metrics['flow_patterns']
        all_statuses = self.flow_metrics['all_statuses']
        loops = self.flow_metrics.get('loops', {})
        time_in_status = self.flow_metrics.get('time_in_status', {})
        timeline = self.flow_metrics.get('timeline', {})

        # Timeline data
        timeline_data = timeline.get('daily_data', [])
        dates = [d['date'] for d in timeline_data]
        created_counts = [d['created'] for d in timeline_data]
        closed_counts = [d['closed'] for d in timeline_data]
        open_counts = [d['open'] for d in timeline_data]

        # Calculate trends
        created_trend = self._calculate_trend(dates, created_counts) if created_counts else []
        closed_trend = self._calculate_trend(dates, closed_counts) if closed_counts else []
        open_trend = self._calculate_trend(dates, open_counts) if open_counts else []

        # Sankey diagram data
        node_labels = all_statuses
        node_dict = {status: idx for idx, status in enumerate(node_labels)}

        sources = []
        targets = []
        values = []
        link_labels = []
        link_colors = []

        # Detect backward flows for coloring
        for pattern in flow_patterns:
            from_status = pattern['from']
        to_status = pattern['to']
        count = pattern['count']

        sources.append(node_dict[from_status])
        targets.append(node_dict[to_status])
        values.append(count)
        link_labels.append(f"{from_status} → {to_status}: {count}")

        # Check if this is a backward/loop transition
        is_loop = False
        for loop in loops.get('common_loops', []):
            if f"{to_status} ← {from_status}" in loop['pattern']:
                is_loop = True
                break

        # Red for loops, gray for normal
        link_colors.append('rgba(255,0,0,0.3)' if is_loop else 'rgba(0,0,0,0.2)')

        # Time in status table HTML
        time_table_rows = ""
        for status, stats in sorted(time_in_status.items(), key=lambda x: x[1]['avg_days'], reverse=True):
            time_table_rows += f"""
        <tr>
            <td>{status}</td>
            <td>{stats['avg_days']:.1f}</td>
            <td>{stats['median_hours'] / 24:.1f}</td>
            <td>{stats['count']}</td>
        </tr>
        """

        # Loop details HTML
        loop_rows = ""
        for loop in loops.get('common_loops', [])[:10]:
            loop_rows += f"""
        <tr>
            <td>{loop['pattern']}</td>
            <td>{loop['count']}</td>
        </tr>
        """

        # Generate HTML
        html_content = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jira Bug Flow Report - {self.metadata['project']}</title>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #2d3748;
            font-size: 1.8em;
            margin-bottom: 15px;
        }}
        .metadata {{
            color: #718096;
            font-size: 0.95em;
            line-height: 1.6;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .stat-card.warning {{
            border-left: 4px solid #f59e0b;
        }}
        .stat-label {{
            color: #718096;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }}
        .stat-value {{
            color: #2d3748;
            font-size: 2em;
            font-weight: 700;
        }}
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
        .chart-title {{
            color: #2d3748;
            font-size: 1.3em;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        .chart-subtitle {{
            color: #718096;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #f7fafc;
            font-weight: 600;
            color: #2d3748;
        }}
        tr:hover {{
            background-color: #f7fafc;
        }}
        .loop-emphasis {{
            color: #dc2626;
            font-weight: 600;
        }}
        .footer {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            color: #718096;
            font-size: 0.9em;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        </style>
        </head>
        <body>
        <div class="container">
        <div class="header">
            <h1>🐛 Jira Bug Flow Analysis</h1>
            <div class="metadata">
                <strong>Project:</strong> {self.metadata['project']}<br>
                <strong>Fetched:</strong> {self.metadata.get('fetched_at', 'N/A')}<br>
                <strong>Date Range:</strong> {self.metadata.get('start_date', 'All')} to {self.metadata.get('end_date', 'All')}<br>
                <strong>Total Bugs:</strong> {self.flow_metrics.get('total_issues', 0)}
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Bugs</div>
                <div class="stat-value">{self.flow_metrics.get('total_issues', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Transitions</div>
                <div class="stat-value">{self.flow_metrics['total_transitions']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Unique Statuses</div>
                <div class="stat-value">{self.flow_metrics['unique_statuses']}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Rework Loops</div>
                <div class="stat-value loop-emphasis">{loops.get('total_loops', 0)}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Bugs with Loops</div>
                <div class="stat-value loop-emphasis">{len(loops.get('issues_with_loops', []))}</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📈 Created vs Closed Bugs Over Time</div>
            <div class="chart-subtitle">Daily bug creation and closure with trend lines</div>
            <div id="timeline-chart"></div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📊 Open Bugs Over Time</div>
            <div class="chart-subtitle">Cumulative open bugs with trend analysis</div>
            <div id="open-chart"></div>
        </div>

        <div class="chart-container">
            <div class="chart-title">🔄 Status Flow Diagram (Sankey)</div>
            <div class="chart-subtitle">Red flows indicate rework/loops (bugs going backward in the process)</div>
            <div id="sankey-chart"></div>
        </div>

        <div class="chart-container">
            <div class="chart-title">⏱️ Average Time in Each Status</div>
            <div class="chart-subtitle">How long bugs spend in each status (in days)</div>
            <table>
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Avg Days</th>
                        <th>Median Days</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    {time_table_rows if time_table_rows else '<tr><td colspan="4">No data available</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="chart-container">
            <div class="chart-title loop-emphasis">🔁 Rework Patterns (Loops)</div>
            <div class="chart-subtitle">Top 10 patterns where bugs went backwards in the workflow</div>
            <table>
                <thead>
                    <tr>
                        <th>Loop Pattern</th>
                        <th>Occurrences</th>
                    </tr>
                </thead>
                <tbody>
                    {loop_rows if loop_rows else '<tr><td colspan="2">No loops detected</td></tr>'}
                </tbody>
            </table>
            <p style="margin-top: 15px; color: #718096; font-size: 0.9em;">
                Total rework instances: <strong>{loops.get('total_loops', 0)}</strong><br>
                Bugs affected: <strong>{len(loops.get('issues_with_loops', []))}</strong>
            </p>
        </div>

        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Jira Bug Flow Analyzer v2.0
        </div>
        </div>

        <script>
        // Created vs Closed Timeline
        const timelineData = [
            {{
                x: {json.dumps(dates)},
                y: {json.dumps(created_counts)},
                name: 'Created',
                type: 'scatter',
                mode: 'lines+markers',
                line: {{ color: '#3b82f6', width: 2 }},
                marker: {{ size: 6 }}
            }},
            {{
                x: {json.dumps(dates)},
                y: {json.dumps(created_trend)},
                name: 'Created Trend',
                type: 'scatter',
                mode: 'lines',
                line: {{ color: '#3b82f6', width: 2, dash: 'dash' }},
                opacity: 0.6
            }},
            {{
                x: {json.dumps(dates)},
                y: {json.dumps(closed_counts)},
                name: 'Closed',
                type: 'scatter',
                mode: 'lines+markers',
                line: {{ color: '#10b981', width: 2 }},
                marker: {{ size: 6 }}
            }},
            {{
                x: {json.dumps(dates)},
                y: {json.dumps(closed_trend)},
                name: 'Closed Trend',
                type: 'scatter',
                mode: 'lines',
                line: {{ color: '#10b981', width: 2, dash: 'dash' }},
                opacity: 0.6
            }}
        ];

        const timelineLayout = {{
            xaxis: {{ title: 'Date' }},
            yaxis: {{ title: 'Number of Bugs' }},
            hovermode: 'x unified',
            showlegend: true,
            height: 400
        }};

        Plotly.newPlot('timeline-chart', timelineData, timelineLayout, {{responsive: true}});

        // Open Bugs Timeline
        const openData = [
            {{
                x: {json.dumps(dates)},
                y: {json.dumps(open_counts)},
                name: 'Open Bugs',
                type: 'scatter',
                mode: 'lines+markers',
                fill: 'tozeroy',
                line: {{ color: '#f59e0b', width: 2 }},
                marker: {{ size: 6 }}
            }},
            {{
                x: {json.dumps(dates)},
                y: {json.dumps(open_trend)},
                name: 'Trend',
                type: 'scatter',
                mode: 'lines',
                line: {{ color: '#dc2626', width: 3, dash: 'dash' }}
            }}
        ];

        const openLayout = {{
            xaxis: {{ title: 'Date' }},
            yaxis: {{ title: 'Open Bugs' }},
            hovermode: 'x unified',
            showlegend: true,
            height: 400
        }};

        Plotly.newPlot('open-chart', openData, openLayout, {{responsive: true}});

        // Sankey diagram
        const sankeyData = [{{
            type: "sankey",
            orientation: "h",
            node: {{
                pad: 15,
                thickness: 30,
                line: {{
                    color: "black",
                    width: 0.5
                }},
                label: {json.dumps(node_labels)},
                color: {json.dumps(['#' + format(hash(s) % 0xFFFFFF, '06x') for s in node_labels])}
            }},
            link: {{
                source: {json.dumps(sources)},
                target: {json.dumps(targets)},
                value: {json.dumps(values)},
                label: {json.dumps(link_labels)},
                color: {json.dumps(link_colors)}
            }}
        }}];

        const sankeyLayout = {{
            font: {{
                size: 11,
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }},
            height: 700,
            margin: {{ l: 20, r: 20, t: 20, b: 20 }}
        }};

        Plotly.newPlot('sankey-chart', sankeyData, sankeyLayout, {{responsive: true}});
        </script>
        </body>
        </html>
        """

        # Write to file
        from pathlib import Path
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Fetch Jira bugs, analyze flows with rework detection, and generate comprehensive reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all bugs from project PROJ
  %(prog)s --project PROJ

  # Fetch bugs and analyze with date range (filtering done in Python)
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-12-31 --report

  # Fetch bugs with label
  %(prog)s --project PROJ --label Sprint-1

  # Fetch bugs and generate comprehensive flow report
  %(prog)s --project PROJ --force-fetch --report

  # Generate report from cached bugs with date filtering
  %(prog)s --project PROJ --start-date 2024-06-01 --end-date 2024-12-31 --report

Note:
  - Only bugs (type: Bug, "Błąd w programie") are fetched from Jira
  - Date filtering is applied during analysis in Python, not in JQL
  - Reports include: timeline trends, loop detection, time in status, flow diagrams
        """
    )

    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Jira project key (e.g., PROJ, DEMO)'
    )

    parser.add_argument(
        '--start-date', '-s',
        help='Start date for analysis in YYYY-MM-DD format (filtering in Python, not JQL)'
    )

    parser.add_argument(
        '--end-date', '-e',
        help='End date for analysis in YYYY-MM-DD format (filtering in Python, not JQL)'
    )

    parser.add_argument(
        '--label', '-l',
        help='Filter by label (optional)'
    )

    parser.add_argument(
        '--force-fetch', '-f',
        action='store_true',
        help='Force fetch from API, ignore cache'
    )

    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=100,
        help='Number of issues to fetch per request (default: 100)'
    )

    parser.add_argument(
        '--output', '-o',
        default='jira_cached.json',
        help='Output file path (default: jira_cached.json)'
    )

    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='Generate HTML flow report from cached data'
    )

    parser.add_argument(
        '--report-output',
        default='jira_flow_report.html',
        help='HTML report output file (default: jira_flow_report.html)'
    )

    return parser.parse_args()


def validate_date(date_string: str) -> bool:
    """Validate date format YYYY-MM-DD."""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def main():
    """Main entry point."""
    args = parse_args()

    # Validate dates if provided
    if args.start_date and not validate_date(args.start_date):
        print(f"Error: Invalid start date format: {args.start_date}")
        print("Expected format: YYYY-MM-DD")
        sys.exit(1)

    if args.end_date and not validate_date(args.end_date):
        print(f"Error: Invalid end date format: {args.end_date}")
        print("Expected format: YYYY-MM-DD")
        sys.exit(1)

    # Validate date range if both provided
    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, '%Y-%m-%d')
        end = datetime.strptime(args.end_date, '%Y-%m-%d')
        if start > end:
            print("Error: Start date must be before end date")
            sys.exit(1)

    output_path = Path(args.output)

    # Check cache
    if output_path.exists() and not args.force_fetch:
        print(f"\nCache found at {output_path}")
        print("Use --force-fetch to refresh from API")

        with open(output_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)

        print(f"\nCached data:")
        print(f"  Issues: {len(cached_data['issues'])}")
        print(f"  Fetched: {cached_data['metadata']['fetched_at']}")
        print(f"  Project: {cached_data['metadata']['project']}")
        if cached_data['metadata'].get('start_date'):
            print(f"  Start date: {cached_data['metadata']['start_date']}")
        if cached_data['metadata'].get('end_date'):
            print(f"  End date: {cached_data['metadata']['end_date']}")
        if cached_data['metadata'].get('label'):
            print(f"  Label: {cached_data['metadata']['label']}")

        # Generate report if requested
        if args.report:
            print("\n" + "=" * 60)
            print("GENERATING FLOW REPORT")
            print("=" * 60)

            analyzer = FlowAnalyzer(
                cached_data['issues'],
                start_date=args.start_date,
                end_date=args.end_date
            )
            flow_metrics = analyzer.calculate_flow_metrics()

            print(f"\nFlow Analysis:")
            print(f"  Total bugs analyzed: {flow_metrics.get('total_issues', 0)}")
            print(f"  Total transitions: {flow_metrics['total_transitions']}")
            print(f"  Unique statuses: {flow_metrics['unique_statuses']}")
            print(f"  Flow patterns: {len(flow_metrics['flow_patterns'])}")
            print(f"  Rework loops detected: {flow_metrics.get('loops', {}).get('total_loops', 0)}")
            print(f"  Bugs with loops: {len(flow_metrics.get('loops', {}).get('issues_with_loops', []))}")

            generator = ReportGenerator(cached_data['metadata'], flow_metrics)
            report_path = generator.generate_html(args.report_output)

            print(f"\nReport generated: {report_path}")
            print("=" * 60)

        return

    # Fetch from API
    try:
        print("=" * 60)
        print("JIRA BUG FETCHER")
        print("=" * 60)
        print("Fetching only bugs (type: Bug, \"Błąd w programie\")")
        if args.start_date or args.end_date:
            print(f"Date filtering will be applied during analysis:"
                  f" {args.start_date or 'any'} to {args.end_date or 'any'}")

        fetcher = JiraFetcher()

        issues = fetcher.fetch_issues(
            project=args.project,
            start_date=args.start_date,
            end_date=args.end_date,
            label=args.label,
            batch_size=args.batch_size,
        )

        # Prepare output data
        output_data = {
            'metadata': {
                'project': args.project,
                'start_date': args.start_date,
                'end_date': args.end_date,
                'label': args.label,
                'fetched_at': datetime.now().isoformat(),
                'total_issues': len(issues),
            },
            'issues': issues,
        }

        # Save to file
        print(f"\nSaving {len(issues)} issues to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("FETCH COMPLETE")
        print("=" * 60)
        print(f"Total issues: {len(issues)}")
        print(f"Saved to: {output_path}")
        print("=" * 60)

        # Generate report if requested
        if args.report:
            print("\n" + "=" * 60)
            print("GENERATING FLOW REPORT")
            print("=" * 60)

            analyzer = FlowAnalyzer(
                issues,
                start_date=args.start_date,
                end_date=args.end_date
            )
            flow_metrics = analyzer.calculate_flow_metrics()

            print(f"\nFlow Analysis:")
            print(f"  Total bugs analyzed: {flow_metrics.get('total_issues', 0)}")
            print(f"  Total transitions: {flow_metrics['total_transitions']}")
            print(f"  Unique statuses: {flow_metrics['unique_statuses']}")
            print(f"  Flow patterns: {len(flow_metrics['flow_patterns'])}")
            print(f"  Rework loops detected: {flow_metrics.get('loops', {}).get('total_loops', 0)}")
            print(f"  Bugs with loops: {len(flow_metrics.get('loops', {}).get('issues_with_loops', []))}")

            generator = ReportGenerator(output_data['metadata'], flow_metrics)
            report_path = generator.generate_html(args.report_output)

            print(f"\nReport generated: {report_path}")
            print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
