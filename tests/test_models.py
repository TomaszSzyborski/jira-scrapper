"""
Tests for Pydantic models.

This module tests the Jira data models including validation,
computed fields, and helper methods.
"""

from datetime import datetime

import pytest

from jira_analyzer.models import (
    ChangelogEntry,
    JiraIssue,
    IssueSnapshot,
    StatusCategory,
    StatusMetrics,
    FlowPattern,
    DailyMetrics,
    ProjectMetrics,
)


class TestChangelogEntry:
    """Test cases for ChangelogEntry model."""

    def test_create_changelog_entry(self):
        """Test creating a changelog entry."""
        entry = ChangelogEntry(
            created="2024-01-15T10:00:00.000+0000",
            author="John Doe",
            from_string="To Do",
            to_string="In Progress",
            duration_hours=24.5
        )

        assert entry.created == "2024-01-15T10:00:00.000+0000"
        assert entry.author == "John Doe"
        assert entry.from_string == "To Do"
        assert entry.to_string == "In Progress"
        assert entry.duration_hours == 24.5

    def test_created_date_computed_field(self):
        """Test that created_date extracts date correctly."""
        entry = ChangelogEntry(
            created="2024-01-15T10:00:00.000+0000",
            author="Test",
            from_string="A",
            to_string="B"
        )

        assert entry.created_date == "2024-01-15"

    def test_created_datetime_computed_field(self):
        """Test that created_datetime parses correctly."""
        entry = ChangelogEntry(
            created="2024-01-15T10:00:00.000+0000",
            author="Test",
            from_string="A",
            to_string="B"
        )

        assert isinstance(entry.created_datetime, datetime)
        assert entry.created_datetime.year == 2024
        assert entry.created_datetime.month == 1
        assert entry.created_datetime.day == 15

    def test_duration_days_computed_field(self):
        """Test duration conversion to days."""
        entry = ChangelogEntry(
            created="2024-01-15T10:00:00.000+0000",
            author="Test",
            from_string="A",
            to_string="B",
            duration_hours=48.0
        )

        assert entry.duration_days == 2.0

    def test_duration_days_none(self):
        """Test duration_days when duration_hours is None."""
        entry = ChangelogEntry(
            created="2024-01-15T10:00:00.000+0000",
            author="Test",
            from_string="A",
            to_string="B"
        )

        assert entry.duration_days is None


class TestJiraIssue:
    """Test cases for JiraIssue model."""

    def test_create_minimal_issue(self):
        """Test creating issue with minimal required fields."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test issue",
            status="Open",
            created="2024-01-15T09:00:00.000+0000"
        )

        assert issue.key == "PROJ-123"
        assert issue.summary == "Test issue"
        assert issue.status == "Open"

    def test_create_full_issue(self):
        """Test creating issue with all fields."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test issue",
            status="In Progress",
            issue_type="Bug",
            priority="High",
            assignee="John Doe",
            reporter="Jane Smith",
            created="2024-01-15T09:00:00.000+0000",
            updated="2024-01-16T10:00:00.000+0000",
            resolved="2024-01-20T15:00:00.000+0000",
            labels=["bug", "critical"],
            components=["Frontend"],
            description="Test description",
            changelog=[]
        )

        assert issue.key == "PROJ-123"
        assert issue.priority == "High"
        assert issue.labels == ["bug", "critical"]
        assert issue.components == ["Frontend"]

    def test_parse_changelog_from_dict(self):
        """Test that changelog is parsed from dict list."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Open",
            created="2024-01-15T09:00:00.000+0000",
            changelog=[
                {
                    "created": "2024-01-15T10:00:00.000+0000",
                    "author": "John",
                    "from_string": "To Do",
                    "to_string": "In Progress"
                }
            ]
        )

        assert len(issue.changelog) == 1
        assert isinstance(issue.changelog[0], ChangelogEntry)
        assert issue.changelog[0].from_string == "To Do"

    def test_created_date_computed_field(self):
        """Test created_date extraction."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Open",
            created="2024-01-15T09:00:00.000+0000"
        )

        assert issue.created_date == "2024-01-15"

    def test_resolved_date_computed_field(self):
        """Test resolved_date extraction."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Closed",
            created="2024-01-15T09:00:00.000+0000",
            resolved="2024-01-20T15:00:00.000+0000"
        )

        assert issue.resolved_date == "2024-01-20"

    def test_resolved_date_none(self):
        """Test resolved_date when not resolved."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Open",
            created="2024-01-15T09:00:00.000+0000"
        )

        assert issue.resolved_date is None

    def test_total_transitions(self):
        """Test total_transitions count."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Open",
            created="2024-01-15T09:00:00.000+0000",
            changelog=[
                {"created": "2024-01-15T10:00:00.000+0000", "author": "A", "from_string": "X", "to_string": "Y"},
                {"created": "2024-01-16T10:00:00.000+0000", "author": "B", "from_string": "Y", "to_string": "Z"},
            ]
        )

        assert issue.total_transitions == 2

    def test_get_status_on_date_before_creation(self):
        """Test getting status before issue was created."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Open",
            created="2024-01-15T09:00:00.000+0000"
        )

        status = issue.get_status_on_date("2024-01-10")
        assert status is None

    def test_get_status_on_date_no_changelog(self):
        """Test getting status when no changelog exists."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Open",
            created="2024-01-15T09:00:00.000+0000",
            changelog=[]
        )

        status = issue.get_status_on_date("2024-01-20")
        assert status == "Open"

    def test_get_status_on_date_with_changelog(self):
        """Test getting status with changelog."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Closed",
            created="2024-01-15T09:00:00.000+0000",
            changelog=[
                {"created": "2024-01-16T10:00:00.000+0000", "author": "A", "from_string": "To Do", "to_string": "In Progress"},
                {"created": "2024-01-18T10:00:00.000+0000", "author": "B", "from_string": "In Progress", "to_string": "Closed"},
            ]
        )

        # Before first transition
        assert issue.get_status_on_date("2024-01-15") == "To Do"
        # After first transition
        assert issue.get_status_on_date("2024-01-17") == "In Progress"
        # After second transition
        assert issue.get_status_on_date("2024-01-20") == "Closed"

    def test_get_status_category(self):
        """Test status categorization."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Open",
            created="2024-01-15T09:00:00.000+0000"
        )

        assert issue.get_status_category("New") == StatusCategory.NEW
        assert issue.get_status_category("In Progress") == StatusCategory.IN_PROGRESS
        assert issue.get_status_category("In Development") == StatusCategory.IN_PROGRESS
        assert issue.get_status_category("Closed") == StatusCategory.CLOSED
        assert issue.get_status_category("Unknown") == StatusCategory.OTHER
        assert issue.get_status_category("") == StatusCategory.UNKNOWN

    def test_is_open_on_date(self):
        """Test checking if issue was open on date."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Closed",
            created="2024-01-15T09:00:00.000+0000",
            changelog=[
                {"created": "2024-01-16T10:00:00.000+0000", "author": "A", "from_string": "To Do", "to_string": "In Progress"},
                {"created": "2024-01-20T10:00:00.000+0000", "author": "B", "from_string": "In Progress", "to_string": "Closed"},
            ]
        )

        # Before creation
        assert issue.is_open_on_date("2024-01-10") is False
        # When in To Do (NEW)
        assert issue.is_open_on_date("2024-01-15") is True
        # When in In Progress
        assert issue.is_open_on_date("2024-01-17") is True
        # When Closed
        assert issue.is_open_on_date("2024-01-21") is False

    def test_calculate_status_metrics(self):
        """Test calculating status metrics."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Closed",
            created="2024-01-15T09:00:00.000+0000",
            changelog=[
                {"created": "2024-01-16T10:00:00.000+0000", "author": "A", "from_string": "To Do", "to_string": "In Progress", "duration_hours": 25.0},
                {"created": "2024-01-20T10:00:00.000+0000", "author": "B", "from_string": "In Progress", "to_string": "Closed", "duration_hours": 96.0},
            ]
        )

        metrics = issue.calculate_status_metrics()

        assert "To Do" in metrics
        assert metrics["To Do"]["hours"] == 25.0
        assert metrics["To Do"]["days"] == pytest.approx(1.04, rel=0.01)
        assert metrics["In Progress"]["hours"] == 96.0
        assert metrics["In Progress"]["days"] == 4.0

    def test_detect_loops(self):
        """Test loop detection."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Closed",
            created="2024-01-15T09:00:00.000+0000",
            changelog=[
                {"created": "2024-01-16T10:00:00.000+0000", "author": "A", "from_string": "To Do", "to_string": "In Progress"},
                {"created": "2024-01-17T10:00:00.000+0000", "author": "A", "from_string": "In Progress", "to_string": "In Test"},
                {"created": "2024-01-18T10:00:00.000+0000", "author": "B", "from_string": "In Test", "to_string": "In Progress"},  # Loop!
                {"created": "2024-01-20T10:00:00.000+0000", "author": "A", "from_string": "In Progress", "to_string": "Closed"},
            ]
        )

        loops = issue.detect_loops()

        assert len(loops) == 1
        assert loops[0]['to'] == "In Progress"
        assert loops[0]['from'] == "In Test"

    def test_get_timeline(self):
        """Test getting complete timeline."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test",
            status="Closed",
            created="2024-01-15T09:00:00.000+0000",
            reporter="Reporter",
            changelog=[
                {"created": "2024-01-16T10:00:00.000+0000", "author": "A", "from_string": "To Do", "to_string": "In Progress", "duration_hours": 25.0},
            ]
        )

        timeline = issue.get_timeline()

        assert len(timeline) == 2  # Creation + 1 transition
        assert timeline[0]['event'] == 'created'
        assert timeline[0]['author'] == 'Reporter'
        assert timeline[1]['event'] == 'transition'
        assert timeline[1]['status'] == 'In Progress'


class TestIssueSnapshot:
    """Test cases for IssueSnapshot model."""

    def test_create_snapshot(self):
        """Test creating snapshot manually."""
        snapshot = IssueSnapshot(
            issue_key="PROJ-123",
            date="2024-01-20",
            status="In Progress",
            category=StatusCategory.IN_PROGRESS,
            is_open=True,
            summary="Test issue"
        )

        assert snapshot.issue_key == "PROJ-123"
        assert snapshot.status == "In Progress"
        assert snapshot.is_open is True

    def test_from_issue(self):
        """Test creating snapshot from issue."""
        issue = JiraIssue(
            key="PROJ-123",
            id="10123",
            summary="Test issue",
            status="Closed",
            created="2024-01-15T09:00:00.000+0000",
            assignee="John Doe",
            changelog=[
                {"created": "2024-01-16T10:00:00.000+0000", "author": "A", "from_string": "To Do", "to_string": "In Progress"},
                {"created": "2024-01-20T10:00:00.000+0000", "author": "B", "from_string": "In Progress", "to_string": "Closed"},
            ]
        )

        snapshot = IssueSnapshot.from_issue(issue, "2024-01-17")

        assert snapshot.issue_key == "PROJ-123"
        assert snapshot.date == "2024-01-17"
        assert snapshot.status == "In Progress"
        assert snapshot.category == StatusCategory.IN_PROGRESS
        assert snapshot.is_open is True
        assert snapshot.summary == "Test issue"
        assert snapshot.assignee == "John Doe"


class TestOtherModels:
    """Test cases for other models."""

    def test_status_metrics(self):
        """Test StatusMetrics model."""
        metrics = StatusMetrics(
            status="In Progress",
            avg_hours=48.5,
            avg_days=2.02,
            median_hours=45.0,
            min_hours=24.0,
            max_hours=72.0,
            count=5
        )

        assert metrics.status == "In Progress"
        assert metrics.avg_hours == 48.5
        assert metrics.count == 5

    def test_flow_pattern(self):
        """Test FlowPattern model."""
        pattern = FlowPattern(
            from_status="In Progress",
            to_status="In Test",
            count=10,
            is_loop=False
        )

        assert pattern.from_status == "In Progress"
        assert pattern.count == 10
        assert pattern.is_loop is False

    def test_daily_metrics(self):
        """Test DailyMetrics model."""
        metrics = DailyMetrics(
            date="2024-01-20",
            created_count=5,
            closed_count=3,
            open_count=12
        )

        assert metrics.date == "2024-01-20"
        assert metrics.created_count == 5
        assert metrics.open_count == 12

    def test_project_metrics(self):
        """Test ProjectMetrics model."""
        metrics = ProjectMetrics(
            project="PROJ",
            total_issues=100,
            date_range_start="2024-01-01",
            date_range_end="2024-01-31",
            total_transitions=250,
            unique_statuses=8,
            total_loops=15,
            issues_with_loops=12
        )

        assert metrics.project == "PROJ"
        assert metrics.total_issues == 100
        assert metrics.total_loops == 15
