"""Jira data extraction module - Python 3.13 compatible version."""

import os
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

try:
    # Try using atlassian-python-api (Python 3.13 compatible)
    from atlassian import Jira
    USING_ATLASSIAN_API = True
except ImportError:
    # Fallback to jira library (Python 3.11 and below)
    from jira import JIRA
    from jira.exceptions import JIRAError
    USING_ATLASSIAN_API = False


class JiraScraper:
    """Handles Jira API authentication and data extraction for both Cloud and On-Premise."""

    def __init__(
        self,
        jira_url: Optional[str] = None,
        jira_email: Optional[str] = None,
        jira_api_token: Optional[str] = None,
        jira_username: Optional[str] = None,
        jira_password: Optional[str] = None,
        auth_method: str = "auto",
        max_retries: int = 3,
        backoff_factor: int = 2,
        requests_per_minute: int = 60,
    ):
        """
        Initialize Jira scraper with support for Cloud (API token) and On-Premise (username/password).

        Args:
            jira_url: Jira instance URL (defaults to JIRA_URL env var)
            jira_email: Jira user email for Cloud (defaults to JIRA_EMAIL env var)
            jira_api_token: Jira API token for Cloud (defaults to JIRA_API_TOKEN env var)
            jira_username: Jira username for On-Premise (defaults to JIRA_USERNAME env var)
            jira_password: Jira password for On-Premise (defaults to JIRA_PASSWORD env var)
            auth_method: Authentication method - "token" (Cloud), "password" (On-Prem),
                        or "auto" (auto-detect). Default is "auto".
            max_retries: Maximum number of retry attempts for failed requests
            backoff_factor: Multiplier for exponential backoff
            requests_per_minute: Rate limit for API requests
        """
        load_dotenv()

        self.jira_url = jira_url or os.getenv("JIRA_URL")

        # Cloud authentication (API token)
        self.jira_email = jira_email or os.getenv("JIRA_EMAIL")
        self.jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN")

        # On-Premise authentication (username/password)
        self.jira_username = jira_username or os.getenv("JIRA_USERNAME")
        self.jira_password = jira_password or os.getenv("JIRA_PASSWORD")

        self.auth_method = auth_method
        self.using_atlassian_api = USING_ATLASSIAN_API

        # Validate credentials based on auth method
        if not self.jira_url:
            raise ValueError("JIRA_URL is required. Set it in environment variables or pass as argument.")

        # Auto-detect authentication method
        if self.auth_method == "auto":
            if self.jira_api_token and self.jira_email:
                self.auth_method = "token"
                print("Auto-detected: Using API token authentication (Jira Cloud)")
            elif self.jira_username and self.jira_password:
                self.auth_method = "password"
                print("Auto-detected: Using username/password authentication (Jira On-Premise)")
            else:
                raise ValueError(
                    "Missing Jira credentials. Provide either:\n"
                    "  - API token auth (Cloud): JIRA_EMAIL and JIRA_API_TOKEN\n"
                    "  - Username/password auth (On-Prem): JIRA_USERNAME and JIRA_PASSWORD"
                )

        # Validate credentials for chosen method
        if self.auth_method == "token":
            if not all([self.jira_email, self.jira_api_token]):
                raise ValueError(
                    "API token authentication requires JIRA_EMAIL and JIRA_API_TOKEN"
                )
        elif self.auth_method == "password":
            if not all([self.jira_username, self.jira_password]):
                raise ValueError(
                    "Password authentication requires JIRA_USERNAME and JIRA_PASSWORD"
                )
        else:
            raise ValueError(
                f"Invalid auth_method: {self.auth_method}. Use 'token', 'password', or 'auto'."
            )

        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.requests_per_minute = requests_per_minute
        self.min_request_interval = 60.0 / requests_per_minute

        self._last_request_time = 0.0
        self._jira_client = None

        if USING_ATLASSIAN_API:
            print("Using atlassian-python-api (Python 3.13 compatible)")
        else:
            print("Using jira library (Python 3.11 and below)")

    @property
    def client(self):
        """Get or create Jira client instance with appropriate authentication."""
        if self._jira_client is None:
            if USING_ATLASSIAN_API:
                # Using atlassian-python-api (Python 3.13 compatible)
                if self.auth_method == "token":
                    # Cloud authentication
                    self._jira_client = Jira(
                        url=self.jira_url,
                        username=self.jira_email,
                        password=self.jira_api_token,
                        cloud=True
                    )
                    print(f"Connected to Jira Cloud: {self.jira_url}")
                else:
                    # On-Premise authentication
                    self._jira_client = Jira(
                        url=self.jira_url,
                        username=self.jira_username,
                        password=self.jira_password,
                        cloud=False
                    )
                    print(f"Connected to Jira On-Premise: {self.jira_url}")
            else:
                # Using jira library (fallback for Python 3.11 and below)
                if self.auth_method == "token":
                    self._jira_client = JIRA(
                        server=self.jira_url,
                        basic_auth=(self.jira_email, self.jira_api_token),
                    )
                    print(f"Connected to Jira Cloud: {self.jira_url}")
                else:
                    self._jira_client = JIRA(
                        server=self.jira_url,
                        basic_auth=(self.jira_username, self.jira_password),
                    )
                    print(f"Connected to Jira On-Premise: {self.jira_url}")
        return self._jira_client

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _retry_request(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with exponential backoff retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                # Check if it's a rate limit or server error
                error_str = str(e).lower()
                if "429" in error_str or "rate limit" in error_str or "5" in str(getattr(e, 'status_code', '')):
                    wait_time = self.backoff_factor ** attempt
                    print(f"Request failed (attempt {attempt + 1}/{self.max_retries}). "
                          f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

    def get_project_tickets(
        self,
        project_key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        batch_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all tickets for a project within a date range.

        Args:
            project_key: Jira project key (e.g., "PROJ")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            batch_size: Number of tickets to fetch per request

        Returns:
            List of ticket dictionaries with full details and changelog
        """
        jql = f"project = {project_key}"

        if start_date:
            jql += f" AND created >= '{start_date}'"
        if end_date:
            jql += f" AND created <= '{end_date}'"

        jql += " ORDER BY created ASC"

        tickets = []
        start_at = 0

        while True:
            try:
                if USING_ATLASSIAN_API:
                    # Using atlassian-python-api
                    results = self._retry_request(
                        self.client.jql,
                        jql,
                        start=start_at,
                        limit=batch_size,
                        fields="*all",
                        expand="changelog"
                    )
                    issues = results.get("issues", [])
                else:
                    # Using jira library
                    issues = self._retry_request(
                        self.client.search_issues,
                        jql,
                        startAt=start_at,
                        maxResults=batch_size,
                        expand="changelog",
                        fields="*all",
                    )

                if not issues:
                    break

                for issue in issues:
                    ticket_data = self._extract_ticket_data(issue)
                    tickets.append(ticket_data)

                print(f"Fetched {len(tickets)} tickets...")

                if len(issues) < batch_size:
                    break

                start_at += batch_size

            except Exception as e:
                print(f"Error fetching tickets: {e}")
                raise

        print(f"Total tickets fetched: {len(tickets)}")
        return tickets

    def _extract_ticket_data(self, issue) -> Dict[str, Any]:
        """
        Extract relevant data from a Jira issue.

        Args:
            issue: Jira issue object (dict for atlassian-python-api, object for jira library)

        Returns:
            Dictionary with ticket data including changelog and Xray fields
        """
        if USING_ATLASSIAN_API:
            # issue is a dictionary
            fields = issue.get("fields", {})
            ticket = {
                "key": issue.get("key"),
                "summary": fields.get("summary", ""),
                "description": fields.get("description", ""),
                "status": fields.get("status", {}).get("name", ""),
                "issue_type": fields.get("issuetype", {}).get("name", ""),
                "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
                "created": fields.get("created", ""),
                "updated": fields.get("updated", ""),
                "resolved": fields.get("resolutiondate"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
                "labels": fields.get("labels", []),
                "components": [c.get("name") for c in fields.get("components", [])],
                "changelog": self._extract_changelog_atlassian(issue),
            }

            # Story points
            if "customfield_10016" in fields:
                ticket["story_points"] = fields.get("customfield_10016")
        else:
            # Using jira library - issue is an object
            ticket = {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": getattr(issue.fields, "description", ""),
                "status": issue.fields.status.name,
                "issue_type": issue.fields.issuetype.name,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "resolved": getattr(issue.fields, "resolutiondate", None),
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
                "labels": issue.fields.labels,
                "components": [c.name for c in issue.fields.components],
                "changelog": self._extract_changelog_jira(issue),
            }

            # Story points
            if hasattr(issue.fields, "customfield_10016"):
                ticket["story_points"] = getattr(issue.fields, "customfield_10016", None)

        # Extract Xray-specific fields
        ticket["xray_data"] = self._extract_xray_fields(issue if USING_ATLASSIAN_API else issue, ticket)

        return ticket

    def _extract_xray_fields(self, issue, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract Xray-specific fields from a Jira issue (On-Premise version).

        Args:
            issue: Jira issue object or dict
            ticket: Already extracted ticket data

        Returns:
            Dictionary with Xray-specific data
        """
        xray_data = {
            "is_test_execution": False,
            "test_execution_status": None,
            "test_plan": None,
            "test_environments": [],
            "test_count": 0,
        }

        # Check if this is a Test Execution issue type
        issue_type = ticket.get("issue_type", "")
        if issue_type in ["Test Execution", "Test"]:
            xray_data["is_test_execution"] = True
            xray_data["test_execution_status"] = ticket.get("status")

            # For atlassian-python-api, check custom fields in the dict
            if USING_ATLASSIAN_API and isinstance(issue, dict):
                fields = issue.get("fields", {})
                for field_name, field_value in fields.items():
                    if field_name.startswith("customfield"):
                        # Check for Test Plan reference
                        if isinstance(field_value, dict) and "key" in field_value:
                            if field_value.get("fields", {}).get("issuetype", {}).get("name") == "Test Plan":
                                xray_data["test_plan"] = field_value.get("key")

                        # Check for Test Environments
                        if isinstance(field_value, list) and field_value:
                            if all(isinstance(v, str) for v in field_value):
                                if any(env_keyword in str(field_value).lower()
                                       for env_keyword in ['test', 'dev', 'prod', 'stage', 'qa']):
                                    xray_data["test_environments"] = field_value

        return xray_data

    def _extract_changelog_atlassian(self, issue: Dict) -> List[Dict[str, Any]]:
        """Extract changelog for atlassian-python-api."""
        changelog = []
        changelog_data = issue.get("changelog", {})

        for history in changelog_data.get("histories", []):
            for item in history.get("items", []):
                if item.get("field") == "status":
                    changelog.append({
                        "timestamp": history.get("created", ""),
                        "from_status": item.get("fromString", ""),
                        "to_status": item.get("toString", ""),
                        "author": history.get("author", {}).get("displayName", "Unknown"),
                    })

        return changelog

    def _extract_changelog_jira(self, issue) -> List[Dict[str, Any]]:
        """Extract changelog for jira library."""
        changelog = []

        if not hasattr(issue, "changelog"):
            return changelog

        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == "status":
                    changelog.append({
                        "timestamp": history.created,
                        "from_status": item.fromString,
                        "to_status": item.toString,
                        "author": history.author.displayName if history.author else "Unknown",
                    })

        return changelog

    def get_project_info(self, project_key: str) -> Dict[str, Any]:
        """
        Get basic project information.

        Args:
            project_key: Jira project key

        Returns:
            Dictionary with project metadata
        """
        try:
            if USING_ATLASSIAN_API:
                project = self._retry_request(self.client.project, project_key)
                return {
                    "key": project.get("key"),
                    "name": project.get("name"),
                    "description": project.get("description", ""),
                    "lead": project.get("lead", {}).get("displayName"),
                }
            else:
                project = self._retry_request(self.client.project, project_key)
                return {
                    "key": project.key,
                    "name": project.name,
                    "description": getattr(project, "description", ""),
                    "lead": project.lead.displayName if project.lead else None,
                }
        except Exception as e:
            print(f"Error fetching project info: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test the Jira connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if USING_ATLASSIAN_API:
                self.client.myself()
            else:
                self.client.myself()
            print("Successfully connected to Jira")
            return True
        except Exception as e:
            print(f"Failed to connect to Jira: {e}")
            return False
