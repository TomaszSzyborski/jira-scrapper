"""
Pydantic Models for Jira Bug Flow Analysis.

This module provides comprehensive data models with validation for Jira issues,
changelog entries, and metrics. Enables full transparency of issue history
and state reconstruction on any given date.

Classes:
    ChangelogEntry: Single status transition in issue history
    JiraIssue: Complete Jira issue with full history
    IssueSnapshot: Issue state at a specific point in time
    StatusMetrics: Metrics for time spent in statuses
    FlowMetrics: Comprehensive flow analysis metrics
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator, computed_field


class StatusCategory(str, Enum):
    """Standard status categories for workflow analysis."""

    NEW = "NEW"
    IN_PROGRESS = "IN PROGRESS"
    CLOSED = "CLOSED"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class ChangelogEntry(BaseModel):
    """
    Single status transition in issue history.

    Represents a change event when an issue moved from one status to another,
    including timestamp and author information.

    Attributes:
        created: ISO timestamp when status change occurred
        author: User who made the change
        from_string: Previous status name
        to_string: New status name
        duration_hours: Time spent in previous status (calculated)

    Example:
        >>> entry = ChangelogEntry(
        ...     created="2024-01-15T10:00:00.000+0000",
        ...     author="John Doe",
        ...     from_string="To Do",
        ...     to_string="In Progress"
        ... )
        >>> entry.created_date
        '2024-01-15'
    """

    created: str = Field(..., description="ISO timestamp of status change")
    author: str = Field(..., description="User who made the change")
    from_string: str = Field(..., description="Previous status name")
    to_string: str = Field(..., description="New status name")
    duration_hours: Optional[float] = Field(None, description="Time in previous status (hours)")

    @computed_field
    @property
    def created_date(self) -> str:
        """Extract date portion from timestamp (YYYY-MM-DD)."""
        return self.created.split('T')[0]

    @computed_field
    @property
    def created_datetime(self) -> datetime:
        """Parse timestamp to datetime object."""
        return datetime.fromisoformat(self.created.replace('Z', '+00:00'))

    @computed_field
    @property
    def duration_days(self) -> Optional[float]:
        """Convert duration to days."""
        return round(self.duration_hours / 24, 2) if self.duration_hours else None

    model_config = {
        "json_schema_extra": {
            "example": {
                "created": "2024-01-15T10:00:00.000+0000",
                "author": "John Doe",
                "from_string": "To Do",
                "to_string": "In Progress",
                "duration_hours": 24.5
            }
        }
    }


class JiraIssue(BaseModel):
    """
    Complete Jira issue with full history and metadata.

    Comprehensive model of a Jira issue including all fields, changelog,
    and helper methods for historical state reconstruction and metrics.

    Attributes:
        key: Jira issue key (e.g., PROJ-123)
        id: Internal Jira issue ID
        summary: Issue title/summary
        status: Current status name
        issue_type: Type of issue (Bug, Task, etc.)
        priority: Priority level
        assignee: Currently assigned user
        reporter: User who created the issue
        created: ISO timestamp of creation
        updated: ISO timestamp of last update
        resolved: ISO timestamp of resolution (if closed)
        labels: List of labels
        components: List of component names
        description: Issue description text
        changelog: Complete history of status changes

    Example:
        >>> issue = JiraIssue(
        ...     key="PROJ-123",
        ...     id="10123",
        ...     summary="Login bug",
        ...     status="In Progress",
        ...     created="2024-01-15T09:00:00.000+0000",
        ...     changelog=[...]
        ... )
        >>> status = issue.get_status_on_date("2024-01-16")
        >>> metrics = issue.calculate_status_metrics()
    """

    key: str = Field(..., description="Jira issue key")
    id: str = Field(..., description="Internal issue ID")
    summary: str = Field(..., description="Issue title")
    status: str = Field(..., description="Current status")
    issue_type: str = Field(default="", description="Issue type (Bug, Task, etc.)")
    priority: str = Field(default="", description="Priority level")
    assignee: str = Field(default="", description="Assigned user")
    reporter: str = Field(default="", description="Reporter user")
    created: str = Field(..., description="ISO timestamp of creation")
    updated: str = Field(default="", description="ISO timestamp of last update")
    resolved: str = Field(default="", description="ISO timestamp of resolution")
    labels: List[str] = Field(default_factory=list, description="Issue labels")
    components: List[str] = Field(default_factory=list, description="Component names")
    description: str = Field(default="", description="Issue description")
    changelog: List[ChangelogEntry] = Field(default_factory=list, description="Status change history")

    @field_validator('changelog', mode='before')
    @classmethod
    def parse_changelog(cls, v):
        """Parse changelog from dict list to ChangelogEntry objects."""
        if not v:
            return []
        if isinstance(v, list) and len(v) > 0:
            if isinstance(v[0], dict):
                return [ChangelogEntry(**entry) for entry in v]
        return v

    @computed_field
    @property
    def created_date(self) -> str:
        """Extract creation date (YYYY-MM-DD)."""
        return self.created.split('T')[0] if self.created else ""

    @computed_field
    @property
    def resolved_date(self) -> Optional[str]:
        """Extract resolution date (YYYY-MM-DD)."""
        return self.resolved.split('T')[0] if self.resolved else None

    @computed_field
    @property
    def age_days(self) -> float:
        """Calculate issue age in days."""
        if not self.created:
            return 0.0
        created_dt = datetime.fromisoformat(self.created.replace('Z', '+00:00'))
        end_dt = datetime.now()
        if self.resolved:
            end_dt = datetime.fromisoformat(self.resolved.replace('Z', '+00:00'))
        return (end_dt - created_dt).total_seconds() / 86400

    @computed_field
    @property
    def total_transitions(self) -> int:
        """Count total number of status transitions."""
        return len(self.changelog)

    def get_status_on_date(self, target_date: str) -> Optional[str]:
        """
        Get the status of this issue on a specific date.

        Args:
            target_date: Date in YYYY-MM-DD format

        Returns:
            Status name on that date, or None if issue didn't exist yet

        Example:
            >>> issue.get_status_on_date("2024-01-20")
            'In Progress'
        """
        if not self.created or target_date < self.created_date:
            return None  # Issue didn't exist yet

        if not self.changelog:
            # No status changes, always in current status
            return self.status

        # Start with first status
        current_status = self.changelog[0].from_string

        # Apply each transition that occurred on or before target date
        for change in self.changelog:
            if change.created_date <= target_date:
                current_status = change.to_string
            else:
                break

        return current_status

    def get_status_category(self, status: str) -> StatusCategory:
        """
        Categorize a status into workflow category.

        Args:
            status: Status name to categorize

        Returns:
            StatusCategory enum value
        """
        if not status:
            return StatusCategory.UNKNOWN

        status_lower = status.lower()

        # NEW category
        if status_lower in ['new', 'to do']:
            return StatusCategory.NEW

        # IN PROGRESS category
        if status_lower in ['analysis', 'blocked', 'development', 'in development', 'in progress',
                           'review', 'development done', 'to test', 'in test']:
            return StatusCategory.IN_PROGRESS

        # CLOSED category
        if status_lower in ['rejected', 'closed', 'resolved', 'ready for uat']:
            return StatusCategory.CLOSED

        return StatusCategory.OTHER

    def is_open_on_date(self, target_date: str) -> bool:
        """
        Check if issue was open (NEW or IN PROGRESS) on a specific date.

        Args:
            target_date: Date in YYYY-MM-DD format

        Returns:
            True if issue was open on that date
        """
        status = self.get_status_on_date(target_date)
        if not status:
            return False

        category = self.get_status_category(status)
        return category in [StatusCategory.NEW, StatusCategory.IN_PROGRESS]

    def calculate_status_metrics(self) -> Dict[str, Any]:
        """
        Calculate time spent in each status.

        Returns:
            Dictionary mapping status names to time metrics

        Example:
            >>> metrics = issue.calculate_status_metrics()
            >>> print(metrics['In Progress'])
            {'hours': 48.5, 'days': 2.02, 'transitions': 2}
        """
        status_times: Dict[str, Dict[str, Any]] = {}

        for change in self.changelog:
            if change.duration_hours is not None:
                status = change.from_string
                if status not in status_times:
                    status_times[status] = {
                        'hours': 0.0,
                        'days': 0.0,
                        'transitions': 0
                    }

                status_times[status]['hours'] += change.duration_hours
                status_times[status]['days'] = round(status_times[status]['hours'] / 24, 2)
                status_times[status]['transitions'] += 1

        return status_times

    def detect_loops(self) -> List[Dict[str, Any]]:
        """
        Detect loops/rework in status transitions.

        Returns:
            List of detected loops with from/to status and occurrence count

        Example:
            >>> loops = issue.detect_loops()
            >>> for loop in loops:
            ...     print(f"{loop['from']} ← {loop['to']}: {loop['count']}")
        """
        loops = []
        seen_statuses = []

        for change in self.changelog:
            to_status = change.to_string

            # Check if we've seen this status before (loop detected)
            if to_status in seen_statuses:
                loops.append({
                    'from': change.from_string,
                    'to': to_status,
                    'date': change.created_date,
                    'author': change.author
                })

            seen_statuses.append(to_status)

        return loops

    def get_timeline(self) -> List[Dict[str, Any]]:
        """
        Get complete timeline of all status changes.

        Returns:
            List of timeline events with status, date, and duration

        Example:
            >>> timeline = issue.get_timeline()
            >>> for event in timeline:
            ...     print(f"{event['date']}: {event['status']} ({event['duration_days']} days)")
        """
        timeline = []

        # Add creation event
        timeline.append({
            'date': self.created_date,
            'event': 'created',
            'status': self.changelog[0].from_string if self.changelog else self.status,
            'author': self.reporter,
            'duration_days': None
        })

        # Add all transitions
        for change in self.changelog:
            timeline.append({
                'date': change.created_date,
                'event': 'transition',
                'status': change.to_string,
                'author': change.author,
                'duration_days': change.duration_days
            })

        return timeline

    model_config = {
        "json_schema_extra": {
            "example": {
                "key": "PROJ-123",
                "id": "10123",
                "summary": "Login button not working",
                "status": "In Progress",
                "issue_type": "Bug",
                "priority": "High",
                "created": "2024-01-15T09:00:00.000+0000",
                "changelog": [
                    {
                        "created": "2024-01-15T10:00:00.000+0000",
                        "author": "John Doe",
                        "from_string": "To Do",
                        "to_string": "In Progress"
                    }
                ]
            }
        }
    }


class IssueSnapshot(BaseModel):
    """
    Issue state at a specific point in time.

    Represents the complete state of an issue on a given date,
    including status, category, and whether it was open.

    Attributes:
        issue_key: Reference to parent issue
        date: Snapshot date (YYYY-MM-DD)
        status: Status on this date
        category: Status category on this date
        is_open: Whether issue was open (NEW/IN PROGRESS)
        summary: Issue summary (for reference)
        assignee: Assigned user on this date

    Example:
        >>> snapshot = IssueSnapshot.from_issue(issue, "2024-01-20")
        >>> print(f"{snapshot.issue_key}: {snapshot.status} ({snapshot.category})")
    """

    issue_key: str = Field(..., description="Jira issue key")
    date: str = Field(..., description="Snapshot date (YYYY-MM-DD)")
    status: Optional[str] = Field(None, description="Status on this date")
    category: StatusCategory = Field(StatusCategory.UNKNOWN, description="Status category")
    is_open: bool = Field(False, description="Whether issue was open")
    summary: str = Field(default="", description="Issue summary")
    assignee: str = Field(default="", description="Assigned user")

    @classmethod
    def from_issue(cls, issue: JiraIssue, date: str) -> 'IssueSnapshot':
        """
        Create snapshot from issue on specific date.

        Args:
            issue: JiraIssue to snapshot
            date: Target date in YYYY-MM-DD format

        Returns:
            IssueSnapshot for the specified date
        """
        status = issue.get_status_on_date(date)
        category = issue.get_status_category(status) if status else StatusCategory.UNKNOWN
        is_open = issue.is_open_on_date(date)

        return cls(
            issue_key=issue.key,
            date=date,
            status=status,
            category=category,
            is_open=is_open,
            summary=issue.summary,
            assignee=issue.assignee
        )


class StatusMetrics(BaseModel):
    """
    Time metrics for a specific status.

    Attributes:
        status: Status name
        avg_hours: Average time in hours
        avg_days: Average time in days
        median_hours: Median time in hours
        min_hours: Minimum time in hours
        max_hours: Maximum time in hours
        count: Number of transitions through this status
    """

    status: str
    avg_hours: float = Field(0.0, ge=0)
    avg_days: float = Field(0.0, ge=0)
    median_hours: float = Field(0.0, ge=0)
    min_hours: float = Field(0.0, ge=0)
    max_hours: float = Field(0.0, ge=0)
    count: int = Field(0, ge=0)


class FlowPattern(BaseModel):
    """
    Status transition flow pattern.

    Attributes:
        from_status: Source status
        to_status: Destination status
        count: Number of transitions
        is_loop: Whether this represents a backward flow
    """

    from_status: str
    to_status: str
    count: int = Field(ge=0)
    is_loop: bool = Field(default=False)


class DailyMetrics(BaseModel):
    """
    Metrics for a single day.

    Attributes:
        date: Date (YYYY-MM-DD)
        created_count: Bugs created this day
        closed_count: Bugs closed this day
        open_count: Bugs open this day
        open_issues: List of issues open on this day
    """

    date: str
    created_count: int = Field(0, ge=0)
    closed_count: int = Field(0, ge=0)
    open_count: int = Field(0, ge=0)
    open_issues: List[IssueSnapshot] = Field(default_factory=list)


class ProjectMetrics(BaseModel):
    """
    Comprehensive project-level metrics.

    Attributes:
        project: Project key
        total_issues: Total number of issues
        date_range_start: Analysis start date
        date_range_end: Analysis end date
        total_transitions: Total status transitions
        unique_statuses: Number of unique statuses
        total_loops: Total rework loops detected
        issues_with_loops: Count of issues with loops
    """

    project: str
    total_issues: int = Field(0, ge=0)
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    total_transitions: int = Field(0, ge=0)
    unique_statuses: int = Field(0, ge=0)
    total_loops: int = Field(0, ge=0)
    issues_with_loops: int = Field(0, ge=0)
