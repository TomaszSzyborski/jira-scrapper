#!/usr/bin/env python3
"""
Bitbucket Repository Analyzer - Standalone CLI

This script fetches repository data from Bitbucket Server/Data Center
and generates comprehensive analysis reports.

Usage:
    python bitbucket_main.py --project PROJ --repository myrepo --report

Example:
    # Generate full repository report
    python bitbucket_main.py --project PROJ --repository myrepo --report

    # Filter by user emails
    python bitbucket_main.py --project PROJ --repository myrepo --user-emails user1@example.com,user2@example.com --report

    # Filter by date range
    python bitbucket_main.py --project PROJ --repository myrepo --start-date 2024-01-01 --end-date 2024-12-31 --report
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from jira_analyzer.bitbucket_fetcher import BitbucketFetcher
from jira_analyzer.bitbucket_analyzer import BitbucketAnalyzer
from jira_analyzer.bitbucket_reporter import BitbucketReportGenerator


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Bitbucket Repository Analyzer - Generate repository analysis reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate repository report
  %(prog)s --project PROJ --repository myrepo --report

  # Filter by specific users
  %(prog)s --project PROJ --repository myrepo --user-emails user1@example.com,user2@example.com --report

  # Generate report for date range
  %(prog)s --project PROJ --repository myrepo --start-date 2024-01-01 --end-date 2024-12-31 --report

  # Include pull requests
  %(prog)s --project PROJ --repository myrepo --fetch-prs --report
        """
    )

    parser.add_argument(
        '--project',
        required=True,
        help='Bitbucket project key (e.g., PROJ)'
    )

    parser.add_argument(
        '--repository',
        required=True,
        help='Repository slug (e.g., my-repo)'
    )

    parser.add_argument(
        '--start-date',
        help='Start date for filtering commits (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        help='End date for filtering commits (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--user-emails',
        help='Comma-separated list of user emails to filter by'
    )

    parser.add_argument(
        '--user-names',
        help='Comma-separated list of usernames to filter by'
    )

    parser.add_argument(
        '--fetch-prs',
        action='store_true',
        help='Fetch and analyze pull requests (default: False)'
    )

    parser.add_argument(
        '--pr-state',
        choices=['ALL', 'OPEN', 'MERGED', 'DECLINED'],
        default='ALL',
        help='Pull request state filter (default: ALL)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of items to fetch per request (default: 100)'
    )

    parser.add_argument(
        '--output',
        default='bitbucket_data.json',
        help='Cache file path (default: bitbucket_data.json)'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate HTML report'
    )

    parser.add_argument(
        '--report-output',
        default='bitbucket_report.html',
        help='HTML report output path (default: bitbucket_report.html)'
    )

    parser.add_argument(
        '--force-fetch',
        action='store_true',
        help='Force fetch from Bitbucket, ignore cache'
    )

    return parser.parse_args()


def load_cached_data(cache_file: str) -> dict:
    """
    Load cached repository data from file.

    Args:
        cache_file: Path to cache file

    Returns:
        Cached data dictionary or None if not found
    """
    cache_path = Path(cache_file)
    if cache_path.exists():
        print(f"Loading cached data from {cache_file}...")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_cached_data(data: dict, cache_file: str):
    """
    Save repository data to cache file.

    Args:
        data: Data dictionary to cache
        cache_file: Path to cache file
    """
    print(f"Saving data to cache: {cache_file}")
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def main():
    """Main execution function."""
    args = parse_arguments()

    print("=" * 80)
    print("Bitbucket Repository Analyzer")
    print("=" * 80)

    # Parse user filters
    user_emails = None
    user_names = None
    if args.user_emails:
        user_emails = [email.strip() for email in args.user_emails.split(',')]
        print(f"Filtering by user emails: {user_emails}")

    if args.user_names:
        user_names = [name.strip() for name in args.user_names.split(',')]
        print(f"Filtering by usernames: {user_names}")

    # Check for cached data
    cached_data = None
    if not args.force_fetch:
        cached_data = load_cached_data(args.output)

    # Fetch or use cached data
    if cached_data:
        print("Using cached repository data")
        commits = cached_data.get('commits', [])
        pull_requests = cached_data.get('pull_requests', [])
        repo_info = cached_data.get('repository_info', {})
    else:
        print("\nFetching repository data from Bitbucket...")

        try:
            fetcher = BitbucketFetcher()

            # Fetch repository info
            print("\nFetching repository information...")
            repo_info = fetcher.fetch_repository_info(args.project, args.repository)
            print(f"Repository: {repo_info.get('name', 'N/A')}")
            print(f"Description: {repo_info.get('description', 'N/A')}")

            # Fetch commits
            commits = fetcher.fetch_commits(
                project=args.project,
                repository=args.repository,
                start_date=args.start_date,
                end_date=args.end_date,
                user_emails=user_emails,
                user_names=user_names,
                batch_size=args.batch_size
            )

            # Fetch pull requests if requested
            pull_requests = []
            if args.fetch_prs:
                pull_requests = fetcher.fetch_pull_requests(
                    project=args.project,
                    repository=args.repository,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    state=args.pr_state,
                    batch_size=args.batch_size
                )

            # Cache the data
            cache_data = {
                'commits': commits,
                'pull_requests': pull_requests,
                'repository_info': repo_info,
                'metadata': {
                    'project': args.project,
                    'repository': args.repository,
                    'fetched_at': datetime.now().isoformat(),
                    'start_date': args.start_date,
                    'end_date': args.end_date,
                    'user_emails': user_emails,
                    'user_names': user_names,
                }
            }
            save_cached_data(cache_data, args.output)

        except Exception as e:
            print(f"\n❌ Error fetching repository data: {e}")
            sys.exit(1)

    # Analyze the data
    print("\n" + "=" * 80)
    print("Analyzing repository data...")
    print("=" * 80)

    analyzer = BitbucketAnalyzer(
        commits=commits,
        pull_requests=pull_requests,
        start_date=args.start_date,
        end_date=args.end_date
    )

    metrics = analyzer.calculate_metrics()

    # Print summary
    print(f"\n📊 Summary:")
    print(f"  Total Commits: {metrics['total_commits']}")
    print(f"  Total Contributors: {metrics['total_contributors']}")
    print(f"  Total Pull Requests: {metrics['total_pull_requests']}")

    activity = metrics.get('activity_summary', {})
    print(f"\n📈 Activity:")
    print(f"  Busiest Day: {activity.get('busiest_day', 'N/A')} ({activity.get('busiest_day_commits', 0)} commits)")
    print(f"  Avg Commits/Day: {activity.get('avg_commits_per_day', 0):.2f}")

    busiest_contributor = activity.get('busiest_contributor')
    if busiest_contributor:
        print(f"  Top Contributor: {busiest_contributor['name']} ({busiest_contributor['commits']} commits)")

    # Code churn metrics
    code_churn = metrics.get('code_churn_metrics', {})
    if code_churn:
        print(f"\n💻 Code Churn:")
        print(f"  Total Lines Added: {code_churn.get('total_lines_added', 0):,}")
        print(f"  Total Lines Removed: {code_churn.get('total_lines_removed', 0):,}")
        print(f"  Total Lines Modified: {code_churn.get('total_lines_modified', 0):,}")
        print(f"  Net Lines Change: {code_churn.get('net_lines_change', 0):+,}")
        print(f"  Total Files Changed: {code_churn.get('total_files_changed', 0):,}")
        print(f"  Avg Lines/Commit: {code_churn.get('avg_lines_per_commit', 0):.1f}")
        print(f"  Avg Files/Commit: {code_churn.get('avg_files_per_commit', 0):.1f}")

        size_dist = code_churn.get('commit_size_distribution', {})
        print(f"  Commit Sizes: {size_dist.get('small', 0)} small, {size_dist.get('medium', 0)} medium, {size_dist.get('large', 0)} large")

    # PR code review metrics
    pr_review = metrics.get('pr_code_review_metrics', {})
    if pr_review and pr_review.get('total_pr_lines_modified', 0) > 0:
        print(f"\n🔍 Pull Request Analysis:")
        print(f"  Total PR Lines Modified: {pr_review.get('total_pr_lines_modified', 0):,}")
        print(f"  Avg PR Size: {pr_review.get('avg_pr_size_lines', 0):.1f} lines")
        print(f"  Avg Comments/PR: {pr_review.get('avg_comments_per_pr', 0):.1f}")
        print(f"  Avg Approvals/PR: {pr_review.get('avg_approvals_per_pr', 0):.1f}")
        print(f"  Review Engagement Rate: {pr_review.get('review_engagement_rate', 0):.1f}%")

        pr_size_dist = pr_review.get('pr_size_distribution', {})
        print(f"  PR Sizes: {pr_size_dist.get('small', 0)} small, {pr_size_dist.get('medium', 0)} medium, {pr_size_dist.get('large', 0)} large")

    # Top contributors
    top_contributors = analyzer.get_top_contributors(limit=5)
    if top_contributors:
        print(f"\n👥 Top 5 Contributors:")
        for i, contributor in enumerate(top_contributors, 1):
            additions = contributor.get('additions', 0)
            deletions = contributor.get('deletions', 0)
            files = contributor.get('files_changed', 0)
            print(f"  {i}. {contributor['name']} ({contributor['email']})")
            print(f"      {contributor['commits']} commits | +{additions:,}/-{deletions:,} lines | {files:,} files")

    # Generate HTML report if requested
    if args.report:
        print("\n" + "=" * 80)
        print("Generating HTML Report...")
        print("=" * 80)

        metadata = {
            'project': args.project,
            'repository': args.repository,
            'start_date': args.start_date or 'All time',
            'end_date': args.end_date or 'Present',
        }

        try:
            import os
            bitbucket_url = os.getenv('BITBUCKET_URL', '')

            reporter = BitbucketReportGenerator(
                metadata=metadata,
                metrics=metrics,
                bitbucket_url=bitbucket_url
            )

            report_file = reporter.generate_html(args.report_output)
            print(f"\n✅ Report generated successfully: {report_file}")
            print(f"   Open it in a browser to view the analysis")

        except Exception as e:
            print(f"\n❌ Error generating report: {e}")
            sys.exit(1)

    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


if __name__ == '__main__':
    main()
