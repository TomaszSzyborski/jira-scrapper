"""Jira data extraction module."""

import os
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from jira import JIRA
from jira.exceptions import JIRAError
from .jql_queries import JQLQueries, STANDARD_FIELDS


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
        cache_dir: str = ".jira_cache",
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
            cache_dir: Directory to store cached data (default: .jira_cache)
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
        self._jira_client: Optional[JIRA] = None

        # Cache configuration
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    @property
    def client(self) -> JIRA:
        """Get or create Jira client instance with appropriate authentication."""
        if self._jira_client is None:
            if self.auth_method == "token":
                # Cloud authentication with API token
                self._jira_client = JIRA(
                    server=self.jira_url,
                    basic_auth=(self.jira_email, self.jira_api_token),
                )
                print(f"Connected to Jira Cloud: {self.jira_url}")
            else:  # password authentication
                # On-Premise authentication with username/password
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
            JIRAError: If all retry attempts fail
        """
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                return func(*args, **kwargs)
            except JIRAError as e:
                if attempt == self.max_retries - 1:
                    raise

                # Check if it's a rate limit error (429) or server error (5xx)
                if hasattr(e, 'status_code') and e.status_code in [429, 500, 502, 503, 504]:
                    wait_time = self.backoff_factor ** attempt
                    print(f"Request failed (attempt {attempt + 1}/{self.max_retries}). "
                          f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

    def _generate_cache_key(
        self,
        project_key: str,
        query_type: str,
        label: Optional[str] = None,
    ) -> str:
        """
        Generate a unique cache key based on query parameters.

        Note: Date filtering is now done during analysis, not during fetch,
        so cache keys don't include dates.

        Args:
            project_key: Jira project key
            query_type: Type of query (e.g., 'tickets', 'bugs', 'test_executions')
            label: Optional label filter

        Returns:
            MD5 hash string to use as cache filename
        """
        params = {
            "project": project_key,
            "type": query_type,
            "label": label,
        }
        params_str = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.md5(params_str.encode())
        return hash_obj.hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the full path for a cache file."""
        return self.cache_dir / f"{cache_key}.json"

    def _save_to_cache(
        self,
        cache_key: str,
        data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save data to cache file.

        Args:
            cache_key: Cache key generated from query parameters
            data: Data to cache
            metadata: Optional metadata to store with the cache
        """
        cache_path = self._get_cache_path(cache_key)
        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "data": data,
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"Data cached to: {cache_path}")
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")

    def _load_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load data from cache file if it exists.

        Args:
            cache_key: Cache key generated from query parameters

        Returns:
            Cached data if available, None otherwise
        """
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            cached_at = datetime.fromisoformat(cache_data["cached_at"])
            data_count = len(cache_data["data"])

            print(f"Found cached data from {cached_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Cached records: {data_count}")

            return cache_data["data"]
        except Exception as e:
            print(f"Warning: Failed to load cache: {e}")
            return None

    def get_project_tickets(
        self,
        project_key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        label: Optional[str] = None,
        batch_size: int = 1000,
        force_fetch: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all tickets for a project.

        Note: Fetches ALL tickets regardless of date. Date filtering should be done
        during analysis phase for better caching efficiency.

        Args:
            project_key: Jira project key (e.g., "PROJ")
            start_date: [DEPRECATED] Not used - kept for backwards compatibility
            end_date: [DEPRECATED] Not used - kept for backwards compatibility
            label: Optional label to filter tickets
            batch_size: Number of tickets to fetch per request
            force_fetch: If True, ignore cache and fetch from API

        Returns:
            List of all ticket dictionaries with full details and changelog
        """
        # Check cache first unless force_fetch is enabled
        cache_key = self._generate_cache_key(project_key, "tickets", label)

        if not force_fetch:
            cached_data = self._load_from_cache(cache_key)
            if cached_data is not None:
                print("Using cached data. Use --force-fetch to refresh from API.")
                return cached_data

        print("Fetching data from Jira API...")
        # Use JQL query template from jql_queries.py - fetch ALL tickets
        if label:
            jql = JQLQueries.format_query(
                JQLQueries.PROJECT_TICKETS_WITH_LABEL,
                project=project_key,
                label=label
            )
        else:
            jql = JQLQueries.format_query(
                JQLQueries.PROJECT_TICKETS,
                project=project_key
            )

        print(f"Using JQL query: {jql}")

        tickets = []
        start_at = 0

        while True:
            try:
                results = self._retry_request(
                    self.client.search_issues,
                    jql,
                    startAt=start_at,
                    maxResults=batch_size,
                    expand="changelog",
                    fields="*all",
                )

                if not results:
                    break

                for issue in results:
                    ticket_data = self._extract_ticket_data(issue)
                    tickets.append(ticket_data)

                print(f"Fetched {len(tickets)} tickets...")

                if len(results) < batch_size:
                    break

                start_at += batch_size

            except JIRAError as e:
                print(f"Error fetching tickets: {e}")
                raise

        print(f"Total tickets fetched: {len(tickets)}")

        # Save to cache
        metadata = {
            "project_key": project_key,
            "start_date": start_date,
            "end_date": end_date,
            "label": label,
            "total_count": len(tickets),
        }
        self._save_to_cache(cache_key, tickets, metadata)

        return tickets

    def _extract_ticket_data(self, issue) -> Dict[str, Any]:
        """
        Extract relevant data from a Jira issue.

        Args:
            issue: Jira issue object

        Returns:
            Dictionary with ticket data including changelog and Xray fields
        """
        ticket = {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": getattr(issue.fields, "description", ""),
            "status": issue.fields.status.name,
            "status_category": issue.fields.status.statusCategory.name if hasattr(issue.fields.status, 'statusCategory') else "",
            "issue_type": issue.fields.issuetype.name,
            "priority": issue.fields.priority.name if issue.fields.priority else None,
            "created": issue.fields.created,
            "updated": issue.fields.updated,
            "resolved": getattr(issue.fields, "resolutiondate", None),
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
            "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
            "labels": issue.fields.labels,
            "components": [c.name for c in issue.fields.components],
            "changelog": self._extract_changelog(issue),
        }

        # Extract custom fields if available
        if hasattr(issue.fields, "customfield_10016"):  # Story points (common field)
            ticket["story_points"] = getattr(issue.fields, "customfield_10016", None)

        # Extract Xray-specific fields for test executions (On-Premise)
        ticket["xray_data"] = self._extract_xray_fields(issue)

        return ticket

    def _extract_xray_fields(self, issue) -> Dict[str, Any]:
        """
        Extract Xray-specific fields from a Jira issue (On-Premise version).

        Xray On-Premise uses different custom field names than Cloud.
        Common Xray custom fields for On-Premise:
        - Test Execution Status: varies by configuration
        - Test Plan: varies by configuration
        - Test Environments: varies by configuration

        Args:
            issue: Jira issue object

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
        issue_type = issue.fields.issuetype.name
        if issue_type in ["Test Execution", "Test"]:
            xray_data["is_test_execution"] = True

            # For Xray On-Premise, the test execution status is typically in the main status field
            # but we also check for Xray-specific custom fields
            xray_data["test_execution_status"] = issue.fields.status.name

            # Try to extract Test Plan (custom field varies by installation)
            # Common custom field IDs: customfield_10700, customfield_11000, etc.
            for field_name in dir(issue.fields):
                if "customfield" in field_name:
                    field_value = getattr(issue.fields, field_name, None)

                    # Check for Test Plan reference
                    if field_value and hasattr(field_value, 'key'):
                        # This might be a link to a Test Plan
                        if hasattr(field_value, 'fields') and hasattr(field_value.fields, 'issuetype'):
                            if field_value.fields.issuetype.name == "Test Plan":
                                xray_data["test_plan"] = field_value.key

                    # Check for Test Environments (usually an array)
                    if isinstance(field_value, list) and field_value:
                        # Could be environments
                        if all(isinstance(v, str) for v in field_value):
                            # Heuristic: if it looks like environment names
                            if any(env_keyword in str(field_value).lower()
                                   for env_keyword in ['test', 'dev', 'prod', 'stage', 'qa']):
                                xray_data["test_environments"] = field_value

        return xray_data

    def _extract_changelog(self, issue) -> List[Dict[str, Any]]:
        """
        Extract changelog (status transitions) from a Jira issue.

        Args:
            issue: Jira issue object

        Returns:
            List of changelog entries with timestamps and field changes
            Format includes: changed_at, from_status, to_status, from_status_category, to_status_category
        """
        from .status_definitions import StatusDefinitions

        changelog = []

        if not hasattr(issue, "changelog"):
            return changelog

        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == "status":
                    from_status = item.fromString
                    to_status = item.toString

                    # Categorize statuses using StatusDefinitions
                    from_category = StatusDefinitions.categorize_status(from_status) if from_status else ""
                    to_category = StatusDefinitions.categorize_status(to_status) if to_status else ""

                    changelog.append({
                        "changed_at": history.created,  # Charts expect "changed_at" not "timestamp"
                        "timestamp": history.created,  # Keep for backward compatibility
                        "from_status": from_status,
                        "to_status": to_status,
                        "from_status_category": from_category,
                        "to_status_category": to_category,
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
            project = self._retry_request(self.client.project, project_key)
            return {
                "key": project.key,
                "name": project.name,
                "description": getattr(project, "description", ""),
                "lead": project.lead.displayName if project.lead else None,
            }
        except JIRAError as e:
            print(f"Error fetching project info: {e}")
            raise

    def get_bugs(
        self,
        project_key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        label: Optional[str] = None,
        batch_size: int = 1000,
        force_fetch: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all bugs for a project by issue type (Bug or "Błąd w programie").

        Note: Fetches ALL bugs regardless of date. Date filtering should be done
        during analysis phase.

        Args:
            project_key: Jira project key (e.g., "PROJ")
            start_date: [DEPRECATED] Not used - kept for backwards compatibility
            end_date: [DEPRECATED] Not used - kept for backwards compatibility
            label: Optional label to filter bugs
            batch_size: Number of tickets to fetch per request
            force_fetch: If True, ignore cache and fetch from API

        Returns:
            List of all bug ticket dictionaries (type = Bug or "Błąd w programie")
        """
        # Check cache first unless force_fetch is enabled
        cache_key = self._generate_cache_key(project_key, "bugs", label)

        if not force_fetch:
            cached_data = self._load_from_cache(cache_key)
            if cached_data is not None:
                print("Using cached bugs data. Use --force-fetch to refresh from API.")
                return cached_data

        print("Fetching bugs from Jira API...")
        # Fetch ALL bugs by type (Bug or "Błąd w programie")
        if label:
            jql = JQLQueries.format_query(
                JQLQueries.BUGS_ALL_WITH_LABEL,
                project=project_key,
                label=label
            )
        else:
            jql = JQLQueries.format_query(
                JQLQueries.BUGS_ALL,
                project=project_key
            )

        print(f"Fetching bugs with JQL: {jql}")

        bugs = []
        start_at = 0

        while True:
            try:
                results = self._retry_request(
                    self.client.search_issues,
                    jql,
                    startAt=start_at,
                    maxResults=batch_size,
                    expand="changelog",
                    fields="*all",
                )

                if not results:
                    break

                for issue in results:
                    bug_data = self._extract_ticket_data(issue)
                    bugs.append(bug_data)

                print(f"Fetched {len(bugs)} bugs...")

                if len(results) < batch_size:
                    break

                start_at += batch_size

            except JIRAError as e:
                print(f"Error fetching bugs: {e}")
                raise

        print(f"Total bugs fetched: {len(bugs)}")

        # Save to cache
        metadata = {
            "project_key": project_key,
            "start_date": start_date,
            "end_date": end_date,
            "label": label,
            "total_count": len(bugs),
        }
        self._save_to_cache(cache_key, bugs, metadata)

        return bugs

    def get_test_executions(
        self,
        project_key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        label: Optional[str] = None,
        batch_size: int = 1000,
        force_fetch: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all test executions for a project.

        Note: Fetches ALL test executions regardless of date. Date filtering should
        be done during analysis phase.

        Args:
            project_key: Jira project key (e.g., "PROJ")
            start_date: [DEPRECATED] Not used - kept for backwards compatibility
            end_date: [DEPRECATED] Not used - kept for backwards compatibility
            label: Optional label to filter test executions
            batch_size: Number of tickets to fetch per request
            force_fetch: If True, ignore cache and fetch from API

        Returns:
            List of all test execution ticket dictionaries
        """
        # Check cache first unless force_fetch is enabled
        cache_key = self._generate_cache_key(project_key, "test_executions", label)

        if not force_fetch:
            cached_data = self._load_from_cache(cache_key)
            if cached_data is not None:
                print("Using cached test executions data. Use --force-fetch to refresh from API.")
                return cached_data

        print("Fetching test executions from Jira API...")
        # Fetch ALL test executions
        if label:
            jql = JQLQueries.format_query(
                JQLQueries.TEST_EXECUTIONS_WITH_LABEL,
                project=project_key,
                label=label
            )
        else:
            jql = JQLQueries.format_query(
                JQLQueries.TEST_EXECUTIONS,
                project=project_key
            )

        print(f"Fetching test executions with JQL: {jql}")

        test_executions = []
        start_at = 0

        while True:
            try:
                results = self._retry_request(
                    self.client.search_issues,
                    jql,
                    startAt=start_at,
                    maxResults=batch_size,
                    expand="changelog",
                    fields="*all",
                )

                if not results:
                    break

                for issue in results:
                    test_data = self._extract_ticket_data(issue)
                    test_executions.append(test_data)

                print(f"Fetched {len(test_executions)} test executions...")

                if len(results) < batch_size:
                    break

                start_at += batch_size

            except JIRAError as e:
                print(f"Error fetching test executions: {e}")
                raise

        print(f"Total test executions fetched: {len(test_executions)}")

        # Save to cache
        metadata = {
            "project_key": project_key,
            "start_date": start_date,
            "end_date": end_date,
            "label": label,
            "total_count": len(test_executions),
        }
        self._save_to_cache(cache_key, test_executions, metadata)

        return test_executions

    def test_connection(self) -> bool:
        """
        Test the Jira connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.client.myself()
            print("Successfully connected to Jira")
            return True
        except JIRAError as e:
            print(f"Failed to connect to Jira: {e}")
            return False
