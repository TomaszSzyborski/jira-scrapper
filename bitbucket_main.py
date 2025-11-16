#!/usr/bin/env python3
"""
Bitbucket Commit Analyzer - Main CLI Entry Point.

This script fetches commit and pull request data from Bitbucket Server (On-Premise),
analyzes productivity metrics, and generates comprehensive HTML reports with rankings.

Usage:
    python bitbucket_main.py --project PROJ --repository my-repo \\
        --authors user1 user2 user3 \\
        --start-date 2024-01-01 --end-date 2024-12-31

Example with user aliases:
    python bitbucket_main.py --project PROJ --repository my-repo \\
        --authors john.doe jane.smith bob.wilson \\
        --aliases "Team A:john.doe,jane.smith" "Team B:bob.wilson" \\
        --start-date 2024-01-01 --end-date 2024-12-31
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

from bitbucket_analyzer import BitbucketFetcher, CommitAnalyzer, ReportGenerator


def parse_aliases(alias_args):
    """
    Parse alias arguments into a dictionary.

    Args:
        alias_args: List of strings in format "GroupName:user1,user2,user3"

    Returns:
        Dictionary mapping usernames to group names

    Example:
        >>> parse_aliases(["Team A:john,jane", "Team B:bob"])
        {'john': 'Team A', 'jane': 'Team A', 'bob': 'Team B'}
    """
    if not alias_args:
        return {}

    user_to_group = {}
    for alias in alias_args:
        try:
            group_name, users = alias.split(':', 1)
            usernames = [u.strip() for u in users.split(',')]
            for username in usernames:
                user_to_group[username] = group_name.strip()
        except ValueError:
            print(f"⚠️  Warning: Invalid alias format: {alias}")
            print("   Expected format: 'GroupName:user1,user2,user3'")

    return user_to_group


def main():
    """Main entry point for Bitbucket commit analyzer."""
    parser = argparse.ArgumentParser(
        description='Analyze Bitbucket commits and generate productivity reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python bitbucket_main.py --project PROJ --repository my-repo \\
      --authors john.doe jane.smith

  # With date range
  python bitbucket_main.py --project PROJ --repository my-repo \\
      --authors john.doe jane.smith \\
      --start-date 2024-01-01 --end-date 2024-12-31

  # With user aliases (team grouping)
  python bitbucket_main.py --project PROJ --repository my-repo \\
      --authors john.doe jane.smith bob.wilson \\
      --aliases "Team A:john.doe,jane.smith" "Team B:bob.wilson"

  # With detailed commit output
  python bitbucket_main.py --project PROJ --repository my-repo \\
      --authors john.doe \\
      --detailed-commits
        """
    )

    # Required arguments
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Bitbucket project key (e.g., "PROJ")'
    )

    parser.add_argument(
        '--repository', '-r',
        required=True,
        help='Repository name/slug (e.g., "my-repo")'
    )

    # Optional arguments
    parser.add_argument(
        '--authors', '-a',
        nargs='+',
        help='Usernames to analyze (e.g., john.doe jane.smith). If not specified, all authors are included.'
    )

    parser.add_argument(
        '--start-date',
        help='Start date for analysis (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        help='End date for analysis (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--branch',
        default='master',
        help='Branch name to analyze (default: master)'
    )

    parser.add_argument(
        '--aliases',
        nargs='*',
        help='User aliases/groups in format "GroupName:user1,user2" (can be specified multiple times)'
    )

    parser.add_argument(
        '--output', '-o',
        default='bitbucket_commit_report.html',
        help='Output HTML report filename (default: bitbucket_commit_report.html)'
    )

    parser.add_argument(
        '--cache-dir',
        default='data/bitbucket_cache',
        help='Directory for caching fetched data (default: data/bitbucket_cache)'
    )

    parser.add_argument(
        '--detailed-commits',
        action='store_true',
        help='Include detailed commit lists in the report'
    )

    parser.add_argument(
        '--pr-state',
        choices=['ALL', 'OPEN', 'MERGED', 'DECLINED'],
        default='ALL',
        help='Pull request state to fetch (default: ALL)'
    )

    args = parser.parse_args()

    try:
        print("=" * 80)
        print("Bitbucket Commit Analyzer")
        print("=" * 80)

        # Parse user aliases
        user_aliases = parse_aliases(args.aliases)
        if user_aliases:
            print(f"\n📋 User Aliases:")
            for user, group in user_aliases.items():
                print(f"   {user} → {group}")

        # Initialize fetcher
        print(f"\n🔌 Connecting to Bitbucket...")
        fetcher = BitbucketFetcher()

        # Create cache directory
        cache_dir = Path(args.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache file path
        cache_key = f"{args.project}_{args.repository}_{args.branch}_{args.start_date or 'all'}_{args.end_date or 'all'}"
        cache_file = cache_dir / f"{cache_key}.json"

        # Fetch commits (with caching)
        if cache_file.exists():
            print(f"\n💾 Loading commits from cache: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            commits = cache_data.get('commits', [])
            prs = cache_data.get('pull_requests', [])
        else:
            # Fetch commits
            commits = fetcher.fetch_commits(
                project=args.project,
                repository=args.repository,
                authors=args.authors,
                start_date=args.start_date,
                end_date=args.end_date,
                branch=args.branch
            )

            # Fetch pull requests
            prs = fetcher.fetch_pull_requests(
                project=args.project,
                repository=args.repository,
                authors=args.authors,
                start_date=args.start_date,
                end_date=args.end_date,
                state=args.pr_state
            )

            # Cache the results
            cache_data = {
                'metadata': {
                    'project': args.project,
                    'repository': args.repository,
                    'branch': args.branch,
                    'start_date': args.start_date,
                    'end_date': args.end_date,
                    'authors': args.authors,
                    'fetched_at': datetime.now().isoformat()
                },
                'commits': commits,
                'pull_requests': prs
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Cached data saved to: {cache_file}")

        # Fetch commit diffs (this can take a while)
        print(f"\n📊 Fetching diff statistics for {len(commits)} commits...")
        commit_diffs = {}
        for i, commit in enumerate(commits, 1):
            commit_id = commit.get('id', '')
            if commit_id:
                if i % 10 == 0:
                    print(f"   Progress: {i}/{len(commits)}")
                diff_stats = fetcher.fetch_commit_diff(
                    args.project,
                    args.repository,
                    commit_id
                )
                commit_diffs[commit_id] = diff_stats

        # Analyze commits
        print(f"\n🔍 Analyzing commit statistics...")
        analyzer = CommitAnalyzer(
            commits=commits,
            commit_diffs=commit_diffs,
            prs=prs,
            user_aliases=user_aliases
        )

        user_stats = analyzer.calculate_statistics()
        rankings = analyzer.get_rankings(user_stats)
        summary = analyzer.get_summary(user_stats)

        # Get detailed commits if requested
        detailed_commits = {}
        if args.detailed_commits:
            print(f"\n📝 Collecting detailed commit information...")
            for username in user_stats.keys():
                detailed_commits[username] = analyzer.get_detailed_commit_list(username)

        # Generate report
        print(f"\n📄 Generating HTML report...")
        metadata = {
            'project': args.project,
            'repository': args.repository,
            'branch': args.branch,
            'start_date': args.start_date or 'Beginning',
            'end_date': args.end_date or 'Now',
            'generated_at': datetime.now().isoformat()
        }

        generator = ReportGenerator(
            user_stats=user_stats,
            rankings=rankings,
            summary=summary,
            metadata=metadata,
            detailed_commits=detailed_commits
        )

        generator.generate_html(args.output)

        # Print summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"Total Users:        {summary['total_users']}")
        print(f"Total Commits:      {summary['total_commits']}")
        print(f"Total Changes:      {summary['total_changes']:,} lines")
        print(f"  - Added:          {summary['total_lines_added']:,}")
        print(f"  - Deleted:        {summary['total_lines_deleted']:,}")
        print(f"  - Modified:       {summary['total_lines_modified']:,}")
        print(f"Total PRs:          {summary['total_pull_requests']}")
        print(f"\nAverage per user:   {summary['average_commits_per_user']:.1f} commits")
        print(f"                    {summary['average_changes_per_user']:.1f} changes")
        print(f"                    {summary['average_prs_per_user']:.1f} PRs")

        print("\n" + "=" * 80)
        print(f"✅ Report generated successfully: {args.output}")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
