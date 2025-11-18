"""
Xray for Jira Test Execution Fetcher Module.

This module handles fetching test execution data from Xray for Jira (on-prem)
using the Xray REST API.

Classes:
    XrayFetcher: Main class for fetching test execution data from Xray
"""

import os
from typing import Optional, List
from datetime import datetime

from dotenv import load_dotenv
from jira import JIRA


class XrayFetcher:
    """
    Xray API connector for fetching test execution data.

    This class handles authentication with Jira and fetches test execution
    data from Xray for Jira (on-prem version).

    Attributes:
        jira_url (str): Jira instance URL
        jira (JIRA): Authenticated Jira client instance

    Example:
        >>> fetcher = XrayFetcher()
        >>> executions = fetcher.fetch_test_executions(project='PROJ')
    """

    def __init__(self):
        """
        Initialize Xray connection from environment variables.

        Reads configuration from .env file and establishes connection using
        Jira credentials.

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

    def build_jql_for_test_executions(
        self,
        project: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        test_plan: Optional[str] = None
    ) -> str:
        """
        Build JQL query to fetch test executions.

        Args:
            project: Jira project key (e.g., 'PROJ')
            start_date: Start date for filtering (YYYY-MM-DD)
            end_date: End date for filtering (YYYY-MM-DD)
            test_plan: Test Plan key (e.g., 'PROJ-123')

        Returns:
            JQL query string for test executions

        Example:
            >>> fetcher = XrayFetcher()
            >>> jql = fetcher.build_jql_for_test_executions('PROJ')
            >>> print(jql)
            'project = "PROJ" AND issuetype = "Test Execution" ORDER BY created DESC'
        """
        jql_parts = [
            f'project = "{project}"',
            'issuetype = "Test Execution"'
        ]

        if start_date:
            jql_parts.append(f'created >= "{start_date}"')

        if end_date:
            jql_parts.append(f'created <= "{end_date}"')

        if test_plan:
            jql_parts.append(f'issue in testPlanTests("{test_plan}")')

        jql = " AND ".join(jql_parts)
        jql += " ORDER BY created DESC"

        return jql

    def fetch_test_executions(
        self,
        project: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        test_plan: Optional[str] = None,
        batch_size: int = 100
    ) -> list:
        """
        Fetch test executions from Xray.

        Retrieves all test execution issues with their test runs.

        Args:
            project: Jira project key
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            test_plan: Optional test plan key
            batch_size: Number of issues to fetch per request (default: 100)

        Returns:
            List of test execution dictionaries with test run data

        Example:
            >>> fetcher = XrayFetcher()
            >>> executions = fetcher.fetch_test_executions('PROJ', start_date='2024-01-01')
            >>> print(f"Fetched {len(executions)} test executions")
        """
        jql = self.build_jql_for_test_executions(project, start_date, end_date, test_plan)
        print(f"\nJQL Query: {jql}")

        executions = []
        start_at = 0

        while True:
            print(f"Fetching test executions {start_at} to {start_at + batch_size}...")

            batch = self.jira.search_issues(
                jql,
                startAt=start_at,
                maxResults=batch_size,
                expand='changelog',
                fields='*all'
            )

            if not batch:
                break

            # Convert issues to dictionaries and fetch test runs
            for issue in batch:
                execution_data = self._test_execution_to_dict(issue)

                # Fetch test runs for this execution
                test_runs = self._fetch_test_runs(issue.key)
                execution_data['test_runs'] = test_runs

                executions.append(execution_data)

            print(f"  Found {len(batch)} test executions (total: {len(executions)})")

            if len(batch) < batch_size:
                break

            start_at += batch_size

        return executions

    def _fetch_test_runs(self, execution_key: str) -> list:
        """
        Fetch test runs for a specific test execution using Xray API.

        Args:
            execution_key: Test execution issue key (e.g., 'PROJ-123')

        Returns:
            List of test run dictionaries

        Note:
            Uses Xray REST API endpoint: /rest/raven/1.0/api/testrun
        """
        try:
            # Xray API endpoint for test runs
            url = f"{self.jira_url}/rest/raven/1.0/api/testrun?testExecIssueKey={execution_key}"

            # Make request using JIRA client's session
            response = self.jira._session.get(url)
            response.raise_for_status()

            test_runs_data = response.json()

            test_runs = []
            for run in test_runs_data:
                test_runs.append({
                    'id': run.get('id'),
                    'test_key': run.get('testKey'),
                    'status': run.get('status', {}).get('name', 'Unknown'),
                    'started_on': run.get('startedOn'),
                    'finished_on': run.get('finishedOn'),
                    'executed_by': run.get('executedBy'),
                    'defects': run.get('defects', []),
                    'examples': run.get('examples', []),
                    'comment': run.get('comment', '')
                })

            return test_runs

        except Exception as e:
            print(f"  Warning: Could not fetch test runs for {execution_key}: {e}")
            return []

    def _test_execution_to_dict(self, issue) -> dict:
        """
        Convert Jira test execution issue to dictionary.

        Extracts all relevant fields from test execution issue.

        Args:
            issue: Jira issue object from the API

        Returns:
            Dictionary containing test execution data
        """
        fields = issue.raw['fields']

        return {
            'key': issue.key,
            'id': issue.id,
            'summary': fields.get('summary', ''),
            'status': fields.get('status', {}).get('name', ''),
            'created': fields.get('created', ''),
            'updated': fields.get('updated', ''),
            'assignee': fields.get('assignee', {}).get('displayName', '') if fields.get('assignee') else '',
            'reporter': fields.get('reporter', {}).get('displayName', '') if fields.get('reporter') else '',
            'labels': fields.get('labels', []),
            'test_plan': fields.get('customfield_10000', ''),  # Adjust based on your Xray config
            'test_environments': fields.get('customfield_10001', []),  # Adjust based on your Xray config
            'description': fields.get('description', ''),
        }

    def fetch_test_plans(
        self,
        project: str,
        batch_size: int = 100
    ) -> list:
        """
        Fetch all test plans for a project.

        Args:
            project: Jira project key
            batch_size: Number of issues to fetch per request (default: 100)

        Returns:
            List of test plan dictionaries

        Example:
            >>> fetcher = XrayFetcher()
            >>> plans = fetcher.fetch_test_plans('PROJ')
            >>> print(f"Found {len(plans)} test plans")
        """
        jql = f'project = "{project}" AND issuetype = "Test Plan" ORDER BY created DESC'
        print(f"\nJQL Query: {jql}")

        plans = []
        start_at = 0

        while True:
            batch = self.jira.search_issues(
                jql,
                startAt=start_at,
                maxResults=batch_size,
                fields='*all'
            )

            if not batch:
                break

            for issue in batch:
                fields = issue.raw['fields']
                plans.append({
                    'key': issue.key,
                    'id': issue.id,
                    'summary': fields.get('summary', ''),
                    'status': fields.get('status', {}).get('name', ''),
                    'created': fields.get('created', ''),
                    'labels': fields.get('labels', [])
                })

            print(f"  Found {len(batch)} test plans (total: {len(plans)})")

            if len(batch) < batch_size:
                break

            start_at += batch_size

        return plans
