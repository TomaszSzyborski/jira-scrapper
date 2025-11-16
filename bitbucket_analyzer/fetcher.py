"""
Bitbucket API Fetcher Module.

This module handles all interactions with the Bitbucket Server API (On-Premise),
including authentication, fetching commits, pull requests, and diff data.

Classes:
    BitbucketFetcher: Main class for fetching commit and PR data from Bitbucket
"""

import os
from typing import Optional, List, Dict
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv


class BitbucketFetcher:
    """
    Bitbucket Server API connector for fetching commit and PR data.

    This class handles authentication with Bitbucket Server (On-Premise),
    fetches commits, pull requests, and detailed diff information for
    productivity analysis.

    Attributes:
        bitbucket_url (str): Bitbucket Server instance URL
        auth: HTTPBasicAuth instance for API requests
        session: Requests session for persistent connections

    Example:
        >>> fetcher = BitbucketFetcher()
        >>> commits = fetcher.fetch_commits(
        ...     project='PROJ',
        ...     repository='repo-name',
        ...     authors=['user1', 'user2'],
        ...     start_date='2024-01-01'
        ... )
    """

    def __init__(self):
        """
        Initialize Bitbucket connection from environment variables.

        Reads configuration from .env file and establishes connection using
        basic authentication (username + password or API token).

        Raises:
            ValueError: If BITBUCKET_URL is not set or credentials are missing
        """
        load_dotenv()

        self.bitbucket_url = os.getenv("BITBUCKET_URL")
        if not self.bitbucket_url:
            raise ValueError("BITBUCKET_URL not found in environment variables")

        # Remove trailing slash if present
        self.bitbucket_url = self.bitbucket_url.rstrip('/')

        # Get credentials
        bitbucket_username = os.getenv("BITBUCKET_USERNAME")
        bitbucket_password = os.getenv("BITBUCKET_PASSWORD")

        if not bitbucket_username or not bitbucket_password:
            raise ValueError(
                "Missing Bitbucket credentials. Set both:\n"
                "  - BITBUCKET_USERNAME\n"
                "  - BITBUCKET_PASSWORD (or API token)"
            )

        # Setup authentication
        self.auth = HTTPBasicAuth(bitbucket_username, bitbucket_password)
        self.session = requests.Session()
        self.session.auth = self.auth

        print(f"Connecting to Bitbucket Server: {self.bitbucket_url}")

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make an API request to Bitbucket Server.

        Args:
            endpoint: API endpoint path (e.g., '/rest/api/1.0/projects')
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.HTTPError: If the request fails
        """
        url = f"{self.bitbucket_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _paginated_request(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Make paginated API requests to Bitbucket Server.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            List of all items from all pages

        Example:
            Results are automatically collected from all pages.
        """
        if params is None:
            params = {}

        items = []
        start = 0
        is_last_page = False

        while not is_last_page:
            params['start'] = start
            params['limit'] = 100  # Max items per page

            response = self._make_request(endpoint, params)

            values = response.get('values', [])
            items.extend(values)

            is_last_page = response.get('isLastPage', True)
            start = response.get('nextPageStart', 0)

        return items

    def fetch_commits(
        self,
        project: str,
        repository: str,
        authors: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        branch: str = 'master'
    ) -> List[Dict]:
        """
        Fetch commits from a Bitbucket repository.

        Args:
            project: Bitbucket project key
            repository: Repository slug/name
            authors: List of author usernames to filter by
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
            branch: Branch name (default: 'master')

        Returns:
            List of commit dictionaries with details

        Example:
            >>> fetcher = BitbucketFetcher()
            >>> commits = fetcher.fetch_commits(
            ...     project='PROJ',
            ...     repository='my-repo',
            ...     authors=['john.doe', 'jane.smith'],
            ...     start_date='2024-01-01'
            ... )
        """
        endpoint = f"/rest/api/1.0/projects/{project}/repos/{repository}/commits"
        params = {'until': branch}

        print(f"\nFetching commits from {project}/{repository} (branch: {branch})...")

        all_commits = self._paginated_request(endpoint, params)

        # Filter by authors and dates
        filtered_commits = []
        for commit in all_commits:
            # Filter by author
            if authors:
                commit_author = commit.get('author', {}).get('name', '')
                if commit_author not in authors:
                    continue

            # Filter by date
            commit_timestamp = commit.get('authorTimestamp', 0) / 1000  # Convert from milliseconds
            commit_date = datetime.fromtimestamp(commit_timestamp).strftime('%Y-%m-%d')

            if start_date and commit_date < start_date:
                continue
            if end_date and commit_date > end_date:
                continue

            filtered_commits.append(commit)

        print(f"  Found {len(filtered_commits)} commits (filtered from {len(all_commits)} total)")
        return filtered_commits

    def fetch_commit_diff(
        self,
        project: str,
        repository: str,
        commit_id: str
    ) -> Dict:
        """
        Fetch diff details for a specific commit.

        Args:
            project: Bitbucket project key
            repository: Repository slug/name
            commit_id: Commit hash/ID

        Returns:
            Dictionary containing diff statistics:
            - added: Number of lines added
            - deleted: Number of lines deleted
            - modified: Number of lines modified (changed)
            - files_changed: Number of files changed

        Note:
            Modified lines are counted separately from added/deleted.
            A line is considered "modified" if it was changed in place.
        """
        endpoint = f"/rest/api/1.0/projects/{project}/repos/{repository}/commits/{commit_id}/diff"

        try:
            diffs = self._paginated_request(endpoint)

            stats = {
                'added': 0,
                'deleted': 0,
                'modified': 0,
                'files_changed': 0
            }

            for diff in diffs:
                if 'hunks' not in diff:
                    continue

                stats['files_changed'] += 1

                for hunk in diff['hunks']:
                    for segment in hunk.get('segments', []):
                        segment_type = segment.get('type', '')
                        lines = segment.get('lines', [])

                        if segment_type == 'ADDED':
                            # Check if this is a modification (paired with deletion)
                            # For simplicity, we'll count pure additions here
                            stats['added'] += len(lines)
                        elif segment_type == 'REMOVED':
                            stats['deleted'] += len(lines)
                        elif segment_type == 'CONTEXT':
                            # Context lines are unchanged
                            pass

            # Calculate modified lines (simplified heuristic)
            # Modified = min(added, deleted) in close proximity
            stats['modified'] = min(stats['added'], stats['deleted'])
            stats['added'] -= stats['modified']
            stats['deleted'] -= stats['modified']

            return stats

        except Exception as e:
            print(f"  Warning: Could not fetch diff for {commit_id[:8]}: {e}")
            return {'added': 0, 'deleted': 0, 'modified': 0, 'files_changed': 0}

    def fetch_pull_requests(
        self,
        project: str,
        repository: str,
        authors: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        state: str = 'ALL'
    ) -> List[Dict]:
        """
        Fetch pull requests from a Bitbucket repository.

        Args:
            project: Bitbucket project key
            repository: Repository slug/name
            authors: List of author usernames to filter by
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
            state: PR state - 'OPEN', 'MERGED', 'DECLINED', or 'ALL' (default)

        Returns:
            List of pull request dictionaries

        Example:
            >>> fetcher = BitbucketFetcher()
            >>> prs = fetcher.fetch_pull_requests(
            ...     project='PROJ',
            ...     repository='my-repo',
            ...     authors=['john.doe'],
            ...     state='MERGED'
            ... )
        """
        endpoint = f"/rest/api/1.0/projects/{project}/repos/{repository}/pull-requests"
        params = {}

        if state != 'ALL':
            params['state'] = state

        print(f"\nFetching pull requests from {project}/{repository}...")

        all_prs = self._paginated_request(endpoint, params)

        # Filter by authors and dates
        filtered_prs = []
        for pr in all_prs:
            # Filter by author
            if authors:
                pr_author = pr.get('author', {}).get('user', {}).get('name', '')
                if pr_author not in authors:
                    continue

            # Filter by date (use creation date)
            pr_timestamp = pr.get('createdDate', 0) / 1000  # Convert from milliseconds
            pr_date = datetime.fromtimestamp(pr_timestamp).strftime('%Y-%m-%d')

            if start_date and pr_date < start_date:
                continue
            if end_date and pr_date > end_date:
                continue

            filtered_prs.append(pr)

        print(f"  Found {len(filtered_prs)} pull requests (filtered from {len(all_prs)} total)")
        return filtered_prs

    def get_user_aliases(self, aliases: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Create a mapping of usernames to group aliases.

        Args:
            aliases: Dictionary mapping group names to lists of usernames
                    Example: {'Team A': ['user1', 'user2'], 'Team B': ['user3']}

        Returns:
            Dictionary mapping username to group name
            Example: {'user1': 'Team A', 'user2': 'Team A', 'user3': 'Team B'}

        Note:
            This is used to group users by teams or aliases for reporting.
        """
        user_to_group = {}
        for group_name, usernames in aliases.items():
            for username in usernames:
                user_to_group[username] = group_name
        return user_to_group
