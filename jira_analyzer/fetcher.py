"""
Jira API Fetcher Module.

This module handles all interactions with the Jira API, including authentication,
query building, and issue data retrieval with changelog information.

Classes:
    JiraFetcher: Main class for fetching bug data from Jira
"""

import os
from typing import Optional

from dotenv import load_dotenv
from jira import JIRA


class JiraFetcher:
    """
    Jira API connector for fetching bug data.

    This class handles authentication with Jira (both Cloud and On-Premise),
    builds JQL queries to fetch only bugs, and retrieves issue data including
    complete changelog information for flow analysis.

    Note: This fetcher retrieves ALL bugs for a project. Filtering by dates
    or labels is done in the analysis phase (FlowAnalyzer), not during fetch.

    Attributes:
        jira_url (str): Jira instance URL
        jira (JIRA): Authenticated Jira client instance

    Example:
        >>> fetcher = JiraFetcher()
        >>> issues = fetcher.fetch_issues(project='PROJ')
    """

    def __init__(self):
        """
        Initialize Jira connection from environment variables.

        Reads configuration from .env file and establishes connection using
        either Cloud authentication (email + API token) or On-Premise
        authentication (username + password).

        Raises:
            ValueError: If JIRA_URL is not set or credentials are missing
        """
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
        issue_types: Optional[list] = None,
        incremental: bool = False,
    ) -> str:
        """
        Build JQL query to fetch issues.

        Args:
            project: Jira project key (e.g., 'PROJ')
            start_date: Start date for filtering (YYYY-MM-DD) - used for incremental sync
            end_date: End date for filtering (YYYY-MM-DD)
            issue_types: List of issue types to fetch (e.g., ['Bug', 'Story', 'Task'])
                        If None, defaults to bugs only for backwards compatibility
            incremental: If True, uses date filters in JQL for incremental fetching

        Returns:
            JQL query string that fetches specified issue types

        Example:
            >>> fetcher = JiraFetcher()
            >>> jql = fetcher.build_jql('PROJ', issue_types=['Bug', 'Story'])
            >>> print(jql)
            'project = "PROJ" AND type in (Bug, Story) ORDER BY created ASC'

            >>> jql = fetcher.build_jql('PROJ', start_date='2024-01-01', incremental=True)
            >>> print(jql)
            'project = "PROJ" AND type in (Bug) AND (created >= "2024-01-01" OR updated >= "2024-01-01") ORDER BY created ASC'
        """
        # Default to bugs if no issue types specified
        if issue_types is None:
            issue_types = ['Bug', 'Błąd w programie']

        # Format issue types for JQL
        formatted_types = ', '.join([f'"{t}"' if ' ' in t else t for t in issue_types])

        jql_parts = [f'project = "{project}"', f'type in ({formatted_types})']

        # Add date filters for incremental sync
        if incremental and start_date:
            # Fetch issues created OR updated since last sync
            date_filter = f'(created >= "{start_date}" OR updated >= "{start_date}")'
            jql_parts.append(date_filter)

        if incremental and end_date:
            # Optional end date filter
            jql_parts.append(f'created <= "{end_date}"')

        jql = " AND ".join(jql_parts)
        jql += " ORDER BY created ASC"

        return jql

    def fetch_issues(
        self,
        project: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        batch_size: int = 100,
        issue_types: Optional[list] = None,
        incremental: bool = False,
    ) -> list:
        """
        Fetch issues from Jira using JQL.

        Retrieves all issues with full changelog information.
        Results are fetched in batches to handle large datasets efficiently.

        Note: Date and label filtering is done in Python analysis, not here.

        Args:
            project: Jira project key
            start_date: Optional start date (used in incremental mode for delta fetch)
            end_date: Optional end date (used in incremental mode for delta fetch)
            batch_size: Number of issues to fetch per request (default: 100)
            issue_types: List of issue types to fetch (e.g., ['Bug', 'Story', 'Task'])
                        If None, defaults to bugs only
            incremental: If True, fetches only issues created/updated since start_date

        Returns:
            List of issue dictionaries with changelog data

        Example:
            >>> fetcher = JiraFetcher()
            >>> issues = fetcher.fetch_issues('PROJ', issue_types=['Story'], batch_size=50)
            >>> print(f"Fetched {len(issues)} stories")

            >>> # Incremental fetch - only new/updated since 2024-01-01
            >>> issues = fetcher.fetch_issues('PROJ', start_date='2024-01-01', incremental=True)
        """
        jql = self.build_jql(project, start_date, end_date, issue_types, incremental)
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

    def fetch_current_snapshot(
        self,
        project: str,
        issue_types: Optional[list] = None,
        label: Optional[str] = None,
        batch_size: int = 100,
    ) -> dict:
        """
        Fetch current state snapshot of open issues (statusCategory != Done).

        This creates a snapshot of what's currently open/in-progress for TODAY.
        Useful for current workload visualization and status distribution charts.

        Args:
            project: Jira project key
            issue_types: List of issue types to fetch
            label: Optional label filter
            batch_size: Number of issues to fetch per request (default: 100)

        Returns:
            Dictionary with issues grouped by type:
            {
                'Bug': [...],
                'Story': [...],
                'Zadanie Dev': [...]
            }

        Example:
            >>> fetcher = JiraFetcher()
            >>> snapshot = fetcher.fetch_current_snapshot('PROJ', label='Sprint-5')
            >>> print(f"Open bugs: {len(snapshot.get('Bug', []))}")
        """
        # Default to common issue types if none specified
        if issue_types is None:
            issue_types = ['Bug', 'Błąd w programie', 'Story', 'Zadanie Dev']

        results = {}

        for issue_type in issue_types:
            # Build JQL for current open issues
            jql_parts = [
                f'project = "{project}"',
                f'issuetype = "{issue_type}"',
                'statusCategory != Done'
            ]

            if label:
                jql_parts.append(f'labels = "{label}"')

            jql = " AND ".join(jql_parts)
            jql += " ORDER BY status ASC, priority DESC"

            print(f"\n[Current Snapshot - {issue_type}] JQL: {jql}")

            issues = []
            start_at = 0

            while True:
                batch = self.jira.search_issues(
                    jql,
                    startAt=start_at,
                    maxResults=batch_size,
                    expand='changelog',
                    fields='*all'
                )

                if not batch:
                    break

                for issue in batch:
                    issues.append(self._issue_to_dict(issue))

                print(f"  Found {len(batch)} {issue_type} issues (total: {len(issues)})")

                if len(batch) < batch_size:
                    break

                start_at += batch_size

            if issues:
                results[issue_type] = issues

        return results

    def _issue_to_dict(self, issue) -> dict:
        """
        Convert Jira issue object to dictionary.

        Extracts all relevant fields including changelog with status transitions.

        Args:
            issue: Jira issue object from the API

        Returns:
            Dictionary containing issue data and changelog

        Note:
            Only status transitions are extracted from changelog for flow analysis.
        """
        fields = issue.raw['fields']

        # Extract changelog - only status transitions
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

        issue_type = fields.get('issuetype', {}).get('name', '')

        return {
            'key': issue.key,
            'id': issue.id,
            'summary': fields.get('summary', ''),
            'status': fields.get('status', {}).get('name', ''),
            'statusCategory': fields.get('status', {}).get('statusCategory', {}).get('name', ''),
            'issue_type': issue_type,  # Legacy field name
            'type': issue_type,  # Consistent field name for interactive filtering
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
