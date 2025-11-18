#!/usr/bin/env python3
"""
Xray Test Execution Reporter - Standalone CLI Entry Point.

This script fetches test execution data from Xray for Jira and generates
comprehensive HTML reports with test metrics and visualizations.

Usage:
    # Generate test execution report for a project
    python xray_main.py --project PROJ --report

    # Generate report for specific date range
    python xray_main.py --project PROJ --start-date 2024-01-01 --end-date 2024-12-31 --report

    # Generate report for specific test plan
    python xray_main.py --project PROJ --test-plan PROJ-123 --report

Example:
    >>> python xray_main.py --project MYPROJ --start-date 2024-01-01 --report
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from jira_analyzer.xray_fetcher import XrayFetcher
from jira_analyzer.xray_analyzer import XrayAnalyzer
from jira_analyzer.xray_reporter import XrayReportGenerator


def parse_args():
    """
    Parse command line arguments.

    Returns:
        Namespace object with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Fetch Xray test executions and generate comprehensive reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate test execution report for project
  %(prog)s --project PROJ --report

  # Generate report for specific date range
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-12-31 --report

  # Generate report for specific test plan
  %(prog)s --project PROJ --test-plan PROJ-123 --report

  # Fetch and cache test executions without generating report
  %(prog)s --project PROJ

  # Generate report from cached data
  %(prog)s --project PROJ --report

Note:
  - Requires Jira credentials in .env file (JIRA_URL, JIRA_USERNAME, JIRA_PASSWORD)
  - Xray must be installed in your Jira instance
  - Reports include: pass/fail rates, test trends, duration statistics
        """
    )

    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Jira project key (e.g., PROJ, DEMO)'
    )

    parser.add_argument(
        '--start-date', '-s',
        help='Start date for test executions in YYYY-MM-DD format'
    )

    parser.add_argument(
        '--end-date', '-e',
        help='End date for test executions in YYYY-MM-DD format'
    )

    parser.add_argument(
        '--test-plan', '-t',
        help='Test Plan key (e.g., PROJ-123) to filter executions'
    )

    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=100,
        help='Number of issues to fetch per request (default: 100)'
    )

    parser.add_argument(
        '--output', '-o',
        default='xray_test_executions.json',
        help='Output file path for cached data (default: xray_test_executions.json)'
    )

    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='Generate HTML test execution report'
    )

    parser.add_argument(
        '--report-output',
        default='xray_test_report.html',
        help='HTML report output file (default: xray_test_report.html)'
    )

    parser.add_argument(
        '--force-fetch', '-f',
        action='store_true',
        help='Force fetch from Jira API, ignore cache'
    )

    return parser.parse_args()


def main():
    """
    Main entry point for Xray Test Execution Reporter.

    Orchestrates the workflow:
    1. Parse and validate CLI arguments
    2. Check for cached data or fetch from Xray API
    3. Optionally analyze and generate HTML report

    Exits:
        0: Success
        1: Error (invalid arguments, API error, etc.)
    """
    args = parse_args()

    output_path = Path(args.output)

    # Check cache
    if output_path.exists() and not args.force_fetch:
        print(f"\nCache found at {output_path}")
        print("Use --force-fetch to refresh from API")

        with open(output_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)

        print(f"\nCached data:")
        print(f"  Test executions: {len(cached_data['executions'])}")
        print(f"  Fetched: {cached_data['metadata']['fetched_at']}")
        print(f"  Project: {cached_data['metadata']['project']}")

        # Generate report if requested
        if args.report:
            print("\n" + "=" * 60)
            print("GENERATING TEST EXECUTION REPORT")
            print("=" * 60)

            analyzer = XrayAnalyzer(
                cached_data['executions'],
                start_date=args.start_date,
                end_date=args.end_date
            )
            test_metrics = analyzer.calculate_test_metrics()

            print(f"\nTest Execution Metrics:")
            print(f"  Total executions: {test_metrics.get('total_executions', 0)}")
            print(f"  Total test runs: {test_metrics.get('total_test_runs', 0)}")
            print(f"  Passed: {test_metrics.get('pass_count', 0)} ({test_metrics.get('pass_rate', 0):.1f}%)")
            print(f"  Failed: {test_metrics.get('fail_count', 0)} ({test_metrics.get('fail_rate', 0):.1f}%)")
            print(f"  Other: {test_metrics.get('other_count', 0)}")
            print(f"  Defects found: {len(test_metrics.get('defects_found', []))}")

            report_metadata = {
                'project': cached_data['metadata']['project'],
                'fetched_at': cached_data['metadata']['fetched_at']
            }

            generator = XrayReportGenerator(
                report_metadata,
                test_metrics,
                jira_url=os.getenv('JIRA_URL')
            )
            report_path = generator.generate_html(args.report_output)

            print(f"\nReport generated: {report_path}")
            print("=" * 60)

        return

    # Fetch from API
    try:
        print("=" * 60)
        print("XRAY TEST EXECUTION FETCHER")
        print("=" * 60)
        print(f"Project: {args.project}")
        if args.start_date:
            print(f"Start date: {args.start_date}")
        if args.end_date:
            print(f"End date: {args.end_date}")
        if args.test_plan:
            print(f"Test plan: {args.test_plan}")

        fetcher = XrayFetcher()

        executions = fetcher.fetch_test_executions(
            project=args.project,
            start_date=args.start_date,
            end_date=args.end_date,
            test_plan=args.test_plan,
            batch_size=args.batch_size
        )

        # Prepare output data
        output_data = {
            'metadata': {
                'project': args.project,
                'start_date': args.start_date,
                'end_date': args.end_date,
                'test_plan': args.test_plan,
                'fetched_at': datetime.now().isoformat(),
                'total_executions': len(executions),
            },
            'executions': executions,
        }

        # Save to file
        print(f"\nSaving {len(executions)} test executions to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("FETCH COMPLETE")
        print("=" * 60)
        print(f"Total test executions: {len(executions)}")
        print(f"Saved to: {output_path}")
        print("=" * 60)

        # Generate report if requested
        if args.report:
            print("\n" + "=" * 60)
            print("GENERATING TEST EXECUTION REPORT")
            print("=" * 60)

            analyzer = XrayAnalyzer(
                executions,
                start_date=args.start_date,
                end_date=args.end_date
            )
            test_metrics = analyzer.calculate_test_metrics()

            print(f"\nTest Execution Metrics:")
            print(f"  Total executions: {test_metrics.get('total_executions', 0)}")
            print(f"  Total test runs: {test_metrics.get('total_test_runs', 0)}")
            print(f"  Passed: {test_metrics.get('pass_count', 0)} ({test_metrics.get('pass_rate', 0):.1f}%)")
            print(f"  Failed: {test_metrics.get('fail_count', 0)} ({test_metrics.get('fail_rate', 0):.1f}%)")
            print(f"  Other: {test_metrics.get('other_count', 0)}")
            print(f"  Defects found: {len(test_metrics.get('defects_found', []))}")

            report_metadata = {
                'project': output_data['metadata']['project'],
                'fetched_at': output_data['metadata']['fetched_at']
            }

            generator = XrayReportGenerator(
                report_metadata,
                test_metrics,
                jira_url=fetcher.jira_url
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
