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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Fetch Jira issues and cache them to jira_cached.json',
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
