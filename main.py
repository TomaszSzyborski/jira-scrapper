#!/usr/bin/env python3
"""Main CLI entry point for Jira Scraper & Analytics."""

import argparse
import sys
from datetime import datetime

from src.jira_scraper.scraper import JiraScraper
from src.jira_scraper.analyzer import JiraAnalyzer
from src.jira_scraper.report_generator import ReportGenerator


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Jira Scraper & Analytics - Generate comprehensive reports from Jira data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-10-23
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --granularity weekly
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --output custom_report.html
  %(prog)s --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --test-label Sprint-1
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
        help="Start date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--end-date",
        "-e",
        required=True,
        help="End date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--granularity",
        "-g",
        choices=["daily", "weekly"],
        default="daily",
        help="Temporal trend granularity (default: daily)",
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
        "--test-label",
        "-t",
        help="Filter test executions by label (e.g., 'Sprint-1', 'Release-2.0')",
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

        # Fetch tickets
        print(f"\nFetching tickets from {args.start_date} to {args.end_date}...")
        tickets = scraper.get_project_tickets(
            project_key=args.project,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size,
        )

        if not tickets:
            print("No tickets found for the specified criteria.")
            sys.exit(0)

        # Analyze data
        print(f"\nAnalyzing {len(tickets)} tickets...")
        analyzer = JiraAnalyzer(tickets, jira_url=scraper.jira_url)
        analyzer.build_dataframes()

        print("Calculating metrics...")
        summary_stats = analyzer.get_summary_statistics()
        flow_metrics = analyzer.calculate_flow_metrics()
        cycle_metrics = analyzer.calculate_cycle_metrics()
        temporal_trends = analyzer.calculate_temporal_trends(
            start_date=args.start_date,
            end_date=args.end_date,
            granularity=args.granularity,
        )

        # Generate report
        print(f"\nGenerating HTML report...")
        report_gen = ReportGenerator(
            project_name=args.project,
            start_date=args.start_date,
            end_date=args.end_date,
            jira_url=scraper.jira_url,
        )

        output_path = report_gen.generate_html_report(
            summary_stats=summary_stats,
            flow_metrics=flow_metrics,
            cycle_metrics=cycle_metrics,
            temporal_trends=temporal_trends,
            tickets=tickets,
            test_label=args.test_label,
            output_file=args.output,
        )

        # Summary
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Total tickets analyzed: {summary_stats['total_tickets']}")
        print(f"Resolved tickets: {summary_stats['resolved_tickets']}")
        print(f"Average lead time: {cycle_metrics['avg_lead_time']:.2f} days")
        print(f"Average cycle time: {cycle_metrics['avg_cycle_time']:.2f} days")
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
