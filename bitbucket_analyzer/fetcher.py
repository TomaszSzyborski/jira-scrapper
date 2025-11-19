"""
Bitbucket Repository Data Fetcher Module.

This module handles fetching repository data from Bitbucket Server/Data Center
using the Bitbucket REST API.

Classes:
    BitbucketFetcher: Main class for fetching repository data from Bitbucket
"""

import os
from typing import Optional, List
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

from dotenv import load_dotenv


class BitbucketFetcher:
    """
    Bitbucket API connector for fetching repository data.

    This class handles authentication with Bitbucket and fetches commits,
    pull requests, and contributor statistics.

    Attributes:
        bitbucket_url (str): Bitbucket instance URL
        auth (HTTPBasicAuth): Authentication credentials
        session (requests.Session): Requests session for API calls

    Example:
        >>> fetcher = BitbucketFetcher()
        >>> commits = fetcher.fetch_commits(repository='myrepo')
    """

    def __init__(self):
        """
        Initialize Bitbucket connection from environment variables.

        Reads configuration from .env file and establishes connection.

        Raises:
            ValueError: If BITBUCKET_URL is not set or credentials are missing
        """
        load_dotenv()

        self.bitbucket_url = os.getenv("BITBUCKET_URL")
        if not self.bitbucket_url:
            raise ValueError("BITBUCKET_URL not found in environment variables")

        # Remove trailing slash
        self.bitbucket_url = self.bitbucket_url.rstrip('/')

        # Get credentials
        username = os.getenv("BITBUCKET_USERNAME")
        password = os.getenv("BITBUCKET_PASSWORD")
        token = os.getenv("BITBUCKET_TOKEN")

        if token:
            print(f"Connecting to Bitbucket with token: {self.bitbucket_url}")
            # For Bitbucket Server, token goes in password field
            self.auth = HTTPBasicAuth(username or 'x-token-auth', token)
        elif username and password:
            print(f"Connecting to Bitbucket with username/password: {self.bitbucket_url}")
            self.auth = HTTPBasicAuth(username, password)
        else:
            raise ValueError(
                "Missing credentials. Set either:\n"
                "  - BITBUCKET_USERNAME and BITBUCKET_TOKEN, or\n"
                "  - BITBUCKET_USERNAME and BITBUCKET_PASSWORD"
            )

        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def fetch_commits(
        self,
        project: str,
        repository: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_emails: Optional[List[str]] = None,
        user_names: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> list:
        """
        Fetch commits from a Bitbucket repository.

        Args:
            project: Bitbucket project key (e.g., 'PROJ')
            repository: Repository slug (e.g., 'my-repo')
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
            user_emails: List of user emails to filter by
            user_names: List of usernames to filter by
            batch_size: Number of commits per page (default: 100)

        Returns:
            List of commit dictionaries

        Example:
            >>> fetcher = BitbucketFetcher()
            >>> commits = fetcher.fetch_commits('PROJ', 'my-repo')
        """
        print(f"\nFetching commits from {project}/{repository}...")

        # Parse dates
        start_timestamp = None
        end_timestamp = None
        if start_date:
            start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        if end_date:
            end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)

        commits = []
        start = 0
        is_last_page = False

        while not is_last_page:
            # Bitbucket REST API endpoint for commits
            url = f"{self.bitbucket_url}/rest/api/1.0/projects/{project}/repos/{repository}/commits"
            params = {
                'limit': batch_size,
                'start': start
            }

            # Add date filtering via since/until
            if start_timestamp:
                params['since'] = start_timestamp
            if end_timestamp:
                params['until'] = end_timestamp

            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                batch = data.get('values', [])
                is_last_page = data.get('isLastPage', True)
                next_page_start = data.get('nextPageStart')

                for commit_data in batch:
                    commit = self._commit_to_dict(commit_data)

                    # Fetch diff/changeset data for this commit
                    commit_id = commit.get('id')
                    if commit_id:
                        diff_stats = self._fetch_commit_changes(project, repository, commit_id)
                        commit.update(diff_stats)

                    # Filter by user email or username
                    if user_emails or user_names:
                        author_email = commit.get('author_email', '').lower()
                        author_name = commit.get('author_name', '').lower()

                        email_match = not user_emails or any(
                            email.lower() in author_email for email in user_emails
                        )
                        name_match = not user_names or any(
                            name.lower() in author_name for name in user_names
                        )

                        if email_match or name_match:
                            commits.append(commit)
                    else:
                        commits.append(commit)

                print(f"  Fetched {len(batch)} commits (total: {len(commits)})")

                if not is_last_page and next_page_start is not None:
                    start = next_page_start
                else:
                    break

            except Exception as e:
                print(f"  Error fetching commits: {e}")
                break

        print(f"Total commits fetched: {len(commits)}")
        return commits

    def fetch_pull_requests(
        self,
        project: str,
        repository: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        state: str = 'ALL',
        batch_size: int = 100
    ) -> list:
        """
        Fetch pull requests from a Bitbucket repository.

        Args:
            project: Bitbucket project key
            repository: Repository slug
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
            state: PR state filter (ALL, OPEN, MERGED, DECLINED)
            batch_size: Number of PRs per page

        Returns:
            List of pull request dictionaries
        """
        print(f"\nFetching pull requests from {project}/{repository}...")

        pull_requests = []
        start = 0
        is_last_page = False

        # Parse dates
        start_ts = None
        end_ts = None
        if start_date:
            start_ts = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_ts = datetime.strptime(end_date, '%Y-%m-%d')

        while not is_last_page:
            url = f"{self.bitbucket_url}/rest/api/1.0/projects/{project}/repos/{repository}/pull-requests"
            params = {
                'limit': batch_size,
                'start': start,
                'state': state
            }

            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                batch = data.get('values', [])
                is_last_page = data.get('isLastPage', True)
                next_page_start = data.get('nextPageStart')

                for pr_data in batch:
                    pr = self._pr_to_dict(pr_data)

                    # Fetch additional PR data: activities, comments, and diff stats
                    pr_id = pr.get('id')
                    if pr_id:
                        pr_activities = self._fetch_pr_activities(project, repository, pr_id)
                        pr_diff_stats = self._fetch_pr_diff_stats(project, repository, pr_id)
                        pr['activities'] = pr_activities
                        pr.update(pr_diff_stats)

                    # Filter by date if specified
                    if start_ts or end_ts:
                        created_date = datetime.fromtimestamp(pr['created_timestamp'] / 1000)

                        if start_ts and created_date < start_ts:
                            continue
                        if end_ts and created_date > end_ts:
                            continue

                    pull_requests.append(pr)

                print(f"  Fetched {len(batch)} pull requests (total: {len(pull_requests)})")

                if not is_last_page and next_page_start is not None:
                    start = next_page_start
                else:
                    break

            except Exception as e:
                print(f"  Error fetching pull requests: {e}")
                break

        print(f"Total pull requests fetched: {len(pull_requests)}")
        return pull_requests

    def _fetch_commit_changes(self, project: str, repository: str, commit_id: str) -> dict:
        """
        Fetch changeset/diff statistics for a specific commit.

        Args:
            project: Bitbucket project key
            repository: Repository slug
            commit_id: Commit hash

        Returns:
            Dictionary with file changes statistics:
            - files_changed: Number of files changed
            - lines_added: Total lines added
            - lines_removed: Total lines removed
            - file_changes: List of changed files with details
        """
        try:
            # Bitbucket API endpoint for commit changes
            url = f"{self.bitbucket_url}/rest/api/1.0/projects/{project}/repos/{repository}/commits/{commit_id}/changes"
            params = {'limit': 1000}  # Get up to 1000 file changes

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            changes = data.get('values', [])
            files_changed = len(changes)

            # Collect file-level statistics
            file_changes = []
            for change in changes:
                file_path = change.get('path', {}).get('toString', '')
                change_type = change.get('type', 'UNKNOWN')  # MODIFY, ADD, DELETE, etc.

                file_changes.append({
                    'path': file_path,
                    'type': change_type
                })

            # Note: Bitbucket Server API doesn't provide line-level stats in /changes endpoint
            # To get line counts, we'd need to fetch the actual diff, which is expensive
            # For now, we'll fetch diff stats if available
            diff_stats = self._fetch_commit_diff_stats(project, repository, commit_id)

            return {
                'files_changed': files_changed,
                'lines_added': diff_stats.get('lines_added', 0),
                'lines_removed': diff_stats.get('lines_removed', 0),
                'file_changes': file_changes
            }

        except Exception as e:
            # Don't fail the entire fetch if one commit's changes fail
            return {
                'files_changed': 0,
                'lines_added': 0,
                'lines_removed': 0,
                'file_changes': []
            }

    def _fetch_commit_diff_stats(self, project: str, repository: str, commit_id: str) -> dict:
        """
        Fetch diff statistics by parsing the actual diff output.

        Args:
            project: Bitbucket project key
            repository: Repository slug
            commit_id: Commit hash

        Returns:
            Dictionary with lines_added and lines_removed counts
        """
        try:
            # Get the diff for this commit
            url = f"{self.bitbucket_url}/rest/api/1.0/projects/{project}/repos/{repository}/commits/{commit_id}/diff"
            params = {'contextLines': 0}  # Minimize context to reduce response size

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            lines_added = 0
            lines_removed = 0

            # Parse diffs from response
            diffs = data.get('diffs', [])
            for diff in diffs:
                hunks = diff.get('hunks', [])
                for hunk in hunks:
                    segments = hunk.get('segments', [])
                    for segment in segments:
                        segment_type = segment.get('type', '')
                        lines = segment.get('lines', [])

                        if segment_type == 'ADDED':
                            lines_added += len(lines)
                        elif segment_type == 'REMOVED':
                            lines_removed += len(lines)

            return {
                'lines_added': lines_added,
                'lines_removed': lines_removed
            }

        except Exception:
            # If diff fetching fails, return zeros
            return {
                'lines_added': 0,
                'lines_removed': 0
            }

    def _fetch_pr_activities(self, project: str, repository: str, pr_id: int) -> dict:
        """
        Fetch activities for a pull request (comments, reviews, approvals).

        Args:
            project: Bitbucket project key
            repository: Repository slug
            pr_id: Pull request ID

        Returns:
            Dictionary with PR activities statistics
        """
        try:
            url = f"{self.bitbucket_url}/rest/api/1.0/projects/{project}/repos/{repository}/pull-requests/{pr_id}/activities"
            params = {'limit': 1000}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            activities = data.get('values', [])

            comments_count = 0
            reviews_count = 0
            approvals_count = 0
            comments = []

            for activity in activities:
                action = activity.get('action', '')

                if action == 'COMMENTED':
                    comments_count += 1
                    comment = activity.get('comment', {})
                    comments.append({
                        'author': comment.get('author', {}).get('name', ''),
                        'text': comment.get('text', ''),
                        'created_date': comment.get('createdDate', 0)
                    })
                elif action == 'REVIEWED':
                    reviews_count += 1
                elif action == 'APPROVED':
                    approvals_count += 1

            return {
                'comments_count': comments_count,
                'reviews_count': reviews_count,
                'approvals_count': approvals_count,
                'total_activities': len(activities),
                'comments': comments[:10]  # Keep first 10 comments
            }

        except Exception:
            return {
                'comments_count': 0,
                'reviews_count': 0,
                'approvals_count': 0,
                'total_activities': 0,
                'comments': []
            }

    def _fetch_pr_diff_stats(self, project: str, repository: str, pr_id: int) -> dict:
        """
        Fetch diff statistics for a pull request.

        Args:
            project: Bitbucket project key
            repository: Repository slug
            pr_id: Pull request ID

        Returns:
            Dictionary with PR diff statistics
        """
        try:
            url = f"{self.bitbucket_url}/rest/api/1.0/projects/{project}/repos/{repository}/pull-requests/{pr_id}/diff"
            params = {'contextLines': 0}

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            lines_added = 0
            lines_removed = 0
            files_changed = 0

            diffs = data.get('diffs', [])
            files_changed = len(diffs)

            for diff in diffs:
                hunks = diff.get('hunks', [])
                for hunk in hunks:
                    segments = hunk.get('segments', [])
                    for segment in segments:
                        segment_type = segment.get('type', '')
                        lines = segment.get('lines', [])

                        if segment_type == 'ADDED':
                            lines_added += len(lines)
                        elif segment_type == 'REMOVED':
                            lines_removed += len(lines)

            return {
                'pr_files_changed': files_changed,
                'pr_lines_added': lines_added,
                'pr_lines_removed': lines_removed,
                'pr_lines_modified': lines_added + lines_removed
            }

        except Exception:
            return {
                'pr_files_changed': 0,
                'pr_lines_added': 0,
                'pr_lines_removed': 0,
                'pr_lines_modified': 0
            }

    def _commit_to_dict(self, commit_data: dict) -> dict:
        """
        Convert Bitbucket commit data to dictionary.

        Args:
            commit_data: Raw commit data from Bitbucket API

        Returns:
            Standardized commit dictionary
        """
        author = commit_data.get('author', {})
        committer = commit_data.get('committer', {})

        return {
            'id': commit_data.get('id', ''),
            'display_id': commit_data.get('displayId', ''),
            'message': commit_data.get('message', ''),
            'author_name': author.get('name', ''),
            'author_email': author.get('emailAddress', ''),
            'author_timestamp': commit_data.get('authorTimestamp', 0),
            'committer_name': committer.get('name', ''),
            'committer_email': committer.get('emailAddress', ''),
            'committer_timestamp': commit_data.get('committerTimestamp', 0),
            'parents': [p.get('id') for p in commit_data.get('parents', [])],
        }

    def _pr_to_dict(self, pr_data: dict) -> dict:
        """
        Convert Bitbucket pull request data to dictionary.

        Args:
            pr_data: Raw PR data from Bitbucket API

        Returns:
            Standardized PR dictionary
        """
        author = pr_data.get('author', {}).get('user', {})
        reviewers = pr_data.get('reviewers', [])

        return {
            'id': pr_data.get('id'),
            'title': pr_data.get('title', ''),
            'description': pr_data.get('description', ''),
            'state': pr_data.get('state', ''),
            'created_timestamp': pr_data.get('createdDate', 0),
            'updated_timestamp': pr_data.get('updatedDate', 0),
            'closed_timestamp': pr_data.get('closedDate'),
            'author_name': author.get('name', ''),
            'author_email': author.get('emailAddress', ''),
            'from_ref': pr_data.get('fromRef', {}).get('displayId', ''),
            'to_ref': pr_data.get('toRef', {}).get('displayId', ''),
            'reviewers': [
                {
                    'name': r.get('user', {}).get('name', ''),
                    'email': r.get('user', {}).get('emailAddress', ''),
                    'approved': r.get('approved', False),
                    'status': r.get('status', 'UNAPPROVED')
                }
                for r in reviewers
            ],
        }

    def fetch_repository_info(self, project: str, repository: str) -> dict:
        """
        Fetch repository information.

        Args:
            project: Bitbucket project key
            repository: Repository slug

        Returns:
            Repository information dictionary
        """
        url = f"{self.bitbucket_url}/rest/api/1.0/projects/{project}/repos/{repository}"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            return {
                'slug': data.get('slug', ''),
                'name': data.get('name', ''),
                'description': data.get('description', ''),
                'state': data.get('state', ''),
                'public': data.get('public', False),
                'project_key': data.get('project', {}).get('key', ''),
                'project_name': data.get('project', {}).get('name', ''),
            }

        except Exception as e:
            print(f"  Error fetching repository info: {e}")
            return {}
