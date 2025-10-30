"""Centralized JQL query templates for Jira API requests.

This module contains all JQL query strings used throughout the application,
making maintenance and development easier.
"""

from typing import Dict, Any


class JQLQueries:
    """Container for all JQL query templates."""

    # Project-based queries - fetch ALL tickets regardless of date
    PROJECT_TICKETS = 'project = "{project}" ORDER BY created ASC'

    PROJECT_TICKETS_WITH_LABEL = 'project = "{project}" AND labels = "{label}" ORDER BY created ASC'

    PROJECT_TICKETS_UPDATED = 'project = "{project}" AND updated >= "{start_date}" AND updated <= "{end_date}" ORDER BY updated ASC'

    PROJECT_TICKETS_UPDATED_WITH_LABEL = 'project = "{project}" AND labels = "{label}" AND updated >= "{start_date}" AND updated <= "{end_date}" ORDER BY updated ASC'
    
    # Status-based queries
    ISSUES_IN_PROGRESS_ON_DATE = 'project = "{project}" AND status was "In Progress" ON "{date}"'
    
    ISSUES_IN_STATUS_ON_DATE = 'project = "{project}" AND status was "{status}" ON "{date}"'
    
    ISSUES_OPEN_ON_DATE = 'project = "{project}" AND created <= "{date}" AND (resolved is EMPTY OR resolved > "{date}")'
    
    # Bug-specific queries - filter by type only (Bug or "Błąd w programie")
    BUGS_ALL = 'project = "{project}" AND (type = Bug OR type = "Błąd w programie") ORDER BY created ASC'

    BUGS_ALL_WITH_LABEL = 'project = "{project}" AND (type = Bug OR type = "Błąd w programie") AND labels = "{label}" ORDER BY created ASC'

    BUGS_RESOLVED = 'project = "{project}" AND (type = Bug OR type = "Błąd w programie") AND resolved >= "{start_date}" AND resolved <= "{end_date}"'

    BUGS_RESOLVED_WITH_LABEL = 'project = "{project}" AND (type = Bug OR type = "Błąd w programie") AND labels = "{label}" AND resolved >= "{start_date}" AND resolved <= "{end_date}"'

    BUGS_OPEN = 'project = "{project}" AND (type = Bug OR type = "Błąd w programie") AND resolution = Unresolved'

    BUGS_OPEN_WITH_LABEL = 'project = "{project}" AND (type = Bug OR type = "Błąd w programie") AND labels = "{label}" AND resolution = Unresolved'
    
    # Test-related queries - fetch ALL test executions
    TEST_EXECUTIONS = 'project = "{project}" AND type = "Test Execution" ORDER BY created ASC'

    TEST_EXECUTIONS_WITH_LABEL = 'project = "{project}" AND type = "Test Execution" AND labels = "{label}" ORDER BY created ASC'
    
    # Test cases (not test executions)
    TEST_CASES = 'project = "{project}" AND type = Test'
    
    TEST_CASES_WITH_LABEL = 'project = "{project}" AND type = Test AND labels = "{label}"'
    
    # Tests linked to test executions
    TESTS_IN_EXECUTION = 'issue in linkedIssues("{test_execution_key}")'
    
    # Advanced queries for test tracking
    TESTS_EXECUTED_BY_DATE = 'project = "{project}" AND type = Test AND updated <= "{date}"'
    
    # Sprint-based queries
    ISSUES_IN_SPRINT = 'project = "{project}" AND sprint = "{sprint_name}"'
    
    # Label-based queries  
    ISSUES_WITH_LABEL = 'project = "{project}" AND labels = "{label}"'
    
    # Date range queries
    ISSUES_CREATED_BETWEEN = 'project = "{project}" AND created >= "{start_date}" AND created <= "{end_date}"'
    
    ISSUES_RESOLVED_BETWEEN = 'project = "{project}" AND resolved >= "{start_date}" AND resolved <= "{end_date}"'
    
    # Historical status queries (for tracking)
    ISSUES_CHANGED_TO_STATUS = 'project = "{project}" AND status changed to "{status}" during ("{start_date}", "{end_date}")'
    
    ISSUES_CHANGED_FROM_STATUS = 'project = "{project}" AND status changed from "{status}" during ("{start_date}", "{end_date}")'

    @staticmethod
    def format_query(template: str, **kwargs: Any) -> str:
        """
        Format a JQL query template with provided parameters.
        
        Args:
            template: JQL query template string
            **kwargs: Parameters to substitute in template
            
        Returns:
            Formatted JQL query string
            
        Example:
            >>> JQLQueries.format_query(
            ...     JQLQueries.PROJECT_TICKETS,
            ...     project="PROJ",
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31"
            ... )
            'project = "PROJ" AND created >= "2024-01-01" AND created <= "2024-12-31" ORDER BY created ASC'
        """
        return template.format(**kwargs)

    @staticmethod
    def get_issues_in_progress_on_dates(project: str, start_date: str, end_date: str) -> Dict[str, str]:
        """
        Generate JQL queries for checking in-progress status for each date in range.
        
        This is useful for tracking how many issues were actively worked on each day.
        Note: This generates one query per day, so use with caution for large date ranges.
        
        Args:
            project: Project key
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping dates to JQL queries
        """
        from datetime import datetime, timedelta
        
        queries = {}
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            queries[date_str] = JQLQueries.format_query(
                JQLQueries.ISSUES_IN_PROGRESS_ON_DATE,
                project=project,
                date=date_str
            )
            current += timedelta(days=1)
        
        return queries


# Commonly used query combinations
COMMON_QUERIES = {
    "all_project_tickets": JQLQueries.PROJECT_TICKETS,
    "bugs_all": JQLQueries.BUGS_ALL,
    "test_executions": JQLQueries.TEST_EXECUTIONS,
    "open_issues": JQLQueries.ISSUES_OPEN_ON_DATE,
}


# Query field configurations (what fields to request from Jira API)
STANDARD_FIELDS = [
    "summary",
    "status",
    "created",
    "updated",
    "resolved",
    "resolutiondate",
    "assignee",
    "reporter",
    "priority",
    "issuetype",
    "labels",
    "project",
]

EXTENDED_FIELDS = STANDARD_FIELDS + [
    "description",
    "comment",
    "attachment",
    "worklog",
    "timetracking",
    "aggregatetimeoriginalestimate",
    "timespent",
]

XRAY_FIELDS = STANDARD_FIELDS + [
    "customfield_10000",  # Common Xray test execution status field
    "customfield_10001",  # Common Xray test plan field
    "customfield_10002",  # Common Xray test set field
]


def build_jql_for_date_range(
    project: str,
    start_date: str,
    end_date: str,
    issue_types: list = None,
    statuses: list = None,
    labels: list = None
) -> str:
    """
    Build a complex JQL query with multiple filters.
    
    Args:
        project: Project key
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        issue_types: Optional list of issue types to filter
        statuses: Optional list of statuses to filter
        labels: Optional list of labels to filter
        
    Returns:
        Formatted JQL query string
    """
    query_parts = [f'project = "{project}"']
    query_parts.append(f'created >= "{start_date}"')
    query_parts.append(f'created <= "{end_date}"')
    
    if issue_types:
        types_str = ", ".join(issue_types)
        query_parts.append(f'type in ({types_str})')
    
    if statuses:
        statuses_str = '", "'.join(statuses)
        query_parts.append(f'status in ("{statuses_str}")')
    
    if labels:
        labels_str = '", "'.join(labels)
        query_parts.append(f'labels in ("{labels_str}")')
    
    query_parts.append('ORDER BY created ASC')
    
    return ' AND '.join(query_parts)
