#!/usr/bin/env python3
"""
Jira Bug Flow Analyzer - Main CLI Entry Point.

This is the main command-line interface for the Jira Bug Flow Analyzer.
It provides a simple interface for fetching bugs from Jira, analyzing their
workflow patterns, and generating comprehensive HTML reports.

Usage:
    # Fetch all bugs from project
    python main.py --project PROJ

    # Fetch bugs and analyze with date range
    python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31 --report

    # Generate report from cached data
    python main.py --project PROJ --report

Example:
    >>> python main.py --project MYPROJ --force-fetch --report
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from jira_analyzer import JiraFetcher, FlowAnalyzer, ReportGenerator


def parse_args():
    """
    Parse command line arguments.

    Returns:
        Namespace object with parsed arguments

    Arguments:
        --project, -p: Jira project key (required)
        --start-date, -s: Start date for analysis (optional, YYYY-MM-DD)
        --end-date, -e: End date for analysis (optional, YYYY-MM-DD)
        --label, -l: Filter by label (optional)
        --force-fetch, -f: Force fetch from API, ignore cache
        --batch-size, -b: Number of issues per request (default: 100)
        --output, -o: Output file path (default: jira_cached.json)
        --report, -r: Generate HTML flow report
        --report-output: HTML report output file (default: jira_flow_report.html)
    """
    parser = argparse.ArgumentParser(
        description='Fetch Jira issues, analyze flows with rework detection, and generate comprehensive reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all bugs from project PROJ (default)
  %(prog)s --project PROJ

  # Fetch stories and generate flow report
  %(prog)s --project PROJ --issue-types Story --report

  # Fetch multiple issue types
  %(prog)s --project PROJ --issue-types Bug Story Task --report

  # Fetch issues and analyze with date range (filtering done in Python)
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-12-31 --report

  # Fetch issues with label
  %(prog)s --project PROJ --label Sprint-1

  # Generate report from cached issues with date filtering
  %(prog)s --project PROJ --start-date 2024-06-01 --end-date 2024-12-31 --report

Note:
  - By default, only bugs (type: Bug, "Błąd w programie") are fetched
  - Use --issue-types to fetch other issue types (Story, Task, etc.)
  - Date filtering is applied during analysis in Python, not in JQL
  - Reports include: timeline trends, loop detection, time in status, flow diagrams
  - Report filenames are based on issue types (e.g., story_flow_report.html)
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
        '--issue-types', '-t',
        nargs='+',
        help='Issue types to fetch (e.g., Bug Story Task). Default: Bug'
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

    parser.add_argument(
        '--incremental', '-i',
        action='store_true',
        help='Incremental fetch: only fetch issues created/updated since last fetch (uses cache timestamp)'
    )

    parser.add_argument(
        '--current-snapshot',
        action='store_true',
        help='Fetch current state snapshot (statusCategory != Done) and add to report'
    )

    return parser.parse_args()


def validate_date(date_string: str) -> bool:
    """
    Validate date format YYYY-MM-DD.

    Args:
        date_string: Date string to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_date('2024-01-01')
        True
        >>> validate_date('2024-13-01')
        False
    """
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def merge_issues(existing_issues: list, new_issues: list) -> list:
    """
    Merge new/updated issues with existing cached issues.

    Creates a dictionary keyed by issue ID, with new issues overwriting
    existing ones if they have been updated.

    Args:
        existing_issues: List of issues from cache
        new_issues: List of newly fetched issues

    Returns:
        Merged list of issues (new issues override old ones)

    Example:
        >>> existing = [{'key': 'PROJ-1', 'id': '1', 'updated': '2024-01-01'}]
        >>> new = [{'key': 'PROJ-1', 'id': '1', 'updated': '2024-01-02'}]
        >>> merged = merge_issues(existing, new)
        >>> len(merged)
        1
        >>> merged[0]['updated']
        '2024-01-02'
    """
    # Create dict keyed by issue ID
    issue_dict = {issue['id']: issue for issue in existing_issues}

    # Update with new/updated issues
    for issue in new_issues:
        issue_dict[issue['id']] = issue

    # Return as list, sorted by created date
    return sorted(issue_dict.values(), key=lambda x: x.get('created', ''))


def get_last_update_date(issues: list) -> str:
    """
    Get the most recent updated date from a list of issues.

    Args:
        issues: List of issue dictionaries

    Returns:
        ISO date string (YYYY-MM-DD) of the most recent update,
        or None if no issues

    Example:
        >>> issues = [
        ...     {'updated': '2024-01-01T10:00:00.000+0000'},
        ...     {'updated': '2024-01-05T15:30:00.000+0000'}
        ... ]
        >>> get_last_update_date(issues)
        '2024-01-05'
    """
    if not issues:
        return None

    # Get all update dates and find the max
    update_dates = [issue.get('updated', '') for issue in issues if issue.get('updated')]

    if not update_dates:
        return None

    # Take the date part only (YYYY-MM-DD)
    max_date = max(update_dates)
    return max_date[:10] if max_date else None


def main():
    """
    Main entry point for the Jira Bug Flow Analyzer.

    This function orchestrates the entire workflow:
    1. Parse and validate CLI arguments
    2. Check for cached data or fetch from Jira API
    3. Optionally analyze flows and generate HTML report

    Exits:
        0: Success
        1: Error (invalid arguments, API error, etc.)
    """
    args = parse_args()

    # Set default issue types if not provided
    if not args.issue_types:
        args.issue_types = ['Bug', 'Błąd w programie']
        issue_type_label = 'bug'
    else:
        # Create label from issue types for file naming
        issue_type_label = '_'.join([t.lower().replace(' ', '_') for t in args.issue_types])

    # Update default filenames based on issue type
    if args.output == 'jira_cached.json':
        args.output = f'jira_{issue_type_label}_cached.json'

    if args.report_output == 'jira_flow_report.html':
        args.report_output = f'{issue_type_label}_flow_report.html'

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

        # INCREMENTAL FETCH: Fetch only new/updated issues since last fetch
        if args.incremental:
            print("\n" + "=" * 60)
            print("INCREMENTAL FETCH MODE")
            print("=" * 60)

            # Get the most recent update date from cached issues
            last_update = get_last_update_date(cached_data['issues'])

            if last_update:
                print(f"Last cached update: {last_update}")
                print(f"Fetching issues created/updated since {last_update}...")

                try:
                    fetcher = JiraFetcher()

                    # Fetch only new/updated issues
                    new_issues = fetcher.fetch_issues(
                        project=args.project,
                        start_date=last_update,
                        end_date=None,
                        batch_size=args.batch_size,
                        issue_types=args.issue_types,
                        incremental=True  # Use incremental JQL
                    )

                    print(f"\nFetched {len(new_issues)} new/updated issues")

                    # Merge with cached issues
                    merged_issues = merge_issues(cached_data['issues'], new_issues)

                    print(f"Total issues after merge: {len(merged_issues)}")

                    # Update cached data
                    cached_data['issues'] = merged_issues
                    cached_data['metadata']['fetched_at'] = datetime.now().isoformat()
                    cached_data['metadata']['last_incremental_fetch'] = datetime.now().isoformat()
                    cached_data['metadata']['total_issues'] = len(merged_issues)

                    # Save updated cache
                    print(f"\nUpdating cache at {output_path}...")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(cached_data, f, indent=2, ensure_ascii=False)

                    print("Cache updated successfully!")
                    print("=" * 60)

                except Exception as e:
                    print(f"\nIncremental fetch failed: {e}")
                    print("Using cached data as-is")
            else:
                print("\nNo update date found in cache, skipping incremental fetch")
                print("Use --force-fetch for a full refresh")
        else:
            print("Use --force-fetch to refresh from API or --incremental for delta fetch")

        # Generate report if requested
        if args.report:
            print("\n" + "=" * 60)
            print("GENERATING FLOW REPORT")
            print("=" * 60)

            analyzer = FlowAnalyzer(
                cached_data['issues'],
                start_date=args.start_date,
                end_date=args.end_date,
                label=args.label
            )
            flow_metrics = analyzer.calculate_flow_metrics()

            print(f"\nFlow Analysis (with label filter):")
            print(f"  Total bugs analyzed: {flow_metrics.get('total_issues', 0)}")
            print(f"  Total transitions: {flow_metrics['total_transitions']}")
            print(f"  Unique statuses: {flow_metrics['unique_statuses']}")
            print(f"  Flow patterns: {len(flow_metrics['flow_patterns'])}")
            print(f"  Rework loops detected: {flow_metrics.get('loops', {}).get('total_loops', 0)}")
            print(f"  Bugs with loops: {len(flow_metrics.get('loops', {}).get('issues_with_loops', []))}")

            # If label filter is active, also calculate metrics without label for comparison
            flow_metrics_no_label = None
            if args.label:
                print(f"\nCalculating metrics without label filter for comparison...")
                analyzer_no_label = FlowAnalyzer(
                    cached_data['issues'],
                    start_date=args.start_date,
                    end_date=args.end_date,
                    label=None  # No label filter
                )
                flow_metrics_no_label = analyzer_no_label.calculate_flow_metrics()
                print(f"  Total bugs (no label filter): {flow_metrics_no_label.get('total_issues', 0)}")

            # Fetch current state snapshot if requested
            current_snapshot = None
            if args.current_snapshot:
                print(f"\n" + "=" * 60)
                print("FETCHING CURRENT STATE SNAPSHOT")
                print("=" * 60)

                try:
                    fetcher = JiraFetcher()
                    current_snapshot = fetcher.fetch_current_snapshot(
                        project=args.project,
                        issue_types=args.issue_types,
                        label=args.label
                    )

                    total_open = sum(len(issues) for issues in current_snapshot.values())
                    print(f"\nCurrent state summary (statusCategory != Done):")
                    for issue_type, issues in current_snapshot.items():
                        print(f"  {issue_type}: {len(issues)} open")
                    print(f"  Total open issues: {total_open}")
                    print("=" * 60)

                except Exception as e:
                    print(f"\nCurrent snapshot fetch failed: {e}")
                    print("Continuing without snapshot...")

            # Create simplified metadata (only project and fetched_at from cache)
            report_metadata = {
                'project': cached_data['metadata']['project'],
                'fetched_at': cached_data['metadata']['fetched_at']
            }
            generator = ReportGenerator(
                report_metadata,
                flow_metrics,
                start_date=args.start_date,
                end_date=args.end_date,
                jira_url=os.getenv('JIRA_URL'),
                label=args.label,
                flow_metrics_no_label=flow_metrics_no_label,
                all_issues=cached_data['issues'],  # Pass all issues for interactive filtering
                current_snapshot=current_snapshot  # Pass current state snapshot
            )
            report_path = generator.generate_html(args.report_output)

            print(f"\nReport generated: {report_path}")
            print("=" * 60)

        return

    # Fetch from API
    try:
        print("=" * 60)
        print("JIRA ISSUE FETCHER")
        print("=" * 60)
        print(f"Fetching issue types: {', '.join(args.issue_types)}")
        if args.start_date or args.end_date:
            print(f"Date filtering will be applied during analysis:"
                  f" {args.start_date or 'any'} to {args.end_date or 'any'}")

        fetcher = JiraFetcher()

        issues = fetcher.fetch_issues(
            project=args.project,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size,
            issue_types=args.issue_types,
        )

        # Prepare output data
        output_data = {
            'metadata': {
                'project': args.project,
                'start_date': args.start_date,
                'end_date': args.end_date,
                'label': args.label,
                'issue_types': args.issue_types,
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
                end_date=args.end_date,
                label=args.label
            )
            flow_metrics = analyzer.calculate_flow_metrics()

            print(f"\nFlow Analysis (with label filter):")
            print(f"  Total bugs analyzed: {flow_metrics.get('total_issues', 0)}")
            print(f"  Total transitions: {flow_metrics['total_transitions']}")
            print(f"  Unique statuses: {flow_metrics['unique_statuses']}")
            print(f"  Flow patterns: {len(flow_metrics['flow_patterns'])}")
            print(f"  Rework loops detected: {flow_metrics.get('loops', {}).get('total_loops', 0)}")
            print(f"  Bugs with loops: {len(flow_metrics.get('loops', {}).get('issues_with_loops', []))}")

            # If label filter is active, also calculate metrics without label for comparison
            flow_metrics_no_label = None
            if args.label:
                print(f"\nCalculating metrics without label filter for comparison...")
                analyzer_no_label = FlowAnalyzer(
                    issues,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    label=None  # No label filter
                )
                flow_metrics_no_label = analyzer_no_label.calculate_flow_metrics()
                print(f"  Total bugs (no label filter): {flow_metrics_no_label.get('total_issues', 0)}")

            # Fetch current state snapshot if requested
            current_snapshot = None
            if args.current_snapshot:
                print(f"\n" + "=" * 60)
                print("FETCHING CURRENT STATE SNAPSHOT")
                print("=" * 60)

                try:
                    current_snapshot = fetcher.fetch_current_snapshot(
                        project=args.project,
                        issue_types=args.issue_types,
                        label=args.label
                    )

                    total_open = sum(len(issues_list) for issues_list in current_snapshot.values())
                    print(f"\nCurrent state summary (statusCategory != Done):")
                    for issue_type, issues_list in current_snapshot.items():
                        print(f"  {issue_type}: {len(issues_list)} open")
                    print(f"  Total open issues: {total_open}")
                    print("=" * 60)

                except Exception as e:
                    print(f"\nCurrent snapshot fetch failed: {e}")
                    print("Continuing without snapshot...")

            # Create simplified metadata (only project and fetched_at, not dates)
            report_metadata = {
                'project': output_data['metadata']['project'],
                'fetched_at': output_data['metadata']['fetched_at']
            }
            generator = ReportGenerator(
                report_metadata,
                flow_metrics,
                start_date=args.start_date,
                end_date=args.end_date,
                jira_url=fetcher.jira_url,
                label=args.label,
                flow_metrics_no_label=flow_metrics_no_label,
                all_issues=issues,  # Pass all issues for interactive filtering
                current_snapshot=current_snapshot  # Pass current state snapshot
            )
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
