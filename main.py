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
        Build JQL query with optional date and label filters.

        Args:
            project: Jira project key (e.g., 'PROJ')
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            label: Optional label to filter by

        Returns:
            JQL query string
        """
        jql_parts = [f"project = {project}"]

        if start_date:
            jql_parts.append(f"created >= '{start_date}'")

        if end_date:
            jql_parts.append(f"created <= '{end_date}'")

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

    def __init__(self, issues: list):
        """
        Initialize flow analyzer with issues.

        Args:
            issues: List of issue dictionaries
        """
        self.issues = issues

    def build_transitions_dataframe(self) -> pl.DataFrame:
        """
        Build a Polars DataFrame of all status transitions.

        Returns:
            DataFrame with columns: issue_key, from_status, to_status, transition_date, author
        """
        transitions = []

        for issue in self.issues:
            issue_key = issue['key']
            current_status = issue['status']
            changelog = issue.get('changelog', [])

            # If there's no changelog, the issue was created and stayed in current status
            if not changelog:
                # Initial creation (no from_status)
                transitions.append({
                    'issue_key': issue_key,
                    'from_status': None,
                    'to_status': current_status,
                    'transition_date': issue['created'],
                    'author': issue['reporter'],
                })
            else:
                # Process all status transitions
                for change in changelog:
                    transitions.append({
                        'issue_key': issue_key,
                        'from_status': change['from_string'],
                        'to_status': change['to_string'],
                        'transition_date': change['created'],
                        'author': change['author'],
                    })

        df = pl.DataFrame(transitions)
        return df

    def calculate_flow_metrics(self) -> dict:
        """
        Calculate flow metrics from transitions.

        Returns:
            Dictionary with flow statistics
        """
        df = self.build_transitions_dataframe()

        if df.is_empty():
            return {
                'total_transitions': 0,
                'unique_statuses': 0,
                'flow_patterns': [],
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

        return {
            'total_transitions': len(df),
            'unique_statuses': len(all_statuses),
            'flow_patterns': flow_patterns,
            'all_statuses': sorted(all_statuses),
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

    def generate_html(self, output_file: str = 'jira_flow_report.html'):
        """
        Generate HTML report with Sankey diagram.

        Args:
            output_file: Output HTML file path

        Returns:
            Path to generated report
        """
        # Prepare data for Sankey diagram
        flow_patterns = self.flow_metrics['flow_patterns']
        all_statuses = self.flow_metrics['all_statuses']

        # Build node and link data for Sankey
        # Nodes are statuses, links are transitions
        node_labels = all_statuses
        node_dict = {status: idx for idx, status in enumerate(node_labels)}

        sources = []
        targets = []
        values = []
        link_labels = []

        for pattern in flow_patterns:
            from_status = pattern['from']
            to_status = pattern['to']
            count = pattern['count']

            sources.append(node_dict[from_status])
            targets.append(node_dict[to_status])
            values.append(count)
            link_labels.append(f"{from_status} → {to_status}: {count}")

        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jira Flow Report - {self.metadata['project']}</title>
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
            max-width: 1400px;
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
        .metadata {{
            color: #718096;
            font-size: 0.95em;
            line-height: 1.6;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .stat-label {{
            color: #718096;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }}
        .stat-value {{
            color: #2d3748;
            font-size: 2.5em;
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
            font-size: 1.5em;
            margin-bottom: 20px;
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
            <h1>Jira Flow Report</h1>
            <div class="metadata">
                <strong>Project:</strong> {self.metadata['project']}<br>
                <strong>Fetched:</strong> {self.metadata.get('fetched_at', 'N/A')}<br>
                <strong>Total Issues:</strong> {self.metadata.get('total_issues', 0)}
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Transitions</div>
                <div class="stat-value">{self.flow_metrics['total_transitions']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Unique Statuses</div>
                <div class="stat-value">{self.flow_metrics['unique_statuses']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Flow Patterns</div>
                <div class="stat-value">{len(flow_patterns)}</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">Status Flow Diagram (Sankey)</div>
            <div id="sankey-chart"></div>
        </div>

        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Jira Flow Analyzer
        </div>
    </div>

    <script>
        // Sankey diagram data
        const data = [{{
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
                label: {json.dumps(link_labels)}
            }}
        }}];

        const layout = {{
            font: {{
                size: 12,
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }},
            height: 600,
            margin: {{
                l: 20,
                r: 20,
                t: 20,
                b: 20
            }}
        }};

        const config = {{
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        }};

        Plotly.newPlot('sankey-chart', data, layout, config);
    </script>
</body>
</html>
"""

        # Write to file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Fetch Jira issues, analyze flows, and generate reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all issues from project PROJ
  %(prog)s --project PROJ

  # Fetch with date range
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-12-31

  # Fetch with label
  %(prog)s --project PROJ --label Sprint-1

  # Fetch with all filters and force refresh
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-12-31 --label Sprint-1 --force-fetch

  # Generate flow report from cached data
  %(prog)s --project PROJ --report

  # Fetch and generate report in one go
  %(prog)s --project PROJ --force-fetch --report
        """
    )

    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Jira project key (e.g., PROJ, DEMO)'
    )

    parser.add_argument(
        '--start-date', '-s',
        help='Start date in YYYY-MM-DD format (optional)'
    )

    parser.add_argument(
        '--end-date', '-e',
        help='End date in YYYY-MM-DD format (optional)'
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

            analyzer = FlowAnalyzer(cached_data['issues'])
            flow_metrics = analyzer.calculate_flow_metrics()

            print(f"\nFlow Analysis:")
            print(f"  Total transitions: {flow_metrics['total_transitions']}")
            print(f"  Unique statuses: {flow_metrics['unique_statuses']}")
            print(f"  Flow patterns: {len(flow_metrics['flow_patterns'])}")

            generator = ReportGenerator(cached_data['metadata'], flow_metrics)
            report_path = generator.generate_html(args.report_output)

            print(f"\nReport generated: {report_path}")
            print("=" * 60)

        return

    # Fetch from API
    try:
        print("=" * 60)
        print("JIRA ISSUE FETCHER")
        print("=" * 60)

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

            analyzer = FlowAnalyzer(issues)
            flow_metrics = analyzer.calculate_flow_metrics()

            print(f"\nFlow Analysis:")
            print(f"  Total transitions: {flow_metrics['total_transitions']}")
            print(f"  Unique statuses: {flow_metrics['unique_statuses']}")
            print(f"  Flow patterns: {len(flow_metrics['flow_patterns'])}")

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
