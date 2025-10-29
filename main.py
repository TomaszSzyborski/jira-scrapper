#!/usr/bin/env python3
"""Main CLI entry point for Jira Bug & Test Scraper."""

import argparse
import sys
from datetime import datetime

from src.jira_scraper.scraper import JiraScraper
from src.jira_scraper.report_generator import ReportGenerator
from src.jira_scraper.cache import DataCache


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Jira Bug & Test Scraper - Generate bug and test execution reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-10-23
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --output bug_report.html
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --label Sprint-1
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --force-fetch
        """
    )

    parser.add_argument(
        "--project",
        "-p",
        required=True,
        help="Jira project key (e.g., PROJ, DEMO)",
    )

    parser.add_argument(
        "--start-date",
        "-s",
        required=True,
        help="Report start date in YYYY-MM-DD format (for filtering in report, not for data fetching)",
    )

    parser.add_argument(
        "--end-date",
        "-e",
        required=True,
        help="Report end date in YYYY-MM-DD format (for filtering in report, not for data fetching)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="jira_report.html",
        help="Output HTML file path (default: jira_report.html)",
    )

    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test Jira connection and exit",
    )

    parser.add_argument(
        "--label",
        "-l",
        help="Filter bugs by label (e.g., 'Sprint-1', 'Release-2.0')",
    )

    parser.add_argument(
        "--test-label",
        "-t",
        help="Filter test executions by label (e.g., 'Sprint-1', 'Release-2.0'). If not specified, uses --label",
    )

    parser.add_argument(
        "--batch-size",
        "-b",
        type=int,
        default=1000,
        help="Number of tickets to fetch per request (default: 1000)",
    )

    parser.add_argument(
        "--force-fetch",
        "-f",
        action="store_true",
        help="Force fetch from Jira even if cached data exists",
    )

    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cached data for this project and exit",
    )

    return parser.parse_args()


def validate_date(date_string: str) -> bool:
    """
    Validate date format.

    Args:
        date_string: Date string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def main():
    """Main execution function."""
    args = parse_arguments()

    # Initialize cache
    cache = DataCache()

    # Handle cache clearing
    if args.clear_cache:
        print(f"Clearing cache for project {args.project}...")
        cache.clear_cache(args.project)
        sys.exit(0)

    # Validate dates
    if not validate_date(args.start_date):
        print(f"Error: Invalid start date format: {args.start_date}")
        print("Expected format: YYYY-MM-DD")
        sys.exit(1)

    if not validate_date(args.end_date):
        print(f"Error: Invalid end date format: {args.end_date}")
        print("Expected format: YYYY-MM-DD")
        sys.exit(1)

    # Validate date range
    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    if start > end:
        print("Error: Start date must be before end date")
        sys.exit(1)

    try:
        # Initialize scraper
        print("Initializing Jira connection...")
        scraper = JiraScraper()

        # Test connection if requested
        if args.test_connection:
            if scraper.test_connection():
                print("Connection test successful!")
                sys.exit(0)
            else:
                print("Connection test failed!")
                sys.exit(1)

        # Fetch project info
        print(f"\nFetching project info for {args.project}...")
        project_info = scraper.get_project_info(args.project)
        print(f"Project: {project_info['name']}")
        print(f"Lead: {project_info.get('lead', 'N/A')}")

        # Fetch or load bugs
        bugs = None
        if not args.force_fetch and cache.exists(args.project, "bugs", args.label):
            print(f"\n[1/2] Loading bugs from cache...")
            bugs = cache.load(args.project, "bugs", args.label)

        if bugs is None or args.force_fetch:
            if args.label:
                print(f"\n[1/2] Fetching ALL bugs from Jira with label '{args.label}'...")
            else:
                print(f"\n[1/2] Fetching ALL bugs from Jira...")

            bugs = scraper.get_bugs(
                project_key=args.project,
                label=args.label,
                batch_size=args.batch_size,
            )

            # Save to cache
            cache.save(args.project, "bugs", bugs, args.label)

        print(f"Total bugs available: {len(bugs)}")

        # Fetch or load test executions
        test_label = args.test_label if args.test_label else args.label
        test_executions = None

        if not args.force_fetch and cache.exists(args.project, "test_executions", test_label):
            print(f"\n[2/2] Loading test executions from cache...")
            test_executions = cache.load(args.project, "test_executions", test_label)

        if test_executions is None or args.force_fetch:
            if test_label:
                print(f"\n[2/2] Fetching ALL test executions from Jira with label '{test_label}'...")
            else:
                print(f"\n[2/2] Fetching ALL test executions from Jira...")

            test_executions = scraper.get_test_executions(
                project_key=args.project,
                target_label=test_label,
                batch_size=args.batch_size,
            )

            # Save to cache
            cache.save(args.project, "test_executions", test_executions, test_label)

        print(f"Total test executions available: {len(test_executions)}")

        # Generate report
        print(f"\nGenerating HTML report for date range {args.start_date} to {args.end_date}...")
        report_gen = ReportGenerator(
            project_name=args.project,
            start_date=args.start_date,
            end_date=args.end_date,
            jira_url=scraper.jira_url,
        )

        output_path = report_gen.generate_html_report(
            bugs=bugs,
            test_executions=test_executions,
            test_label=test_label,
            output_file=args.output,
        )

        # Summary
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Total bugs: {len(bugs)}")
        print(f"Total test executions: {len(test_executions)}")
        print(f"Date range filtered in report: {args.start_date} to {args.end_date}")
        print(f"\nReport saved to: {output_path}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
